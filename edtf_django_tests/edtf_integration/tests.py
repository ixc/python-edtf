from django.test import TestCase

from edtf import EDTFObject, struct_time_to_jd
from edtf import parse_edtf as parse

from .models import TestEvent


class TestEventModelTests(TestCase):
    def setUp(self):
        # Create instances and assign them to instance variables
        # date_edtf_direct is a valid EDTF string, date_display is a date
        # to be parsed from natural language
        self.event1 = TestEvent.objects.create(date_edtf_direct="2020-03-15/2020-04-15")
        self.event2 = TestEvent.objects.create(date_edtf_direct="2021-05-06")
        self.event3 = TestEvent.objects.create(date_edtf_direct="2019-11")
        self.event4 = TestEvent.objects.create(date_display="Approximately August 2018")
        self.event5 = TestEvent.objects.create(date_edtf_direct="2021-05-06")

    def test_edtf_object_returned(self):
        for event in TestEvent.objects.all():
            self.assertIsInstance(event.date_edtf, EDTFObject)

    def test_sorting(self):
        events = list(TestEvent.objects.order_by("date_sort_ascending"))
        self.assertEqual(events[0].date_display, "Approximately August 2018")
        self.assertEqual(events[1].date_edtf_direct, "2019-11")
        self.assertEqual(events[2].date_edtf_direct, "2020-03-15/2020-04-15")
        self.assertEqual(events[3].date_edtf_direct, "2021-05-06")
        self.assertEqual(events[4].date_edtf_direct, "2021-05-06")

        events_desc = list(TestEvent.objects.order_by("-date_sort_descending"))
        self.assertEqual(events_desc[0].date_edtf_direct, "2021-05-06")
        self.assertEqual(events_desc[1].date_edtf_direct, "2021-05-06")
        self.assertEqual(events_desc[2].date_edtf_direct, "2020-03-15/2020-04-15")
        self.assertEqual(events_desc[3].date_edtf_direct, "2019-11")
        self.assertEqual(events_desc[4].date_display, "Approximately August 2018")

    def test_date_boundaries(self):
        event = TestEvent.objects.get(date_edtf_direct="2020-03-15/2020-04-15")
        expected_earliest_jd = struct_time_to_jd(parse("2020-03-15").lower_strict())
        expected_latest_jd = struct_time_to_jd(parse("2020-04-15").upper_strict())
        self.assertAlmostEqual(event.date_earliest, expected_earliest_jd, places=1)
        self.assertAlmostEqual(event.date_latest, expected_latest_jd, places=1)

        expected_earliest_jd = struct_time_to_jd(parse("2021-05-06").lower_strict())
        expected_latest_jd = struct_time_to_jd(parse("2021-05-06").upper_strict())
        self.assertAlmostEqual(
            self.event2.date_earliest, expected_earliest_jd, places=1
        )
        self.assertAlmostEqual(self.event2.date_latest, expected_latest_jd, places=1)

        event3 = TestEvent.objects.get(date_edtf_direct="2019-11")
        expected_earliest_jd = struct_time_to_jd(parse("2019-11").lower_strict())
        expected_latest_jd = struct_time_to_jd(parse("2019-11").upper_strict())
        self.assertAlmostEqual(event3.date_earliest, expected_earliest_jd, places=1)
        self.assertAlmostEqual(event3.date_latest, expected_latest_jd, places=1)

        event4 = TestEvent.objects.get(date_display="Approximately August 2018")
        expected_earliest_jd = struct_time_to_jd(parse("2018-08~").lower_fuzzy())
        expected_latest_jd = struct_time_to_jd(parse("2018-08~").upper_fuzzy())
        self.assertAlmostEqual(event4.date_earliest, expected_earliest_jd, places=1)
        self.assertAlmostEqual(event4.date_latest, expected_latest_jd, places=1)

    def test_date_display(self):
        """
        Test that the date_display field is correctly populated based on the EDTF input.
        In the future, a more sophisticated natural language parser could be used to generate
        a human readable date from the EDTF input.
        """
        event = TestEvent.objects.get(date_edtf_direct="2020-03-15/2020-04-15")
        self.assertEqual(event.date_display, "2020-03-15/2020-04-15")
        self.assertEqual(self.event2.date_display, "2021-05-06")
        self.assertEqual(self.event3.date_display, "2019-11")
        self.assertEqual(self.event4.date_display, "Approximately August 2018")

    def test_date_display_with_none_or_empty_string(self):
        """
        Test that the date_display field is correctly populated when the
        `natural_date` field is set to empty string (for example, if it
        were used with `null=False` in the model definition) or set to
        None (if it were used with `null=True`).
        """
        event = TestEvent(date_display="")
        event.date_edtf_direct = "2020-03-15/2020-04-15"
        # Trigger the descriptor to update the date_display field
        event.date_edtf = ""
        self.assertEqual(event.date_display, "2020-03-15/2020-04-15")

        event = TestEvent(date_display=None)
        # Verify date_display is set to None even though the field is `null=False`
        self.assertIsNone(event.date_display)
        event.date_edtf_direct = "2020-03-15/2020-04-15"
        event.date_edtf = ""
        self.assertEqual(event.date_display, "2020-03-15/2020-04-15")

    def test_comparison(self):
        # test equality of the same dates
        self.assertEqual(
            self.event2.date_edtf,
            self.event5.date_edtf,
            "Events with the same date should be equal",
        )

        # test inequality of different dates
        self.assertNotEqual(
            self.event1.date_edtf,
            self.event2.date_edtf,
            "Events with different dates should not be equal",
        )

        # greater than
        self.assertGreater(
            self.event2.date_edtf,
            self.event3.date_edtf,
            "2021-05-06 is greater than 2019-11",
        )

        # less than
        self.assertLess(
            self.event3.date_edtf,
            self.event2.date_edtf,
            "2019-11 is less than 2021-05-06",
        )

    def test_field_related_field_specification(self):
        edtf_field_on_model = TestEvent._meta.get_field("date_edtf")
        required_fields = (
            "direct_input_field",
            "lower_fuzzy_field",
            "lower_strict_field",
            "natural_text_field",
            "upper_fuzzy_field",
            "upper_strict_field",
        )
        for field_alias in required_fields:
            # Remove the alias from the edtf_field
            orig_value = getattr(edtf_field_on_model, field_alias)
            setattr(edtf_field_on_model, field_alias, None)
            errors = edtf_field_on_model.check()
            self.assertEqual(len(errors), 1)
            self.assertTrue(field_alias in errors[0].msg)
            # Should be an 'alias not specified' error
            self.assertEqual(errors[0].id, "python-edtf.EDTF01")

            # Point the alias to a non-existent field
            setattr(edtf_field_on_model, field_alias, "fake")
            errors = edtf_field_on_model.check()
            self.assertEqual(len(errors), 1)
            self.assertTrue(field_alias in errors[0].msg)
            # Should be a 'non-eixstent field' error
            self.assertEqual(errors[0].id, "python-edtf.EDTF02")

            # Repair the field so later tests can still work
            setattr(edtf_field_on_model, field_alias, orig_value)
