from django.db import models
from edtf.fields import EDTFField


class TestEvent(models.Model):
    date_display = models.CharField(
        "Date of creation (display)",
        blank=True,
        null=True,
        max_length=255,
        help_text="Enter the date in natural language format (e.g., 'Approximately June 2004')."
    )

    date_edtf_direct = models.CharField(
        "Date of creation (EDTF format)",
        max_length=255,
        blank=True,
        null=True,
        help_text="Enter the date in EDTF format (e.g., '2004-06~')."
    )

    # EDTF field that parses the input from either natural language or direct EDTF string
    # natural_text_field is the field that stores the natural language input and is used for display
    # direct_input_field stores an EDTF string
    # TODO is there a need for both a natural text input and a label?
    # TODO could consolidate the direct_input_field and natural_text_field into a single field, but would need
    # a flag to indicate whether the input is natural language or EDTF as the natural language parser sometimes
    # misparses an EDTF string as a natural language string (e.g. `2020-03-15/2020-04-15` -> `2020-03-15`)
    date_edtf = EDTFField(
        "Date of creation (EDTF)",
        natural_text_field='date_display',
        direct_input_field='date_edtf_direct',
        lower_fuzzy_field='date_earliest',
        upper_fuzzy_field='date_latest',
        lower_strict_field='date_sort_ascending',
        upper_strict_field='date_sort_descending',
        blank=True,
        null=True,
    )
    # Computed fields for filtering
    date_earliest = models.FloatField(blank=True, null=True)
    date_latest = models.FloatField(blank=True, null=True)
    # Computed fields for sorting
    date_sort_ascending = models.FloatField(blank=True, null=True)
    date_sort_descending = models.FloatField(blank=True, null=True)
