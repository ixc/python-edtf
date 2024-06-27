import pickle

from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import signals
from django.db.models.query_utils import DeferredAttribute
from pyparsing import ParseException

from edtf import EDTFObject, parse_edtf
from edtf.convert import struct_time_to_date, struct_time_to_jd
from edtf.natlang import text_to_edtf
from edtf.parser.edtf_exceptions import EDTFParseException

DATE_ATTRS = (
    "lower_strict",
    "upper_strict",
    "lower_fuzzy",
    "upper_fuzzy",
)


class EDTFFieldDescriptor(DeferredAttribute):
    """
    Descriptor for the EDTFField's attribute on the model instance.
    This updates the dependent fields each time this value is set.
    """

    def __set__(self, instance, value):
        # First set the value we are given
        instance.__dict__[self.field.attname] = value
        # `update_values` may provide us with a new value to set
        edtf = self.field.update_values(instance, value)
        if edtf != value:
            instance.__dict__[self.field.attname] = edtf


class EDTFField(models.CharField):
    def __init__(
        self,
        verbose_name=None,
        name=None,
        natural_text_field=None,
        direct_input_field=None,
        lower_strict_field=None,
        upper_strict_field=None,
        lower_fuzzy_field=None,
        upper_fuzzy_field=None,
        **kwargs,
    ):
        kwargs["max_length"] = 2000
        self.natural_text_field = natural_text_field
        self.direct_input_field = direct_input_field
        self.lower_strict_field = lower_strict_field
        self.upper_strict_field = upper_strict_field
        self.lower_fuzzy_field = lower_fuzzy_field
        self.upper_fuzzy_field = upper_fuzzy_field
        super().__init__(verbose_name, name, **kwargs)

    description = (
        "A field for storing complex/fuzzy date specifications in EDTF format."
    )
    descriptor_class = EDTFFieldDescriptor

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.natural_text_field:
            kwargs["natural_text_field"] = self.natural_text_field
        if self.direct_input_field:
            kwargs["direct_input_field"] = self.direct_input_field

        for attr in DATE_ATTRS:
            field = f"{attr}_field"
            f = getattr(self, field, None)
            if f:
                kwargs[field] = f

        del kwargs["max_length"]
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        # Converting values from the database to Python objects
        if value is None:
            return value

        try:
            # Try to unpickle if the value was pickled
            return pickle.loads(value)  # noqa S301
        except (pickle.PickleError, TypeError):
            # If it fails because it's not pickled data, try parsing as EDTF
            return parse_edtf(value, fail_silently=True)

    def to_python(self, value):
        if isinstance(value, EDTFObject):
            return value

        if value is None:
            return value

        return parse_edtf(value, fail_silently=True)

    def get_db_prep_save(self, value, connection):
        if value:
            return pickle.dumps(value)
        return super().get_db_prep_save(value, connection)

    def get_prep_value(self, value):
        # convert python objects to query values
        value = super().get_prep_value(value)
        if isinstance(value, EDTFObject):
            return pickle.dumps(value)
        return value

    def update_values(self, instance, *args, **kwargs):
        """
        Updates the EDTF value from either the natural_text_field, which is parsed
        with text_to_edtf() and is used for display, or falling back to the direct_input_field,
        which allows directly providing an EDTF string. If one of these provides a valid EDTF object,
        then set the date values accordingly.
        """

        # Get existing value to determine if update is needed
        existing_value = getattr(instance, self.attname, None)
        direct_input = getattr(instance, self.direct_input_field, "")
        natural_text = getattr(instance, self.natural_text_field, "")

        # if direct_input is provided and is different from the existing value, update the EDTF field
        if direct_input and (
            existing_value is None or str(existing_value) != direct_input
        ):
            try:
                edtf = parse_edtf(
                    direct_input, fail_silently=True
                )  # ParseException if invalid; should this be raised?
            except ParseException as err:
                raise EDTFParseException(direct_input, err) from None

            # set the natural_text (display) field to the direct_input if it is not provided
            if not natural_text:
                setattr(instance, self.natural_text_field, direct_input)

        elif natural_text:
            edtf_string = text_to_edtf(natural_text)
            if edtf_string and (
                existing_value is None or str(existing_value) != edtf_string
            ):
                edtf = parse_edtf(
                    edtf_string, fail_silently=True
                )  # potential ParseException if invalid; should this be raised?
            else:
                edtf = existing_value
        else:
            if not existing_value:
                # No inputs provided and no existing value; TODO log this?
                return
            # TODO: if both direct_input and natural_text are cleared, should we throw an error?
            edtf = existing_value

        # Process and update related date fields based on the EDTF object
        for attr in DATE_ATTRS:
            field_attr = f"{attr}_field"
            g = getattr(self, field_attr, None)
            if g:
                if edtf:
                    try:
                        target_field = instance._meta.get_field(g)
                    except FieldDoesNotExist:
                        continue
                    value = getattr(edtf, attr)()  # struct_time
                    if isinstance(target_field, models.FloatField):
                        value = struct_time_to_jd(value)
                    elif isinstance(target_field, models.DateField):
                        value = struct_time_to_date(value)
                    else:
                        raise NotImplementedError(
                            f"EDTFField does not support {type(target_field)} as a derived data"
                            " field, only FloatField or DateField"
                        )
                    setattr(instance, g, value)
                else:
                    setattr(instance, g, None)
        return edtf

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Attach update_values so that dependent fields declared
        # after their corresponding edtf field don't stay cleared by
        # Model.__init__, see Django bug #11196.
        # Only run post-initialization values update on non-abstract models
        if not cls._meta.abstract:
            signals.post_init.connect(self.update_values, sender=cls)

    def check(self, **kwargs):
        errors = super().check(**kwargs)

        for field_alias in [
            "direct_input_field",
            "lower_fuzzy_field",
            "lower_strict_field",
            "natural_text_field",
            "upper_fuzzy_field",
            "upper_strict_field",
        ]:
            errors.extend(self._check_field(field_alias))

        return errors

    def _check_field(self, field_alias):
        field_name = getattr(self, field_alias, None)

        # Check if the alias value has been provided in the field definition
        if not field_name:
            return [
                checks.Error(
                    f"You must specify a '{field_alias}' for EDTFField",
                    hint=None,
                    obj=self,
                    id="python-edtf.EDTF01",
                )
            ]

        # Check if the field that is referenced actually exists
        try:
            self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return [
                checks.Error(
                    f"'{self.name}' refers to a non-existent '{field_alias}' field: '{field_name}'",
                    hint=None,
                    obj=self,
                    id="python-edtf.EDTF02",
                )
            ]
        return []
