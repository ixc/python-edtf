from django.db import models

from edtf import EDTF

DATE_ATTRS = (
    'date_earliest',
    'date_latest',
    'sort_date_earliest',
    'sort_date_latest',
)

class EDTFField(models.CharField):

    description = "An EDTF field for storing complex/fuzzy date specifications."

    def __init__(
        self,
        verbose_name=None, name=None,
        natural_text_field=None,
        date_earliest_field=None,
        date_latest_field=None,
        sort_date_earliest_field=None,
        sort_date_latest_field=None,
        **kwargs
    ):
        kwargs['max_length'] = 255
        self.natural_text_field, self.date_earliest_field, \
        self.date_latest_field, self.sort_date_earliest_field, \
        self.sort_date_latest_field = natural_text_field, date_earliest_field, \
          date_latest_field, sort_date_earliest_field, sort_date_latest_field
        super(EDTFField, self).__init__(verbose_name, name, **kwargs)


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
        return EDTF(edtf_text=value)

    def to_python(self, value):
        if isinstance(value, EDTF):
            return value

        if value is None:
            return value

        return EDTF(edtf_text=value)

    def get_prep_value(self, value):
        # convert python objects to query values
        value = super(EDTFField, self).get_prep_value(value)
        if isinstance(value, EDTF):
            return value.edtf_text
        return value

    def pre_save(self, instance, add):
        """
        Updates the edtf value from the value of the display_field.
        If there's a valid edtf, then set the date values.
        """
        if not self.natural_text_field or self.attname not in instance.__dict__:
            return

        natural_text = getattr(instance, self.natural_text_field)
        e = EDTF(natural_text=natural_text)
        setattr(instance, self.attname, e.edtf_text)

        # set related date fields on the instance
        for attr in DATE_ATTRS:
            field_attr = "%s_field" % attr
            g = getattr(self, field_attr, None)
            if g:
                setattr(instance, g, getattr(e, attr)())

        return e.edtf_text
