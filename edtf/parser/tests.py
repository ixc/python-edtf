# ruff: noqa: S101 # Asserts are ok in tests

from datetime import date
from time import struct_time

import pytest

from edtf.parser.edtf_exceptions import EDTFParseException
from edtf.parser.grammar import parse_edtf as parse
from edtf.parser.parser_classes import TIME_EMPTY_EXTRAS, TIME_EMPTY_TIME, EDTFObject

# Example object types and attributes represented as tuples.
# The first item in each tuple is the input EDTF string, and expected parse result.
# where the first value is a tuple, the second item is a tuple of the normalised parse result.
#
# The values in the second tuple indicate the iso versions of the derived Python `date`s.
#  - If there is one other value, all the derived dates should be the same.
#  - If there are two other values, then all the lower values should be the same
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
    ("2001-02-03", ("2001-02-03",)),
    # year, month
    ("2008-12", ("2008-12-01", "2008-12-31")),
    # year
    ("2008", ("2008-01-01", "2008-12-31")),
    # a negative year
    ("-0999", ("-0999-01-01", "-0999-12-31")),
    # year zero
    ("0000", ("0000-01-01", "0000-12-31")),
    # DateTimes
    ("2001-02-03T09:30:01", ("2001-02-03",)),
    ("2004-01-01T10:10:10Z", ("2004-01-01",)),
    ("2004-01-01T10:10:10+05:00", ("2004-01-01",)),
    ("1985-04-12T23:20:30", ("1985-04-12",)),
    # Intervals
    # An interval beginning sometime in 1964 and ending sometime in 2008. Year precision.
    ("1964/2008", ("1964-01-01", "2008-12-31")),
    # An interval beginning sometime in June 2004 and ending sometime in August of 2006. Month precision.
    ("2004-06/2006-08", ("2004-06-01", "2006-08-31")),
    # An interval beginning sometime on February 1, 2004 and ending sometime on February 8, 2005. Day precision.
    ("2004-02-01/2005-02-08", ("2004-02-01", "2005-02-08")),
    # An interval beginning sometime on February 1, 2004 and ending sometime in February 2005.
    # The precision of the interval is not defined; the start endpoint has day precision and the end endpoint has month precision.
    ("2004-02-01/2005-02", ("2004-02-01", "2005-02-28")),
    # An interval beginning sometime on February 1, 2004 and ending sometime in 2005.
    # The start endpoint has day precision and the end endpoint has year precision.
    ("2004-02-01/2005", ("2004-02-01", "2005-12-31")),
    # An interval beginning sometime in 2005 and ending sometime in February 2006.
    ("2005/2006-02", ("2005-01-01", "2006-02-28")),
    # An interval beginning sometime in -2005 and ending sometime in February -2004.
    ("-2005/-1999-02", ("-2005-01-01", "-1999-02-28")),
    # ******************************* LEVEL 1 *********************************
    # Uncertain/Approximate
    # uncertain: possibly the year 1984, but not definitely
    ("1984?", ("1984-01-01", "1984-12-31", "1983-01-01", "1985-12-31")),
    (
        "2004-06-11?",
        ("2004-06-11", "2003-05-10", "2005-07-12"),
    ),  # everything is fuzzy by 100% for "qualification of a date (complete)" (L1)
    ("2004-06?", ("2004-06-01", "2004-06-30", "2003-05-01", "2005-07-30")),
    # "approximately" the year 1984
    ("1984~", ("1984-01-01", "1984-12-31", "1983-01-01", "1985-12-31")),
    # the year is approximately 1984 and even that is uncertain
    ("1984%", ("1984-01-01", "1984-12-31", "1982-01-01", "1986-12-31")),
    # Unspecified
    # some unspecified year in the 1990s.
    ("199X", ("1990-01-01", "1999-12-31")),
    # some unspecified year in the 1900s.
    ("19XX", ("1900-01-01", "1999-12-31")),
    # some month in 1999
    ("1999-XX", ("1999-01-01", "1999-12-31")),
    # some day in January 1999
    ("1999-01-XX", ("1999-01-01", "1999-01-31")),
    # some day in 1999
    ("1999-XX-XX", ("1999-01-01", "1999-12-31")),
    # negative unspecified year
    ("-01XX", ("-0199-01-01", "-0100-12-31")),
    # Uncertain/Approximate lower boundary dates (BCE)
    ("-0275~", ("-0275-01-01", "-0275-12-31", "-0276-01-01", "-0274-12-31")),
    ("-0001~", ("-0001-01-01", "-0001-12-31", "-0002-01-01", "0000-12-31")),
    ("0000~", ("0000-01-01", "0000-12-31", "-0001-01-01", "0001-12-31")),
    # Unspecified and qualified
    # "circa 17th century"
    ("16XX~", ("1600-01-01", "1699-12-31", "1500-01-01", "1799-12-31")),
    ("16XX%", ("1600-01-01", "1699-12-31", "1400-01-01", "1899-12-31")),
    ("1XXX", ("1000-01-01", "1999-12-31")),
    ("1XXX~", ("1000-01-01", "1999-12-31", "0000-01-01", "2999-12-31")),
    ("156X~", ("1560-01-01", "1569-12-31", "1550-01-01", "1579-12-31")),
    ("-01XX~", ("-0199-01-01", "-0100-12-31", "-0299-01-01", "0000-12-31")),
    # L1 Extended Interval
    # beginning unknown, end 2006
    # for intervals with an unknown beginning or end, the unknown bound is calculated with the constant DELTA_IF_UNKNOWN (10 years)
    ("/2006", ("1996-12-31", "2006-12-31")),
    # beginning June 1, 2004, end unknown
    ("2004-06-01/", ("2004-06-01", "2014-06-01")),
    # beginning open, end 2006
    ("../2006", ("-inf", "2006-12-31")),
    # beginning January 1, 2004 with no end date
    ("2004-01-01/..", ("2004-01-01", "inf")),
    # interval beginning approximately 1984 and ending June 2004
    ("1984~/2004-06", ("1984-01-01", "2004-06-30", "1983-01-01", "2004-06-30")),
    # interval beginning 1984 and ending approximately June 2004
    ("1984/2004-06~", ("1984-01-01", "2004-06-30", "1984-01-01", "2005-07-30")),
    ("1984?/2004%", ("1984-01-01", "2004-12-31", "1983-01-01", "2006-12-31")),
    ("1984~/2004~", ("1984-01-01", "2004-12-31", "1983-01-01", "2005-12-31")),
    # interval whose beginning is uncertain but thought to be 1984, and whose end is uncertain and approximate but thought to be 2004
    ("1984-06?/2004-08?", ("1984-06-01", "2004-08-31", "1983-05-01", "2005-09-30")),
    (
        "1984-06-02?/2004-08-08~",
        ("1984-06-02", "2004-08-08", "1983-05-01", "2005-09-09"),
    ),
    ("1984-06-02?/", ("1984-06-02", "1994-06-02", "1983-05-01", "1994-06-02")),
    # Year exceeding 4 digits
    ("Y170000002", ("170000002-01-01", "170000002-12-31")),
    ("Y-170000002", ("-170000002-01-01", "-170000002-12-31")),
    # Seasons
    ("2001-21", ("2001-03-01", "2001-05-31")),
    ("2003-22", ("2003-06-01", "2003-08-31")),
    ("2000-23", ("2000-09-01", "2000-11-30")),
    ("2010-24", ("2010-12-01", "2010-12-31")),
    # ******************************* LEVEL 2 *********************************
    # Qualification
    # Group qualification: a qualification character to the immediate right of a component applies
    # to that component as well as to all components to the left.
    # year, month, and day are uncertain and approximate
    # this example appears under "group qualification" but actually parses as L1 UncertainOrApproximate
    (
        "2004-06-11%",
        ("2004-06-11", "2002-04-09", "2006-08-13"),
    ),  # all parts to the left are fuzzy by 200%
    # uncertain year; month, day known
    ("2004?-06-11", ("2004-06-11", "2003-06-11", "2005-06-11")),
    # year and month are approximate; day known
    ("2004-06~-11", ("2004-06-11", "2003-05-11", "2005-07-11")),
    # Qualification of individual component: a qualification character to the immediate left
    # of the component applies to that component only
    # day is approximate; year, month known
    ("2004-06-~11", ("2004-06-11", "2004-06-10", "2004-06-12")),
    # Year known, month within year is approximate and uncertain
    ("2004-%06", ("2004-06-01", "2004-06-30", "2004-04-01", "2004-08-30")),
    # Year known, month and day uncertain
    ("2004-?06-?11", ("2004-06-11", "2004-05-10", "2004-07-12")),
    # Year uncertain, month known, day approximate
    ("2004?-06-~11", ("2004-06-11", "2003-06-10", "2005-06-12")),
    # Year uncertain and month is both uncertain and approximate
    ("?2004-%06", ("2004-06-01", "2004-06-30", "2003-04-01", "2005-08-30")),
    # This has the same meaning as the previous example.- NEW SPEC
    ("2004?-%06", ("2004-06-01", "2004-06-30", "2003-04-01", "2005-08-30")),
    # Year uncertain, month and day approximate
    ("2004?-~06-~04", ("2004-06-04", "2003-05-03", "2005-07-05")),
    # Year known, month and day approximate
    ("2011-~06-~04", ("2011-06-04", "2011-05-03", "2011-07-05")),
    # Partial unspecified
    # December 25 sometime during the 1560s
    ("156X-12-25", ("1560-12-25", "1569-12-25")),
    # December 25 sometime during the 1500s
    ("15XX-12-25", ("1500-12-25", "1599-12-25")),
    # Year and day of month specified, month unspecified
    ("1560-XX-25", ("1560-01-25", "1560-12-25")),
    ("15XX-12-XX", ("1500-12-01", "1599-12-31")),
    # Day specified, year and month unspecified
    ("XXXX-XX-23", ("0000-01-23", "9999-12-23")),
    # One of a Set
    # One of the years 1667, 1668, 1670, 1671, 1672
    ("[1667, 1668, 1670..1672]", ("1667-01-01", "1672-12-31")),
    # December 3, 1760 or some earlier date
    ("[..1760-12-03]", ("-inf", "1760-12-03")),
    # December 1760 or some later month
    ("[1760-12..]", ("1760-12-01", "inf")),
    # January or February of 1760 or December 1760 or some later month
    ("[1760-01, 1760-02, 1760-12..]", ("1760-01-01", "inf")),
    # Either the year 1667 or the month December of 1760.
    ("[1667, 1760-12]", ("1667-01-01", "1760-12-31")),
    # Multiple Dates
    # All of the years 1667, 1668, 1670, 1671, 1672
    ("{1667,1668, 1670..1672}", ("1667-01-01", "1672-12-31")),
    # The year 1960 and the month December of 1961.
    ("{1960, 1961-12}", ("1960-01-01", "1961-12-31")),
    # Previously tested masked precision, now eliminated from the spec
    # A date during the 1960s
    ("196X", ("1960-01-01", "1969-12-31")),
    # A date during the 1900s
    ("19XX", ("1900-01-01", "1999-12-31")),
    # L2 Extended Interval
    # Interval with fuzzy day endpoints in June 2004
    (
        "2004-06-~01/2004-06-~20",
        ("2004-06-01", "2004-06-20", "2004-05-31", "2004-06-21"),
    ),
    # The interval began on an unspecified day in June 2004.
    ("2004-06-XX/2004-07-03", ("2004-06-01", "2004-07-03")),
    # Year Requiring More than Four Digits - Exponential Form
    # the year 170000000
    ("Y17E7", ("170000000-01-01", "170000000-12-31")),
    # the year -170000000
    ("Y-17E7", ("-170000000-01-01", "-170000000-12-31")),
    # L2 significant digits
    # Some year between 1900 and 1999, estimated to be 1950
    ("1950S2", ("1950-01-01", "1950-12-31", "1900-01-01", "1999-12-31")),
    ("1953S2", ("1953-01-01", "1953-12-31", "1900-01-01", "1999-12-31")),
    ("1953S3", ("1953-01-01", "1953-12-31", "1950-01-01", "1959-12-31")),
    # Some year between 171010000 and 171999999, estimated to be 171010000 ('S3' indicates a precision of 3 significant digits.)
    (
        "Y17101E4S3",
        ("171010000-01-01", "171010000-12-31", "171000000-01-01", "171999999-12-31"),
    ),
    # Some year between 338000 and 338999, estimated to be 338800
    ("Y3388E2S3", ("338800-01-01", "338800-12-31", "338000-01-01", "338999-12-31")),
    # some year between 171000000 and 171999999 estimated to be 171010000
    (
        "Y171010000S3",
        ("171010000-01-01", "171010000-12-31", "171000000-01-01", "171999999-12-31"),
    ),
    # L2 Seasons
    # Spring southern hemisphere, 2001
    ("2001-29", ("2001-09-01", "2001-11-30")),
    # second quarter of 2001
    ("2001-34", ("2001-04-01", "2001-06-30")),
)

