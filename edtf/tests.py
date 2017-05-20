from datetime import date
import unittest
from edtf import EDTF, EDTFDate, EDTFInterval

"""
Tests for EDTF compliance according to the features set out in
http://www.loc.gov/standards/datetime/pre-submission.html#table

Still to test (ie unimplemented):

Level 0 ISO 8601 Features
- Date and Time
- Interval (start/end)

Level 1 Extensions
- L1 Extended Interval

Level 2 Extensions
- partial uncertain/approximate
- one of a set
- multiple dates
- L2 extended Interval
- Year requiring more than 4 digits - Exponential form

"""

MIN_ISO = date.min.isoformat()
MAX_ISO = date.max.isoformat()


class TestEDTF(unittest.TestCase):

    def test_init(self):
        e = EDTFDate()
        self.assertEqual(unicode(e), "")

        e = EDTFDate('2001-02')
        self.assertEqual(unicode(e), '2001-02')

        e = EDTFDate(natural_text=None)
        self.assertEqual(unicode(e), "")

    def test_text(self):
        e = EDTF('1912-04-07~')
        self.assertEqual(e.edtf_text, '1912-04-07~')
        self.assertEqual(e.natural_text, '')
        self.assertEqual(e.display_text, '1912-04-07~')
        self.assertEqual(unicode(e), e.display_text)
        self.assertEqual(e.combined_text, u'`1912-04-07~`')

        e = EDTF(edtf_text='1912-04-07~', natural_text="Easter, 1912")
        self.assertEqual(e.edtf_text, '1912-04-07~')
        self.assertEqual(e.natural_text, 'Easter, 1912')
        self.assertEqual(e.display_text, u'Easter, 1912')
        self.assertEqual(unicode(e), e.display_text)
        self.assertEqual(e.combined_text, u'Easter, 1912 `1912-04-07~`')

        e = EDTF(natural_text="unparseable")
        self.assertEqual(e.edtf_text, '')
        self.assertEqual(e.natural_text, 'unparseable')
        self.assertEqual(e.display_text, u'unparseable')
        self.assertEqual(unicode(e), e.display_text)
        self.assertEqual(e.combined_text, u'unparseable')

        e = EDTF(natural_text="approx 7 april 1912")
        self.assertEqual(e.edtf_text, '1912-04-07~')
        self.assertEqual(e.natural_text, 'approx 7 april 1912')
        self.assertEqual(e.display_text, u'approx 7 april 1912')
        self.assertEqual(unicode(e), e.display_text)
        self.assertEqual(e.combined_text, u'approx 7 april 1912 `1912-04-07~`')

    def test_combined_text(self):

        e = EDTF('1912-04-07~')
        self.assertEqual(e.combined_text, u'`1912-04-07~`')
        f = EDTF.from_combined_text(e.combined_text)
        self.assertEqual(f, e)

        e = EDTF(edtf_text='1912-04-07~', natural_text="Easter, 1912")
        self.assertEqual(e.combined_text, u'Easter, 1912 `1912-04-07~`')
        f = EDTF.from_combined_text(e.combined_text)
        self.assertEqual(f, e)

        e = EDTF(natural_text="unparseable")
        self.assertEqual(e.combined_text, u'unparseable')
        f = EDTF.from_combined_text(e.combined_text)
        self.assertEqual(f, e)

        e = EDTF(natural_text="approx 7 april 1912")
        self.assertEqual(e.combined_text, u'approx 7 april 1912 `1912-04-07~`')
        f = EDTF.from_combined_text(e.combined_text)
        self.assertEqual(f, e)

        # Currently invalid edtf is kept
        # self.assertRaises(EDTFParseError, EDTF.from_combined_text, ('April `showers`'))


    def test_attributes(self):
        e = EDTFDate('2012-09-17')
        self.assertEqual(e.year, '2012')
        self.assertEqual(e.month, 9)
        self.assertEqual(e.month_string, '09')
        self.assertEqual(e.day, 17)
        self.assertEqual(e.day_string, '17')

        e = EDTFDate('2xuu-uu-uu')
        self.assertEqual(e.year, '2xuu')
        self.assertEqual(e.month, 'uu')
        self.assertEqual(e.month_string, 'uu')
        self.assertEqual(e.day, 'uu')
        self.assertEqual(e.day_string, 'uu')

        e = EDTFDate('2xuu')
        self.assertEqual(e.year, '2xuu')
        self.assertEqual(e.month, None)
        self.assertEqual(e.month_string, 'xx')
        self.assertEqual(e.day, None)
        self.assertEqual(e.day_string, 'xx')

        e = EDTFDate('2012-09-17')
        e.year = '2040'
        self.assertEqual(unicode(e), '2040-09-17')
        e.month = '04'
        self.assertEqual(unicode(e), '2040-04-17')
        e.day = '26'
        self.assertEqual(unicode(e), '2040-04-26')

        e.year = 1924
        e.month = 3
        e.day = 2
        self.assertEqual(unicode(e), '1924-03-02')

    def test_precision(self):
        for i, o in [
            (None, None),
            ('1xxx', 'millenium'),
            ('19xx', 'century'),
            ('198x', 'decade'),
            ('1984', 'year'),
            ('198u', 'year'),
            ('1984-12', 'month'),
            ('198u-12', 'month'),
            ('1984-uu', 'month'),
            ('198u-uu', 'month'),
            ('1984-12-20', 'day'),
            ('1984-12-uu', 'day'),
            ('198u-12-uu', 'day'),
        ]:
            e = EDTFDate(i)
            self.assertEqual(e.precision, o)

    def test_parse_errors(self):
        self.assertEqual(unicode(EDTFDate('xxxx')), "")
        self.assertEqual(unicode(EDTFDate('2010-1x')), "2010")
        self.assertEqual(unicode(EDTFDate('2010-10-0x')), "2010-10")
        self.assertEqual(unicode(EDTFDate('2010-10-0u')), "2010-10")
        self.assertEqual(unicode(EDTFDate('2010-1u-0u')), "2010")
        self.assertEqual(unicode(EDTFDate('2010-u1-0u')), "2010")

    def test_nullify(self):
        # set components to None
        e = EDTFDate('201x-09-17')

        e.day = None
        self.assertEqual(unicode(e), '201x-09')
        self.assertEqual(e.precision, 'month')

        e.month = None
        self.assertEqual(unicode(e), '201x')
        self.assertEqual(e.precision, 'decade')

        # again with empty strings
        e = EDTFDate('201x-09-17')

        e.day = ""
        self.assertEqual(unicode(e), '201x-09')
        self.assertEqual(e.precision, 'month')

        e.month = ""
        self.assertEqual(unicode(e), '201x')
        self.assertEqual(e.precision, 'decade')

        # clear month without clearing day
        e = EDTFDate('201x-09-17')
        e.month = ""
        self.assertEqual(unicode(e), '201x')
        self.assertEqual(e.precision, 'decade')
        e.month = 12
        self.assertEqual(unicode(e), '201x-12')
        self.assertEqual(e.precision, 'month')

        e.year = ""
        self.assertEqual(unicode(e), '')


    def test_uncertain(self):
        for i, o, o2 in [
            ('2010-09-03', False, '2010-09-03?'),
            ('2010-09-03?', True, '2010-09-03'),
            ('2010-09-03?~', True, '2010-09-03~'),
        ]:
            e = EDTFDate(i)
            self.assertEqual(e.is_uncertain, o)
            self.assertEqual(unicode(e), i)

            #change the value
            e.is_uncertain = not o
            self.assertAlmostEqual(unicode(e), o2)

    def test_approximate(self):
        for i, o1, o2, o3 in [
            # date, is_approximate, is_uncertain, date for almost-equal test
            ('2010-09-03', False, False, '2010-09-03~'),
            ('2010-09-03~', True, False, '2010-09-03'),
            ('2010-09-03?', False, True, '2010-09-03?~'),
            ('2010-09-03?~', True, True, '2010-09-03?'),
        ]:
            e = EDTFDate(i)
            self.assertEqual(e.is_approximate, o1)
            self.assertEqual(e.is_uncertain, o2)
            self.assertEqual(unicode(e), i)
            #change the is_approximate value
            e.is_approximate = not o1
            self.assertAlmostEqual(unicode(e), o3)

    def test_negative_year(self):
        e = EDTFDate('-0999')
        self.assertEqual(unicode(e), '-0999')

        # -0 is a different year to 0
        e = EDTFDate('0000')
        self.assertEqual(unicode(e), '0000')
        e.is_negative = True
        self.assertEqual(unicode(e), '-0000') # TODO: no such year; shouldn't be allowed.

    def test_unspecified(self):
        e = EDTFDate('199u')
        self.assertEqual(unicode(e), '199u')
        self.assertEqual(e.precision, "year")

        e = EDTFDate('19uu')
        self.assertEqual(unicode(e), '19uu')
        self.assertEqual(e.precision, "year")

        e = EDTFDate('1999-uu')
        self.assertEqual(unicode(e), '1999-uu')
        self.assertEqual(e.precision, "month")

        e = EDTFDate('1999-01-uu')
        self.assertEqual(unicode(e), '1999-01-uu')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('1999-uu-uu')
        self.assertEqual(unicode(e), '1999-uu-uu')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('1999-12-16')
        self.assertEqual(unicode(e), '1999-12-16')
        e.month = 'uu'
        self.assertEqual(unicode(e), '1999-uu-16')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('156u-12-25')
        self.assertEqual(unicode(e), '156u-12-25')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('15uu-12-25')
        self.assertEqual(unicode(e), '15uu-12-25')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('15uu-12-uu')
        self.assertEqual(unicode(e), '15uu-12-uu')
        self.assertEqual(e.precision, "day")

        e = EDTFDate('1560-uu-25')
        self.assertEqual(unicode(e), '1560-uu-25')
        self.assertEqual(e.precision, "day")

    def test_season(self):
        e = EDTFDate('2001-21')
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "spring")
        self.assertEqual(e.month, 21)

        e = EDTFDate('2001-22')
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "summer")
        self.assertEqual(e.month, 22)

        e = EDTFDate('2001-23')
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "autumn")
        self.assertEqual(e.month, 23)

        e = EDTFDate('2001-24')
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "winter")
        self.assertEqual(e.month, 24)

        e.season = "summer"
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "summer")
        self.assertEqual(e.month, 22)

        e.season = "fall"
        self.assertEqual(e.precision, "season")
        self.assertEqual(e.season, "autumn")
        self.assertEqual(e.month, 23)

        e.month = 11
        self.assertEqual(e.precision, "month")
        self.assertEqual(e.season, None)
        self.assertEqual(e.month, 11)

        e.month = 21
        self.assertEqual(e.season, "spring")
        self.assertEqual(e.precision, "season")

    def test_long_year(self):
        e = EDTFDate('y1700000002')
        self.assertEqual(e.precision, 'year')
        self.assertEqual(e.is_negative, False)
        e.is_negative = True
        self.assertEqual(e.year, 'y-1700000002')

        e = EDTFDate('y-1700000002')
        self.assertEqual(e.precision, 'year')
        self.assertEqual(e.is_negative, True)
        e.is_negative = False
        self.assertEqual(e.year, 'y1700000002')



    def test_iso_range(self):
        for i, o in [
            ('', (None, None)),
            ('2001-02-03', ('2001-02-03', '2001-02-03')),
            ('2008-12', ('2008-12-01', '2008-12-31')),
            ('2008', ('2008-01-01', '2008-12-31')),
            ('-0999', (MIN_ISO, MIN_ISO)),  # can we do better?
            ('0000', (MIN_ISO, MIN_ISO)),
            ('1984?', ('1983-07-01', '1985-06-30')),
            ('1985~', ('1984-07-01', '1986-06-30')),
            ('1984?~', ('1983-01-01', '1985-12-31')),
            ('2004-06?', ('2004-05-16', '2004-07-16')),
            ('2004-06?~', ('2004-04-30', '2004-08-01')),
            ('2000-01-01~', ('1999-12-31', '2000-01-02')),
            ('2000-01-01?~', ('1999-12-30', '2000-01-03')),
            ('1984-12-31~', ('1984-12-30', '1985-01-01')),
            ('1984-01~', ('1983-12-16', '1984-02-16')),
            ('1984-12~', ('1984-11-15', '1985-01-16')),
            ('199u', ('1990-01-01', '1999-12-31')),
            ('190u', ('1900-01-01', '1909-12-31')),
            ('19uu', ('1900-01-01', '1999-12-31')),
            ('1999-uu', ('1999-01-01', '1999-12-31')),
            ('1999-uu-uu', ('1999-01-01', '1999-12-31')),
            ('y170000002', (MAX_ISO, MAX_ISO)),  # can we do better?
            ('y-170000002', (MIN_ISO, MIN_ISO)),
            ('2001-21', ('2001-03-01', '2001-05-31')),  # northern hemisphere
            ('2001-22', ('2001-06-01', '2001-08-31')),  # northern hemisphere
            ('2001-23', ('2001-09-01', '2001-11-30')),  # northern hemisphere
            ('2001-24', ('2001-12-01', '2001-12-31')),  # northern hemisphere
            ('156u-12-25', ('1560-12-25', '1569-12-25')),
            ('15uu-12-25', ('1500-12-25', '1599-12-25')),
            ('15uu-12-uu', ('1500-12-01', '1599-12-31')),
            ('1560-uu-25', ('1560-01-25', '1560-12-25')),
            ('198x', ('1980-01-01', '1989-12-31')),
            ('19xx', ('1900-01-01', '1999-12-31')),
            ('1xxx', ('1000-01-01', '1999-12-31')),
            ('2001-21~', ('2000-12-07', '2001-08-23')),  # northern hemisphere
            ('2001-22~', ('2001-03-09', '2001-11-23')),  # northern hemisphere
            ('2001-23~', ('2001-06-09', '2002-02-22')),  # northern hemisphere
            ('2001-24~', ('2001-09-08', '2002-03-25')),  # northern hemisphere
            ('156u-12-25~', ('1560-12-24', '1569-12-26')),
            ('15uu-12-25~', ('1500-12-24', '1599-12-26')),
            ('15uu-12-uu~', ('1500-11-30', '1600-01-01')),
            ('1560-uu-25~', ('1560-01-24', '1560-12-26')),
            ('198x~', ('1975-01-01', '1994-12-31')),
            ('19xx~', ('1850-01-01', '2049-12-31')),
            ('1xxx~', ('0500-01-01', '2499-12-31')),
            ('0999-03~', ('0999-02-13', '0999-04-16')),
        ]:
            e = EDTFDate(i)
            o1, o2 = o
            earl = e.date_earliest()
            late = e.date_latest()
            if earl:
                self.assertEqual(earl.isoformat(), o1)
            if late:
                self.assertEqual(late.isoformat(), o2)

    def test_sort_value(self):
        for i, o1, o2 in [
            ('', None, None),
            ('2001-02-03', '2001-02-03', '2001-02-03'),
            ('2008-12', '2008-12-31', '2008-12-01'),
            ('2008', '2008-12-31', '2008-01-01'),
            ('-0999', MIN_ISO, MIN_ISO),  # can we do better?
            ('0000', MIN_ISO, MIN_ISO),
            ('1984?', '1984-12-31', '1984-01-01'),
            ('1984~', '1984-12-31', '1984-01-01'),
            ('1984?~', '1984-12-31', '1984-01-01'),
            ('2004-06?', '2004-06-30', '2004-06-01'),
            ('2004-06?~', '2004-06-30', '2004-06-01'),
            ('2000-01-01~', '2000-01-01', '2000-01-01'),
            ('2000-01-01?~', '2000-01-01', '2000-01-01'),
            ('1984-12-31~', '1984-12-31', '1984-12-31'),
            ('1984-01~', '1984-01-31', '1984-01-01'),
            ('1984-12~', '1984-12-31', '1984-12-01'),
            ('199u', '1999-12-31', '1990-01-01'),
            ('190u', '1909-12-31', '1900-01-01'),
            ('19uu', '1999-12-31', '1900-01-01'),
            ('1999-uu', '1999-12-31', '1999-01-01'),
            ('1999-uu-uu', '1999-12-31', '1999-01-01'),
            ('y170000002', MAX_ISO, MAX_ISO),  # can we do better?
            ('y-170000002', MIN_ISO, MIN_ISO),
            ('2001-21', '2001-05-31', '2001-03-01'),  # northern hemisphere
            ('2001-22', '2001-08-31', '2001-06-01'),  # northern hemisphere
            ('2001-23', '2001-11-30', '2001-09-01'),  # northern hemisphere
            ('2001-24', '2001-12-31', '2001-12-01'),  # northern hemisphere
            ('156u-12-25', '1569-12-25', '1560-12-25'),
            ('15uu-12-25', '1599-12-25', '1500-12-25'),
            ('15uu-12-uu', '1599-12-31', '1500-12-01'),
            ('1560-uu-25', '1560-12-25', '1560-01-25'),
            ('198x', '1989-12-31', '1980-01-01'),
            ('19xx', '1999-12-31', '1900-01-01'),
            ('1xxx', '1999-12-31', '1000-01-01'),
            ('2001-21~', '2001-05-31', '2001-03-01'),  # northern hemisphere
        ]:
            e = EDTFDate(i)
            earl = e.sort_date_earliest()
            late = e.sort_date_latest()
            if earl:
                self.assertEqual(earl.isoformat(), o2)
            if late:
                self.assertEqual(late.isoformat(), o1)

    def test_interval_sort_value(self):
        for i, o1, o2 in [
            ('2001/2004', '2004-12-31', '2001-01-01'),
            ('2001/unknown', '2001-12-31', '2001-01-01'),
            ('unknown/2001', '2001-12-31', '2001-01-01'),
            ('unknown/unknown', MAX_ISO, MIN_ISO),
        ]:
            e = EDTFInterval(i)
            self.assertEqual(e.sort_date_earliest().isoformat(), o2)
            self.assertEqual(e.sort_date_latest().isoformat(), o1)

    def test_interval_level_0(self):
        for i, o, r in [
            ('1964/2008', ('1964', '2008'),
             ('1964-01-01', '1964-12-31', '2008-01-01', '2008-12-31')
            ),
            ('2004-06/2006-08', ('2004-06', '2006-08'),
             ('2004-06-01', '2004-06-30', '2006-08-01', '2006-08-31')
            ),
            ('2004-02-01/2005-02-08', ('2004-02-01', '2005-02-08'),
             ('2004-02-01', '2004-02-01', '2005-02-08', '2005-02-08')
            ),
            ('2004-02-01/2005-02', ('2004-02-01', '2005-02'),
             ('2004-02-01', '2004-02-01', '2005-02-01', '2005-02-28')
            ),
            ('2004-02-01/2005', ('2004-02-01', '2005'),
             ('2004-02-01', '2004-02-01', '2005-01-01', '2005-12-31')
            ),
            ('2005/2006-02', ('2005', '2006-02'),
             ('2005-01-01', '2005-12-31', '2006-02-01', '2006-02-28')
            ),
        ]:
            o1, o2 = o
            e = EDTFInterval(i)
            self.assertEqual(unicode(e), i)
            self.assertEqual(unicode(e.start), o1)
            self.assertEqual(unicode(e.end), o2)

            start_earliest, start_latest, end_earliest, end_latest = r
            self.assertEqual(e.start_date_earliest().isoformat(), start_earliest)
            self.assertEqual(e.start_date_latest().isoformat(), start_latest)
            self.assertEqual(e.end_date_earliest().isoformat(), end_earliest)
            self.assertEqual(e.end_date_latest().isoformat(), end_latest)

    def test_interval_level_1(self):

        for i, r in [
            # unknown vs open at different precisions
            # assuming complete overlap
            # for open, we go to the max/min
            # for unknown, we add
            # if precision = millenium, 10000 years
            # if precision = century, 1000 years
            # if precision = decade, 100 years
            # if precision = year, 10 years
            # if precision = month, 1 year
            # if precision = day, 1 month
            ('2004-06-01/unknown',
             ('2004-06-01', '2004-06-01', '2004-06-01', '2004-07-01')),
            ('2004-06/unknown',
             ('2004-06-01', '2004-06-30', '2004-06-01', '2005-06-30')),
            ('2004/unknown',
            ('2004-01-01', '2004-12-31', '2004-01-01', '2009-12-31')),
            ('2004-01-01/open',
            ('2004-01-01', '2004-01-01', '2004-01-01', MAX_ISO)),
            ('2004-01/open',
            ('2004-01-01', '2004-01-31', '2004-01-01', MAX_ISO)),
            ('2004/open',
            ('2004-01-01', '2004-12-31', '2004-01-01', MAX_ISO)),

            ('unknown/2004-06-01',
             ('2004-05-01', '2004-06-01', '2004-06-01', '2004-06-01')),
            ('unknown/2004-06',
             ('2003-06-01', '2004-06-30', '2004-06-01', '2004-06-30')),
            ('unknown/2004',
             ('1999-01-01', '2004-12-31', '2004-01-01', '2004-12-31')),
            ('open/2004-06-01',
             (MIN_ISO, '2004-06-01', '2004-06-01', '2004-06-01')),
            ('open/2004-06',
             (MIN_ISO, '2004-06-30', '2004-06-01', '2004-06-30')),
            ('open/2004',
             (MIN_ISO, '2004-12-31', '2004-01-01', '2004-12-31')),

            #unknown vs open with different accuracies
            ('2004-06-01?~/unknown',
             ('2004-05-30', '2004-06-03', '2004-05-30', '2004-07-03')),
            ('2004-06?~/unknown',
             ('2004-04-30', '2004-08-01', '2004-04-30', '2005-08-01')),
            ('2004?~/unknown',
             ('2003-01-01', '2005-12-31', '2003-01-01', '2010-12-31')),
            ('2004-01-01?~/open',
             ('2003-12-30', '2004-01-03', '2003-12-30', MAX_ISO)),
            ('2004-01?~/open',
             ('2003-11-30', '2004-03-03', '2003-11-30', MAX_ISO)),
            ('2004?~/open',
             ('2003-01-01', '2005-12-31', '2003-01-01', MAX_ISO)),

            #weird ones
            ('open/open',
             (MIN_ISO, MAX_ISO, MIN_ISO, MAX_ISO)),
            ('open/unknown',
             (MIN_ISO, MAX_ISO, MIN_ISO, MAX_ISO)),
            ('unknown/open',
             (MIN_ISO, MAX_ISO, MIN_ISO, MAX_ISO)),
            ('unknown/unknown',
             (MIN_ISO, MAX_ISO, MIN_ISO, MAX_ISO)),

            # combinations of inaccuracies
            ('1984~/2004-06',
             ('1983-07-01', '1985-06-30', '2004-06-01', '2004-06-30')),
            ('1984/2004-06~',
             ('1984-01-01', '1984-12-31', '2004-05-16', '2004-07-16')),
            ('1984~/2004~',
             ('1983-07-01', '1985-06-30', '2003-07-01', '2005-06-30')),
            ('1984?/2004?~',
             ('1983-07-01', '1985-06-30', '2003-01-01', '2005-12-31')),
            ('1984-06?/2004-08?',
             ('1984-05-16', '1984-07-16', '2004-07-16', '2004-09-16')),
            ('1984-06-02?/2004-08-08~',
             ('1984-06-01', '1984-06-03', '2004-08-07', '2004-08-09')),
        ]:
            e = EDTFInterval(i)
            start_earliest, start_latest, end_earliest, end_latest = r
            self.assertEqual(e.start_date_earliest().isoformat(), start_earliest)
            self.assertEqual(e.start_date_latest().isoformat(), start_latest)
            self.assertEqual(e.end_date_earliest().isoformat(), end_earliest)
            self.assertEqual(e.end_date_latest().isoformat(), end_latest)

    def test_different_types(self):
        e = EDTF('1983')
        self.assertEqual(e.is_interval, False)
        self.assertEqual(e.sort_date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.sort_date_latest().isoformat(), '1983-12-31')
        self.assertEqual(e.date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.date_latest().isoformat(), '1983-12-31')
        self.assertEqual(e.start_date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.start_date_latest().isoformat(), '1983-01-01')
        self.assertEqual(e.end_date_earliest().isoformat(), '1983-12-31')
        self.assertEqual(e.end_date_latest().isoformat(), '1983-12-31')

        e = EDTF('1983/1985')
        self.assertEqual(e.is_interval, True)
        self.assertEqual(e.sort_date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.sort_date_latest().isoformat(), '1985-12-31')
        self.assertEqual(e.date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.date_latest().isoformat(), '1985-12-31')
        self.assertEqual(e.start_date_earliest().isoformat(), '1983-01-01')
        self.assertEqual(e.start_date_latest().isoformat(), '1983-12-31')
        self.assertEqual(e.end_date_earliest().isoformat(), '1985-01-01')
        self.assertEqual(e.end_date_latest().isoformat(), '1985-12-31')

    def test_unparseable(self):
        e = EDTF('terrible')
        self.assertEqual(e.is_interval, False)
        self.assertEqual(e.sort_date_earliest(), None)
        self.assertEqual(e.sort_date_latest(), None)
        self.assertEqual(e.date_earliest(), None)
        self.assertEqual(e.date_latest(), None)
        self.assertEqual(e.start_date_earliest(), None)
        self.assertEqual(e.start_date_latest(), None)
        self.assertEqual(e.end_date_earliest(), None)
        self.assertEqual(e.end_date_latest(), None)


if __name__ == '__main__':
    unittest.main()
