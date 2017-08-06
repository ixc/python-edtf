import unittest

from datetime import date

import sys

from edtf import parse_edtf as parse
from parser_classes import EDTFObject
from edtf_exceptions import EDTFParseException

# Example object types and attributes.
# the first item in each tuple is the input EDTF string, and expected parse result.
# where the first value is a tuple, the second item is the normalised parse result.
#
# The rest of the values in each tuple  indicate the iso versions of the derived
# Python ``date``s.
#  - If there's one other value, all the derived dates should be the same.
#  - If there're two other values, then all the lower values should be the same
#    and all the upper values should be the same.
#  - If there are three other values, then the upper and lower ``_strict`` values
#    should be the first value, and the upper and lower ``_fuzzy`` values should be
#    the last two.
#  - If there are four other values, then the first value is the lower strict,
#    the second value is the upper strict; the third value is the lower fuzzy date
#    and the final value is the upper fuzzy date.



EXAMPLES = (
    # ******************************* LEVEL 0 *********************************
    # year, month, day
    ('2001-02-03', '2001-02-03'),
    # year, month
    ('2008-12', '2008-12-01', '2008-12-31'),
    # year
    ('2008', '2008-01-01', '2008-12-31'),
    # a negative year
    ('-0999', date.min.isoformat()),
    # year zero
    ('0000', date.min.isoformat()),
    # DateTimes
    ('2001-02-03T09:30:01', '2001-02-03'),
    ('2004-01-01T10:10:10Z', '2004-01-01'),
    ('2004-01-01T10:10:10+05:00', '2004-01-01'),
    # An interval beginning sometime in 1964 and ending sometime in 2008. Year precision.
    ('1964/2008', '1964-01-01', '2008-12-31'),
    # An interval beginning sometime in June 2004 and ending sometime in August of 2006. Month precision.
    ('2004-06/2006-08', '2004-06-01', '2006-08-31'),
    # An interval beginning sometime on February 1, 2004 and ending sometime on February 8, 2005. Day precision.
    ('2004-02-01/2005-02-08', '2004-02-01', '2005-02-08'),
    # An interval beginning sometime on February 1, 2004 and ending sometime in February 2005. The precision of the interval is not defined; the start endpoint has day precision and the end endpoint has month precision.
    ('2004-02-01/2005-02', '2004-02-01', '2005-02-28'),
    # An interval beginning sometime on February 1, 2004 and ending sometime in 2005. The start endpoint has day precision and the end endpoint has year precision.
    ('2004-02-01/2005', '2004-02-01', '2005-12-31'),
    # An interval beginning sometime in 2005 and ending sometime in February 2006.
    ('2005/2006-02', '2005-01-01', '2006-02-28'),

    # ******************************* LEVEL 1 *********************************
    # Uncertain/Approximate
    # uncertain: possibly the year 1984, but not definitely
    ('1984?', '1984-01-01', '1984-12-31', '1983-01-01', '1985-12-31'),
    ('2004-06-11?', '2004-06-11', '2004-06-11', '2004-06-10', '2004-06-12'),
    ('2004-06?', '2004-06-01', '2004-06-30', '2004-05-01', '2004-07-30'),
    # "approximately" the year 1984
    ('1984~', '1984-01-01', '1984-12-31', '1983-01-01', '1985-12-31'),
    # the year is approximately 1984 and even that is uncertain
    ('1984?~', '1984-01-01', '1984-12-31', '1982-01-01', '1986-12-31'),
    # Unspecified
    # some unspecified year in the 1990s.
    ('199u', '1990-01-01', '1999-12-31'),
    # some unspecified year in the 1900s.
    ('19uu', '1900-01-01', '1999-12-31'),
    # some month in 1999
    ('1999-uu', '1999-01-01', '1999-12-31'),
    # some day in January 1999
    ('1999-01-uu', '1999-01-01', '1999-01-31'),
    # some day in 1999
    ('1999-uu-uu', '1999-01-01', '1999-12-31'),

    # L1 Extended Interval
    # beginning unknown, end 2006
    ('unknown/2006', '1996-12-31', '2006-12-31'),
    # beginning June 1, 2004, end unknown
    ('2004-06-01/unknown', '2004-06-01', '2014-06-01'),
    # beginning January 1 2004 with no end date
    ('2004-01-01/open', '2004-01-01', date.today().isoformat()),
    # interval beginning approximately 1984 and ending June 2004
    ('1984~/2004-06', '1984-01-01', '2004-06-30', '1983-01-01', '2004-06-30'),
    # interval beginning 1984 and ending approximately June 2004
    ('1984/2004-06~', '1984-01-01', '2004-06-30', '1984-01-01', '2004-07-30'),
    ('1984?/2004?~', '1984-01-01', '2004-12-31', '1983-01-01', '2006-12-31'),
    ('1984~/2004~', '1984-01-01', '2004-12-31', '1983-01-01', '2005-12-31'),
    # interval whose beginning is uncertain but thought to be 1984, and whose end is uncertain and approximate but thought to be 2004
    ('1984-06?/2004-08?', '1984-06-01', '2004-08-31', '1984-05-01', '2004-09-30'),
    ('1984-06-02?/2004-08-08~', '1984-06-02', '2004-08-08', '1984-06-01', '2004-08-09'),
    ('1984-06-02?/unknown', '1984-06-02', '1994-06-02', '1984-06-01', '1994-06-02'),
    # Year exceeding 4 digits
    # the year 170000002
    ('y170000002', date.max.isoformat()),
    # the year -170000002
    ('y-170000002', date.min.isoformat()),
    # Seasons
    # Spring, 2001
    ('2001-21', '2001-03-01', '2001-05-31'),
    # Summer, 2003
    ('2003-22', '2003-06-01', '2003-08-31'),
    # Autumn, 2000
    ('2000-23', '2000-09-01', '2000-11-30'),
    # Winter, 2010
    ('2010-24', '2010-12-01', '2010-12-31'),

    # ******************************* LEVEL 2 *********************************

    # Partial Uncertain/ Approximate
    # uncertain year; month, day known
    ('2004?-06-11', '2004-06-11', '2003-06-11', '2005-06-11'),
    # year and month are approximate; day known
    ('2004-06~-11', '2004-06-11', '2003-05-11', '2005-07-11'),
    # uncertain month, year and day known
    ('2004-(06)?-11', '2004-06-11', '2004-05-11', '2004-07-11'),
    # day is approximate; year, month known
    ('2004-06-(11)~', '2004-06-11', '2004-06-10', '2004-06-12'),
    # Year known, month within year is approximate and uncertain
    ('2004-(06)?~', '2004-06-01', '2004-06-30', '2004-04-01', '2004-08-30'),
    # Year known, month and day uncertain
    ('2004-(06-11)?', '2004-06-11', '2004-05-10', '2004-07-12'),
    # Year uncertain, month known, day approximate
    ('2004?-06-(11)~', '2004-06-11', '2003-06-10', '2005-06-12'),
    # Year uncertain and month is both uncertain and approximate
    ('(2004-(06)~)?', '2004-06-01', '2004-06-30', '2003-04-01', '2005-08-30'),
    # This has the same meaning as the previous example.
    ('2004?-(06)?~', '2004-06-01', '2004-06-30', '2003-04-01', '2005-08-30'),
    # Year uncertain, month and day approximate.
    (('(2004)?-06-04~', '2004?-06-04~'), '2004-06-04', '2003-05-03', '2005-07-05'),
    # Year known, month and day approximate. Note that this has the same meaning as the following.
    (('(2011)-06-04~', '2011-(06-04)~'), '2011-06-04', '2011-05-03', '2011-07-05'),
    # Year known, month and day approximate.
    ('2011-(06-04)~', '2011-06-04', '2011-05-03', '2011-07-05'),
    # Approximate season (around Autumn 2011)
    ('2011-23~', '2011-09-01', '2011-11-30', '2011-06-09', '2012-02-22'),
    # Years wrapping
    ('2011-24~', '2011-12-01', '2011-12-31', '2011-09-08', '2012-03-24'),
    # Partial unspecified
    # December 25 sometime during the 1560s
    ('156u-12-25', '1560-12-25', '1569-12-25'),
    # December 25 sometime during the 1500s
    ('15uu-12-25', '1500-12-25', '1599-12-25'),
    # Year and day of month specified, month unspecified
    ('1560-uu-25', '1560-01-25', '1560-12-25'),
    ('15uu-12-uu', '1500-12-01', '1599-12-31'),
    # One of a Set
    # One of the years 1667, 1668, 1670, 1671, 1672
    (('[1667,1668, 1670..1672]', '[1667, 1668, 1670..1672]'),  '1667-01-01', '1672-12-31'),
    # December 3, 1760 or some earlier date
    ('[..1760-12-03]', '1750-12-03', '1760-12-03'),
    # December 1760 or some later month
    ('[1760-12..]', '1760-12-01', '1770-12-01'),
    # January or February of 1760 or December 1760 or some later month
    ('[1760-01, 1760-02, 1760-12..]', '1760-01-01', '1770-12-01'),
    # Either the year 1667 or the month December of 1760.
    ('[1667, 1760-12]', '1667-01-01', '1760-12-31'),
    # Multiple Dates
    # All of the years 1667, 1668, 1670, 1671, 1672
    (('{1667,1668, 1670..1672}', '{1667, 1668, 1670..1672}'), '1667-01-01', '1672-12-31'),
    # The year 1960 and the month December of 1961.
    ('{1960, 1961-12}', '1960-01-01', '1961-12-31'),
    # Masked Precision
    # A date during the 1960s
    ('196x', '1960-01-01', '1969-12-31'),
    # A date during the 1900s
    ('19xx', '1900-01-01', '1999-12-31'),
    # L2 Extended Interval
    # An interval in June 2004 beginning approximately the first and ending approximately the 20th.
    ('2004-06-(01)~/2004-06-(20)~', '2004-06-01', '2004-06-20', '2004-05-31', '2004-06-21'),
    # The interval began on an unspecified day in June 2004.
    ('2004-06-uu/2004-07-03', '2004-06-01', '2004-07-03'),
    # Year Requiring More than Four Digits - Exponential Form
    # the year 170000000
    ('y17e7', date.max.isoformat()),
    # the year -170000000
    ('y-17e7', date.min.isoformat()),
    # Some year between 171000000 and 171999999, estimated to be 171010000 ('p3' indicates a precision of 3 significant digits.)
    ('y17101e4p3', date.max.isoformat()),
)

