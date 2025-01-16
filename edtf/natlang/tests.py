# ruff: noqa: S101 # Asserts are ok in tests

import pytest

from edtf.natlang.en import text_to_edtf


# TODO update the tests and code to test and output the new spec
# where examples are tuples, the second item is the normalised output
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        # Ignoring 'late' for simplicity in these examples
        ("active late 17th-19th centuries", "16XX/18XX"),
        ("active 17-19th Centuries", "16XX/18XX"),
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
        # Previously tested masked precision, uncertain or ambiguous masked precision
        ("1860s", "186X"),
        ("ca. 1860s", "186X~"),
        ("c. 1860s", "186X~"),
        ("Circa 1840s", "184X~"),
        ("circa 1840s", "184X~"),
        ("ca. 1860s?", "186X%"),
        ("uncertain: approx 1862", "1862%"),
        ("1800s", "18XX"),
        ("2000s", "20XX"),
        ("c1900s", "190X~"),
        ("c1800s?", "180X%"),
        # Unspecified dates
        ("January 12", "XXXX-01-12"),
        ("January", "XXXX-01"),
        ("10/7/2008", "2008-10-07"),
        ("7/2008", "2008-07"),
        # Seasons mapped to specific codes
        ("Spring 1872", "1872-21"),
        ("Summer 1872", "1872-22"),
        ("Autumn 1872", "1872-23"),
        ("Fall 1872", "1872-23"),
        ("Winter 1872", "1872-24"),
        # Dates relative to known events (before/after)
        ("earlier than 1928", "/1928"),
        ("before 1928", "/1928"),
        ("after 1928", "1928/"),
        ("later than 1928", "1928/"),
        ("before January 1928", "/1928-01"),
        ("before 18 January 1928", "/1928-01-18"),
        # Approximations combined with before/after
        ("before approx January 18 1928", "/1928-01-18~"),
        ("before approx January 1928", "/1928-01~"),
        ("after approx January 1928", "1928-01~/"),
        ("after approx Summer 1928", "1928-22~/"),
        # Before and after with uncertain / unspecified components
        ("after about the 1920s", "192X~/"),
        ("before about the 1900s", "/190X~"),
        ("before the 1900s", "/19XX"),
        # previous examples for masked precision, now removed from the EDTF spec
        # use `X` for unknown regardless of precision or why the data is unknown
        ("decade in 1800s", "18XX"),
        ("decade somewhere during the 1800s", "18XX"),
        ("year in the 1860s", "186X"),
        ("year in the 1800s", "18XX"),
        ("year in about the 1800s", "180X~"),
        ("month in 1872", "1872-XX"),
        ("day in Spring 1849", "1849-21-XX"),
        ("day in January 1872", "1872-01-XX"),
        ("day in 1872", "1872-XX-XX"),
        ("birthday in 1872", "1872"),
        # Handling centuries with approximation and uncertainty
        ("1st century", "00XX"),
        ("10c", "09XX"),
        ("19th century", "18XX"),
        ("19th century?", "18XX?"),
        ("before 19th century", "/18XX"),
        ("19c", "18XX"),
        ("15c.", "14XX"),
        ("ca. 19c", "18XX~"),
        ("~19c", "18XX~"),
        ("about 19c", "18XX~"),
        ("19c?", "18XX?"),
        ("c.19c?", "18XX%"),
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
        ("2nd century bc", "-01XX"),  # -200 to -101
        ("2nd century bce", "-01XX"),
        ("2nd century ad", "01XX"),
        ("2nd century ce", "01XX"),
        # Combining uncertainties and approximations in creative ways
        ("a day in about Spring 1849?", "1849-21-XX%"),
        # Simple date ranges, showcasing both the limitations and capabilities of the parser
        # Not all of these results are correct EDTF, but this is as good as the EDTF implementation
        # and simple natural language parser we have.
        ("1851-1852", "1851/1852"),
        ("1851-1852; printed 1853-1854", "1851/1852"),
        ("1851-52", "1851/1852"),
        ("1852 - 1860", "1852/1860"),
        ("1856-ca. 1865", "1856/1865~"),
        ("1857-mid 1860s", "1857/186X"),
        ("1858/1860", "[1858, 1860]"),
        ("1860s-1870s", "186X/187X"),
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
        ("1870s, printed ca. 1880s", "187X"),
        ("1900-1903, cast before 1929", "1900/1903"),
        ("1900; 1973", "1900"),
        ("1900; printed 1912", "1900"),
        ("1915 late - autumn 1916", "1915/1916-23"),
        ("1915, from Camerawork, October 1916", "1915"),  # should be {1915, 1916-10}
        ("1920s -early 1930s", "192X/193X"),
        (
            "1930s, printed early 1960s",
            "193X",
        ),  # should be something like {193x, 196x},
        ("1932, printed 1976 by Gunther Sander", "1932"),  # should be {1932, 1976}
        (
            "1938, printed 1940s-1950s",
            "1938",
        ),  # should be something like {1938, 194x-195x}
    ],
)
def test_natlang(input_text, expected_output):
    """
    Test natural language conversion to EDTF format:
    Verify that the conversion from text to EDTF format matches the expected output.
    """
    result = text_to_edtf(input_text)
    assert result == expected_output, (
        f"Failed for input: {input_text} - expected {expected_output}, got {result}"
    )


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("23rd Dynasty", None),
        ("January 2008", "2008-01"),
        ("ca1860", "1860~"),
        ("uncertain: approx 1862", "1862%"),
        ("January", "XXXX-01"),
        ("Winter 1872", "1872-24"),
        ("before approx January 18 1928", "/1928-01-18~"),
        ("birthday in 1872", "1872"),
        ("1270 CE", "1270"),
        ("2nd century bce", "-01XX"),
        ("1858/1860", "[1858, 1860]"),
    ],
)
def test_benchmark_natlang(benchmark, input_text, expected_output):
    """
    Benchmark selected natural language conversions
    """
    benchmark(text_to_edtf, input_text)
