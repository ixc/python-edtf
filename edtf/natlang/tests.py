# ruff: noqa: S101 # Asserts are ok in tests

import pytest

from edtf.natlang.en import text_to_edtf

# TODO update the tests and code to test and output the new spec


# where examples are tuples, the second item is the normalised output
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        # Ignoring 'late' for simplicity in these examples
        ("active late 17th-19th centuries", "16xx/18xx"),
        ("active 17-19th Centuries", "16xx/18xx"),
        # Unrecognised values
        ("", None),
        ("this isn't a date", None),
        # Explicitly rejected values that would otherwise be badly converted
        ("23rd Dynasty", None),
        # Implied century and specific years
        ("90", "1990"),  # Implied century
        ("1860", "1860"),
        ("the year 1800", "1800"),
        ("the year 1897", "1897"),
        ("January 2008", "2008-01"),
        ("January 12, 1940", "1940-01-12"),
        # Uncertain or approximate dates
        ("1860?", "1860?"),
        ("1862 (uncertain)", "1862?"),
        ("maybe 1862", "1862?"),
        ("1862 maybe", "1862?"),
        ("1862 guess", "1862?"),
        ("uncertain: 1862", "1862?"),
        ("uncertain: Jan 18 1862", "1862-01-18?"),
        ("~ Feb 1812", "1812-02~"),
        ("circa Feb 1812", "1812-02~"),
        ("Feb 1812 approx", "1812-02~"),
        ("c1860", "1860~"),  # Different abbreviations
        ("c.1860", "1860~"),  # With or without .
        ("ca1860", "1860~"),
        ("ca.1860", "1860~"),
        ("c 1860", "1860~"),  # With or without space
        ("c. 1860", "1860~"),
        ("ca. 1860", "1860~"),
        ("approx 1860", "1860~"),
        ("1860 approx", "1860~"),
        ("1860 approximately", "1860~"),
        ("approximately 1860", "1860~"),
        ("about 1860", "1860~"),
        ("about Spring 1849", "1849-21~"),
        ("notcirca 1860", "1860"),  # Avoid words containing 'circa'
        (
            "attica 1802",
            "1802",
        ),  # Avoid false positive 'circa' at the end of preceding word
        ("attic. 1802", "1802"),  # Avoid false positive 'circa'
        # Masked precision
        ("1860s", "186x"),  # 186x has decade precision, 186u has year precision.
        # Masked precision + uncertainty
        ("ca. 1860s", "186x~"),
        ("c. 1860s", "186x~"),
        ("Circa 1840s", "184x~"),
        ("circa 1840s", "184x~"),
        ("ca. 1860s?", "186x?~"),
        ("uncertain: approx 1862", "1862?~"),
        # Ambiguous masked precision for centuries and decades
        ("1800s", "18xx"),  # Without additional uncertainty, use the century
        ("2000s", "20xx"),  # Without additional uncertainty, use the century
        ("c1900s", "190x~"),  # If there's additional uncertainty, use the decade
        ("c1800s?", "180x?~"),  # If there's additional uncertainty, use the decade
        # Unspecified dates
        ("January 12", "uuuu-01-12"),
        ("January", "uuuu-01"),
        ("10/7/2008", "2008-10-07"),
        ("7/2008", "2008-07"),
        # Seasons mapped to specific codes
        ("Spring 1872", "1872-21"),
        ("Summer 1872", "1872-22"),
        ("Autumn 1872", "1872-23"),
        ("Fall 1872", "1872-23"),
        ("Winter 1872", "1872-24"),
        # Dates relative to known events (before/after)
        ("earlier than 1928", "unknown/1928"),
        ("before 1928", "unknown/1928"),
        ("after 1928", "1928/unknown"),
        ("later than 1928", "1928/unknown"),
        ("before January 1928", "unknown/1928-01"),
        ("before 18 January 1928", "unknown/1928-01-18"),
        # Approximations combined with before/after
        ("before approx January 18 1928", "unknown/1928-01-18~"),
        ("before approx January 1928", "unknown/1928-01~"),
        ("after approx January 1928", "1928-01~/unknown"),
        ("after approx Summer 1928", "1928-22~/unknown"),
        # Before and after with uncertain / unspecified components
        ("after about the 1920s", "192x~/unknown"),
        ("before about the 1900s", "unknown/190x~"),
        ("before the 1900s", "unknown/19xx"),
        # Specifying unspecified components within a date
        # ('decade in 1800s', '18ux'), #too esoteric
        # ('decade somewhere during the 1800s', '18ux'), #lengthier. Keywords are 'in' or 'during'
        ("year in the 1860s", "186u"),  # 186x has decade precision
        ("year in the 1800s", "18xu"),  # 186u has year precision
        ("year in about the 1800s", "180u~"),
        ("month in 1872", "1872-uu"),
        ("day in Spring 1849", "1849-21-uu"),
        ("day in January 1872", "1872-01-uu"),
        ("day in 1872", "1872-uu-uu"),
        ("birthday in 1872", "1872"),
        # Handling centuries with approximation and uncertainty
        ("1st century", "00xx"),
        ("10c", "09xx"),
        ("19th century", "18xx"),
        ("19th century?", "18xx?"),
        ("before 19th century", "unknown/18xx"),
        ("19c", "18xx"),
        ("15c.", "14xx"),
        ("ca. 19c", "18xx~"),
        ("~19c", "18xx~"),
        ("about 19c", "18xx~"),
        ("19c?", "18xx?"),
        ("c.19c?", "18xx?~"),
        # BC/AD dating
        ("1 AD", "0001"),
        ("17 CE", "0017"),
        ("127 CE", "0127"),
        ("1270 CE", "1270"),
        ("c1 AD", "0001~"),
        ("c17 CE", "0017~"),
        ("c127 CE", "0127~"),
        ("c1270 CE", "1270~"),
        ("c64 BCE", "-0064~"),
        ("2nd century bc", "-01xx"),  # -200 to -101
        ("2nd century bce", "-01xx"),
        ("2nd century ad", "01xx"),
        ("2nd century ce", "01xx"),
        # Combining uncertainties and approximations in creative ways
        ("a day in about Spring 1849?", "1849-21-uu?~"),
        # Simple date ranges, showcasing both the limitations and capabilities of the parser
        # Not all of these results are correct EDTF, but this is as good as the EDTF implementation
        # and simple natural language parser we have.
        ("1851-1852", "1851/1852"),
        ("1851-1852; printed 1853-1854", "1851/1852"),
        ("1851-52", "1851/1852"),
        ("1852 - 1860", "1852/1860"),
        ("1856-ca. 1865", "1856/1865~"),
        ("1857-mid 1860s", "1857/186x"),
        ("1858/1860", "[1858, 1860]"),
        ("1860s-1870s", "186x/187x"),
        ("1910-30", "1910/1930"),
        ("active 1910-30", "1910/1930"),
        ("1861-67", "1861/1867"),
        ("1861-67 (later print)", "1861/1867"),
        ("1863 or 1864", "1863"),
        ("1863, printed 1870", "1863"),
        ("1863, printed ca. 1866", "1863"),
        ("1864 or 1866", "1864"),
        ("1864, printed ca. 1864", "1864"),
        ("1864-1872, printed 1870s", "1864/1872"),
        ("1868-1871?", "1868/1871?"),
        ("1869-70", "1869/1870"),
        ("1870s, printed ca. 1880s", "187x"),
        ("1900-1903, cast before 1929", "1900/1903"),
        ("1900; 1973", "1900"),
        ("1900; printed 1912", "1900"),
        ("1915 late - autumn 1916", "1915/1916-23"),
        ("1915, from Camerawork, October 1916", "1915"),  # should be {1915, 1916-10}
        ("1920s -early 1930s", "192x/193x"),
        (
            "1930s, printed early 1960s",
            "193x",
        ),  # should be something like {193x, 196x},
        ("1932, printed 1976 by Gunther Sander", "1932"),  # should be {1932, 1976}
        (
            "1938, printed 1940s-1950s",
            "1938",
        ),  # should be something like {1938, 194x-195x}
        # Uncertain and approximate on different parts of the date
        # for these to work we need to recast is_uncertain and is_approximate
        # such that they work on different parts. Probably worth rolling our own
        # dateparser at this point.
        # ('July in about 1849', '1849~-07'),
        # ('a day in July in about 1849', '1849~-07-uu'),
        # ('a day in Spring in about 1849', '1849~-21-uu'),
        # ('a day in about July? in about 1849', '1849~-07?~-uu'),
        # ('a day in about Spring in about 1849', '1849~-21~-uu'),
        # ('maybe January in some year in about the 1830s', '183u~-01?'),
        # ('about July? in about 1849', '1849~-07?~'),
    ],
)
def test_natlang(input_text, expected_output):
    """
    Test natural language conversion to EDTF format:
    Verify that the conversion from text to EDTF format matches the expected output.
    """
    result = text_to_edtf(input_text)
    assert result == expected_output, f"Failed for input: {input_text}"
