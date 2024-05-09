try:
    import cPickle as pickle
except:
    import pickle

from django.db import models
from django.core.exceptions import FieldDoesNotExist

from edtf import parse_edtf, EDTFObject
from edtf.natlang import text_to_edtf
from edtf.convert import struct_time_to_date, struct_time_to_jd

DATE_ATTRS = (
    'lower_strict',
    'upper_strict',
    'lower_fuzzy',
    'upper_fuzzy',
)


class EDTFField(models.CharField):

    def __init__(
        self,
        verbose_name=None, name=None,
        natural_text_field=None,
        direct_input_field=None,
        lower_strict_field=None,
        upper_strict_field=None,
        lower_fuzzy_field=None,
        upper_fuzzy_field=None,
        **kwargs
    ):
        kwargs['max_length'] = 2000
        self.natural_text_field, self.direct_input_field, \
        self.lower_strict_field, self.upper_strict_field, \
        self.lower_fuzzy_field, self.upper_fuzzy_field = \
        natural_text_field, direct_input_field, lower_strict_field, \
        upper_strict_field, lower_fuzzy_field, upper_fuzzy_field
        super(EDTFField, self).__init__(verbose_name, name, **kwargs)

    description = "A field for storing complex/fuzzy date specifications in EDTF format."

    def deconstruct(self):
        name, path, args, kwargs = super(EDTFField, self).deconstruct()
        if self.natural_text_field:
            kwargs['natural_text_field'] = self.natural_text_field

        for attr in DATE_ATTRS:
            field = "%s_field" % attr
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
            return pickle.loads(value)
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
        return super(EDTFField, self).get_db_prep_save(value, connection)

    def get_prep_value(self, value):
        # convert python objects to query values
        value = super(EDTFField, self).get_prep_value(value)
        if isinstance(value, EDTFObject):
            return pickle.dumps(value)
        return value

    def pre_save(self, instance, add):
        """
        Updates the EDTF value from either the natural_text_field, which is parsed
        with text_to_edtf() and is used for display, or falling back to the direct_input_field,
        which allows directly providing an EDTF string. If one of these provides a valid EDTF object,
        then set the date values accordingly.
        """
    
        # Get existing value to determine if update is needed
        existing_value = getattr(instance, self.attname, None)
        direct_input = getattr(instance, self.direct_input_field, None)
        natural_text = getattr(instance, self.natural_text_field, None)

        # if direct_input is provided and is different from the existing value, update the EDTF field
        if direct_input and (existing_value is None or str(existing_value) != direct_input):
            edtf = parse_edtf(direct_input, fail_silently=True) # ParseException if invalid; should this be raised?
            # TODO pyparsing.ParseExceptions are very noisy and dumps the whole grammar (see https://github.com/ixc/python-edtf/issues/46)

            # set the natural_text (display) field to the direct_input if it is not provided
            if natural_text is None:
                setattr(instance, self.natural_text_field, direct_input)

        elif natural_text:
            edtf_string = text_to_edtf(natural_text)
            if edtf_string and (existing_value is None or str(existing_value) != edtf_string):
                edtf = parse_edtf(edtf_string, fail_silently=True) # potetial ParseException if invalid; should this be raised?
            else:
                edtf = existing_value
        else:
            if not existing_value:
                # No inputs provided and no existing value; TODO log this?
                return
            # TODO: if both direct_input and natural_text are cleared, should we throw an error?
            edtf = existing_value

        # Update the actual EDTF field in the model if there is a change
        if edtf != existing_value:
            setattr(instance, self.attname, edtf)

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
                            u"EDTFField does not support %s as a derived data"
                            u" field, only FloatField or DateField"
                            % type(target_field))
                    setattr(instance, g, value)
                else:
                    setattr(instance, g, None)
        return edtf