BENCHMARK_EXAMPLES = (
    "2001-02-03",
    "2008-12",
    "2008",
    "-0999",
    "2004-01-01T10:10:10+05:00",
    "-2005/-1999-02",
    "/2006",
    "?2004-%06",
    "[1667, 1760-12]",
    "Y3388E2S3",
    "2001-29",
)

APPROXIMATE_UNCERTAIN_EXAMPLES = (
    # first part of tuple is the input EDTF string, second part is a tuple of booleans:
    # uncertain ?, approximate ~, both uncertain and approximate %
    ("2004", (False, False, False)),
    ("2006-06-11", (False, False, False)),
    ("-0999", (False, False, False)),
    ("1984?", (True, False, False)),
    ("2004-06-11?", (True, False, False)),
    ("1984~", (False, True, False)),
    ("1984%", (False, False, True)),
    ("1984~/2004-06", (False, True, False)),
    ("2004-%06", (False, False, True)),
    ("2004?-~06-~04", (True, True, False)),
    ("2004?-06-04", (True, False, False)),
    ("2011-~06-~04", (False, True, False)),
    ("2004-06-~01/2004-06-~20", (False, True, False)),
    ("156X~", (False, True, False)),
)

BAD_EXAMPLES = (
    # parentheses are not used for group qualification in the 2018 spec
    None,
    "",
    "not a edtf string",
    "Y17E7-12-26",  # Y indicates that the date is year only
    "2016-13-08",  # wrong day order
    "2016-02-39",  # out of range
    "-0000-01-01",  # negative zero year
    "2004-(06)?-11",  # uncertain month, year and day known - OLD SPEC
    "2004-06-(11)~",  # day is approximate; year, month known - OLD SPEC
    "2004-(06)%",  # Year known, month within year is approximate and uncertain - OLD SPEC
    "2004-(06-11)?",  # Year known, month and day uncertain - OLD SPEC
    "2004?-06-(11)~",  # Year uncertain, month known, day approximate - OLD SPEC
    "(2004-(06)~)?",  # Year uncertain and month is both uncertain and approximate - OLD SPEC
    "(2004)?-06-04~",  # Year uncertain, month and day approximate.- OLD SPEC
    "(2011)-06-04~",  # Year known, month and day approximate. Note that this has the same meaning as the following.- OLD SPEC
    "2011-(06-04)~",  # Year known, month and day approximate.- OLD SPEC
    "2004-06-(01)~/2004-06-(20)~",  # An interval in June 2004 beginning approximately the first and ending approximately the 20th - OLD SPEC
)