BAD_EXAMPLES = (
    None,
    '',
    'not a edtf string',
    'y17e7-12-26', # not implemented
    '2016-13-08', # wrong day order
    '2016-02-39', # out of range
    '-0000-01-01',  # negative zero year
)

class TestParsing(unittest.TestCase):

    def test_non_parsing(self):
        for i in BAD_EXAMPLES:
            self.assertRaises(EDTFParseException, parse, i)

    def test_date_values(self):
        """
        Test that every EDTFObject can tell you its lower and upper
        fuzzy and strict dates, and that they're what we think they should be.
        """

        for e in EXAMPLES:
            i = e[0]
            if isinstance(i, tuple):
                i, o = i
            else:
                o = i

            sys.stdout.write("parsing '%s'" % i)
            f = parse(i)
            sys.stdout.write(" => %s()\n" % type(f).__name__)
            self.assertIsInstance(f, EDTFObject)
            self.assertEqual(unicode(f), o)

            if len(e) == 5:
                expected_lower_strict = e[1]
                expected_upper_strict = e[2]
                expected_lower_fuzzy = e[3]
                expected_upper_fuzzy = e[4]
            elif len(e) == 4:
                expected_lower_strict = e[1]
                expected_upper_strict = e[1]
                expected_lower_fuzzy = e[2]
                expected_upper_fuzzy = e[3]
            elif len(e) == 3:
                expected_lower_strict = e[1]
                expected_upper_strict = e[2]
                expected_lower_fuzzy = e[1]
                expected_upper_fuzzy = e[2]
            elif len(e) == 2:
                expected_lower_strict = e[1]
                expected_upper_strict = e[1]
                expected_lower_fuzzy = e[1]
                expected_upper_fuzzy = e[1]
            if len(e) == 1:
                continue

            try:
                self.assertEqual(f.lower_strict().isoformat(), expected_lower_strict)
                self.assertEqual(f.upper_strict().isoformat(), expected_upper_strict)
                self.assertEqual(f.lower_fuzzy().isoformat(), expected_lower_fuzzy)
                self.assertEqual(f.upper_fuzzy().isoformat(), expected_upper_fuzzy)
            except Exception as x:
                print x
                import pdb; pdb.set_trace()

    def test_comparisons(self):
        d1 = parse("1979-08~")
        d2 = parse("1979-08~")
        d3 = parse("1979-09-16")
        d4 = parse("1979-08-16")
        d5 = date(1979, 8, 16)
        d6 = date(1970, 9, 16)

        self.assertEqual(d1, d2)
        self.assertNotEqual(d1, d3)
        self.assertTrue(d1 >= d2)
        self.assertTrue(d2 >= d1)
        self.assertTrue(d3 > d1)
        self.assertTrue(d1 < d4)

        # with python dates (EDTFFormat must be first operand)
        self.assertEqual(d4, d5)
        self.assertTrue(d1 < d5)
        self.assertTrue(d1 > d6)


if __name__ == '__main__':
    unittest.main()
