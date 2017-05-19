import unittest
from parser import parse
from parser_classes import ParserObject

# where examples are tuples, the second item is the normalised output
EXAMPLES = (
    # Level 0
    '2001-02-03',  # year, month, day
    '2008-12',  # year, month
    '2008',  # year
    '-0999',  # a negative year
    '0000',  # year zero
    '2001-02-03T09:30:01',  #
    '2004-01-01T10:10:10Z',  #
    '2004-01-01T10:10:10+05:00',  #
    '1964/2008',
    # An interval beginning sometime in 1964 and ending sometime in 2008. Year precision.
    '2004-06/2006-08',
    # An interval beginning sometime in June 2004 and ending sometime in August of 2006. Month precision.
    '2004-02-01/2005-02-08',
    # An interval beginning sometime on February 1, 2004 and ending sometime on February 8, 2005. Day precision.
    '2004-02-01/2005-02',
    # An interval beginning sometime on February 1, 2004 and ending sometime in February 2005. The precision of the interval is not defined; the start endpoint has day precision and the end endpoint has month precision.
    '2004-02-01/2005',
    # An interval beginning sometime on February 1, 2004 and ending sometime in 2005. The start endpoint has day precision and the end endpoint has year precision.
    '2005/2006-02',
    # An interval beginning sometime in 2005 and ending sometime in February 2006.

    # Level 1
    # Uncertain/Approximate
    '1984?',  # uncertain: possibly the year 1984, but not definitely
    '2004-06?',
    '2004-06-11?',
    '1984~',  # "approximately" the year 1984
    '1984?~',  # the year is approximately 1984 and even that is uncertain
    # Unspecified
    '199u',  # some unspecified year in the 1990s.
    '19uu',  # some unspecified year in the 1900s.
    '1999-uu',  # some month in 1999
    '1999-01-uu',  # some day in January 1999
    '1999-uu-uu',  # some day in 1999
    # L1 Extended Interval
    'unknown/2006',  # beginning unknown, end 2006
    '2004-06-01/unknown',  # beginning June 1, 2004, end unknown
    '2004-01-01/open',  # beginning January 1 2004 with no end date
    '1984~/2004-06',
    # interval beginning approximately 1984 and ending June 2004
    '1984/2004-06~',
    # interval beginning 1984 and ending approximately June 2004
    '1984~/2004~',
    '1984?/2004?~',
    # interval whose beginning is uncertain but thought to be 1984, and whose end is uncertain and approximate but thought to be 2004
    '1984-06?/2004-08?',  #
    '1984-06-02?/2004-08-08~',  #
    '1984-06-02?/unknown',  #
    # Year exceeding 4 digits
    'y170000002',  # the year 170000002
    'y-170000002',  # the year -170000002
    # Seasons
    '2001-21',  # Spring, 2001
    '2003-22',  # Summer, 2003
    '2000-23',  # Autumn, 2000
    '2010-24',  # Winter, 2010

    # Level 2

    # Partial Uncertain/ Approximate
    '2004?-06-11', # uncertain year; month, day known
    '2004-06~-11', # year and month are approximate; day known
    '2004-(06)?-11', # uncertain month, year and day known
    '2004-06-(11)~', # day is approximate; year, month known
    '2004-(06)?~', # Year known, month within year is approximate and uncertain
    '2004-(06-11)?', # Year known, month and day uncertain
    '2004?-06-(11)~', # Year uncertain, month known, day approximate
    '(2004-(06)~)?', # Year uncertain and month is both uncertain and approximate
    '2004?-(06)?~',  # This has the same meaning as the previous example.
    ('(2004)?-06-04~', '2004?-06-04~'), # Year uncertain, month and day approximate.
    ('(2011)-06-04~', '2011-(06-04)~'), # Year known, month and day approximate. Note that this has the same meaning as the following.
    '2011-(06-04)~',  # Year known, month and day approximate.
    '2011-23~',  # Approximate season (around Autumn 2011)
    # Partial unspecified
    '156u-12-25',  # December 25 sometime during the 1560s
    '15uu-12-25',  # December 25 sometime during the 1500s
    '15uu-12-uu',
    '1560-uu-25',  # Year and day of month specified, month unspecified
    # One of a Set
    ('[1667,1668, 1670..1672]', '[1667, 1668, 1670..1672]'),  # One of the years 1667, 1668, 1670, 1671, 1672
    '[..1760-12-03]',  # December 3, 1760 or some earlier date
    '[1760-12..]',  # December 1760 or some later month
    '[1760-01, 1760-02, 1760-12..]', # January or February of 1760 or December 1760 or some later month
    '[1667, 1760-12]',  # Either the year 1667 or the month December of 1760.
    # Multiple Dates
    ('{1667,1668, 1670..1672}', '{1667, 1668, 1670..1672}'),  # All of the years 1667, 1668, 1670, 1671, 1672
    '{1960, 1961-12}',  # The year 1960 and the month December of 1961.
    # Masked Precision
    '196x',  # A date during the 1960s
    '19xx',  # A date during the 1900s
    # L2 Extended Interval
    '2004-06-(01)~/2004-06-(20)~', # An interval in June 2004 beginning approximately the first and ending approximately the 20th.
    '2004-06-uu/2004-07-03',
    # The interval began on an unspecified day in June 2004.
    # Year Requiring More than Four Digits - Exponential Form
    'y17e7',  # the year 170000000
    'y-17e7',  # the year -170000000
    'y17101e4p3', # Some year between 171000000 and 171999999, estimated to be 171010000 ('p3' indicates a precision of 3 significant digits.)

)

class TestLevel0(unittest.TestCase):

    def test_reversibility(self):
        """
        For each of the examples, establish that:
            - the unicode of the parsed object is acceptably equal to the EDTF string
            - the parsed object is a subclass of ParserObject
        :return: 
        """

        for i in EXAMPLES:
            if isinstance(i, tuple):
                i, o = i
            else:
                o = i
            print "parsing '%s'" % i
            f = parse(i)
            self.assertIsInstance(f, ParserObject)
            self.assertEqual(unicode(f), o)




if __name__ == '__main__':
    unittest.main()