def iso_to_struct_time(iso_date):
    """Convert YYYY-mm-dd date strings or infinities to time structs or float infinities."""
    if iso_date == "inf":
        return float("inf")
    elif iso_date == "-inf":
        return float("-inf")

    if iso_date[0] == "-":
        is_negative = True
        iso_date = iso_date[1:]
    else:
        is_negative = False
    y, mo, d = (int(i) for i in iso_date.split("-"))
    if is_negative:
        y *= -1
    return struct_time([y, mo, d] + TIME_EMPTY_TIME + TIME_EMPTY_EXTRAS)


@pytest.mark.parametrize("test_input,expected_tuple", EXAMPLES)
def test_edtf_examples(test_input, expected_tuple):
    """Test parsing of EDTF strings with expected outputs."""
    result = parse(test_input)
    assert isinstance(result, EDTFObject), "Result should be an instance of EDTFObject"

    # Extract only the date part if the result includes a time.
    result_date = str(result)
    if "T" in result_date:
        result_date = result_date.split("T")[0]

    # Unpack expected results based on their count
    if len(expected_tuple) == 1:
        assert result_date == expected_tuple[0], (
            f"Expected {expected_tuple[0]}, got {result_date}"
        )
    elif len(expected_tuple) == 2:
        lower_strict = iso_to_struct_time(expected_tuple[0])
        upper_strict = iso_to_struct_time(expected_tuple[1])
        assert result.lower_strict() == lower_strict, (
            f"Lower strict date does not match. Expected {lower_strict}, got {result.lower_strict()}"
        )
        assert result.upper_strict() == upper_strict, (
            f"Upper strict date does not match. Expected {upper_strict}, got {result.upper_strict()}"
        )
    elif len(expected_tuple) == 3:
        strict_date = iso_to_struct_time(expected_tuple[0])
        lower_fuzzy = iso_to_struct_time(expected_tuple[1])
        upper_fuzzy = iso_to_struct_time(expected_tuple[2])
        assert result.lower_strict() == strict_date, (
            f"Lower strict date does not match. Expected {strict_date}, got {result.lower_strict()}"
        )
        assert result.upper_strict() == strict_date, (
            f"Upper strict date does not match. Expected {strict_date}, got {result.upper_strict()}"
        )
        assert result.lower_fuzzy() == lower_fuzzy, (
            f"Lower fuzzy date does not match. Expected {lower_fuzzy}, got {result.lower_fuzzy()}"
        )
        assert result.upper_fuzzy() == upper_fuzzy, (
            f"Upper fuzzy date does not match. Expected {upper_fuzzy}, got {result.upper_fuzzy()}"
        )
    elif len(expected_tuple) == 4:
        lower_strict = iso_to_struct_time(expected_tuple[0])
        upper_strict = iso_to_struct_time(expected_tuple[1])
        lower_fuzzy = iso_to_struct_time(expected_tuple[2])
        upper_fuzzy = iso_to_struct_time(expected_tuple[3])
        assert result.lower_strict() == lower_strict, (
            f"Lower strict date does not match. Expected {lower_strict}, got {result.lower_strict()}"
        )
        assert result.upper_strict() == upper_strict, (
            f"Upper strict date does not match. Expected {upper_strict}, got {result.upper_strict()}"
        )
        assert result.lower_fuzzy() == lower_fuzzy, (
            f"Lower fuzzy date does not match. Expected {lower_fuzzy}, got {result.lower_fuzzy()}"
        )
        assert result.upper_fuzzy() == upper_fuzzy, (
            f"Upper fuzzy date does not match. Expected {upper_fuzzy}, got {result.upper_fuzzy()}"
        )


