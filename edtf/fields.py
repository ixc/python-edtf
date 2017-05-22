from django.db import models

from edtf import parse_edtf, EDTFObject
from natlang import text_to_edtf

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
        lower_strict_field=None,
        upper_strict_field=None,
        lower_fuzzy_field=None,
        upper_fuzzy_field=None,
        **kwargs
    ):
        kwargs['max_length'] = 255
        self.natural_text_field, self.lower_strict_field, \
        self.upper_strict_field, self.lower_fuzzy_field, \
        self.upper_fuzzy_field = natural_text_field, lower_strict_field, \
            upper_strict_field, lower_fuzzy_field, upper_fuzzy_field
        super(EDTFField, self).__init__(verbose_name, name, **kwargs)

    description = "An field for storing complex/fuzzy date specifications in EDTF format."


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

    def from_db_value(self, value, expression, connection, context):
        # Converting values to Python objects
        return parse_edtf(value, fail_silently=True)

    def to_python(self, value):
        if isinstance(value, EDTFObject):
            return value

        if value is None:
            return value

        return parse_edtf(value, fail_silently=True)

    def get_prep_value(self, value):
        # convert python objects to query values
        value = super(EDTFField, self).get_prep_value(value)
        if isinstance(value, EDTFObject):
            return unicode(value)
        return value

    def pre_save(self, instance, add):
        """
        Updates the edtf value from the value of the display_field.
        If there's a valid edtf, then set the date values.
        """
        if not self.natural_text_field or self.attname not in instance.__dict__:
            return

        natural_text = getattr(instance, self.natural_text_field)
        if natural_text:
            n = text_to_edtf(natural_text)
            setattr(instance, self.attname, n)

        e = parse_edtf(getattr(instance, self.attname), fail_silently=True)
        if e:

            # set related date fields on the instance
            for attr in DATE_ATTRS:
                field_attr = "%s_field" % attr
                g = getattr(self, field_attr, None)
                if g:
                    setattr(instance, g, getattr(e, attr)())

            return unicode(e)