@pytest.mark.parametrize("bad_input", BAD_EXAMPLES)
def test_non_parsing(bad_input):
    """Test that non-parsing inputs correctly raise an exception."""
    with pytest.raises(EDTFParseException):
        parse(bad_input)


@pytest.mark.parametrize("bad_input", [None, ""])
def test_empty_input(bad_input):
    """Test that empty input raises a specific exception."""
    with pytest.raises(EDTFParseException) as exc_info:
        parse(bad_input)
    assert "You must supply some input text" in str(exc_info.value)


def test_comparisons():
    """Test comparisons between parsed EDTF objects and standard dates."""
    d1 = parse("1979-08~")
    d2 = parse("1979-08~")
    d3 = parse("1979-09-16")
    d4 = parse("1979-08-16")
    d5 = date(1979, 8, 16)
    d6 = date(1970, 9, 16)

    assert d1 == d2
    assert d1 != d3
    assert d1 >= d2
    assert d3 > d1
    assert d1 < d4
    assert d4 == d5
    assert d1 < d5
    assert d1 > d6


@pytest.mark.benchmark
@pytest.mark.parametrize("test_input", BENCHMARK_EXAMPLES)
def test_benchmark_parser(benchmark, test_input):
    """Benchmark parsing of selected EDTF strings."""
    benchmark(parse, test_input)


@pytest.mark.parametrize("test_input,expected_tuple", APPROXIMATE_UNCERTAIN_EXAMPLES)
def test_approximate_uncertain(test_input, expected_tuple):
    """Test parsing of EDTF strings and check .is_uncertain, .is_approximate,
    and .is_uncertain_and_approximate properties. The expected_tuple should have three
    values, the first should be a boolean indicating if the date is uncertain,
    the second should be a boolean indicating if the date is approximate, and the
    third should be a boolean indicating if the date is both uncertain and approximate."""
    result = parse(test_input)
    assert isinstance(result, EDTFObject), "Result should be an instance of EDTFObject"
    assert result.is_uncertain == expected_tuple[0]
    assert result.is_approximate == expected_tuple[1]
    assert result.is_uncertain_and_approximate == expected_tuple[2]
