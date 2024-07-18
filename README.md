# python-edtf

<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->

An implementation of EDTF format in Python, together with utility functions for parsing natural language date texts, and converting EDTF dates to related Python `date` or `struct_time` objects.

See <http://www.loc.gov/standards/datetime/> for the final draft specification.

This project is based on python-edtf and was developed to include the newest specification

## To install

```shell
pip install edtf
```

## To use

```python
>>> from edtf import parse_edtf

# Parse an EDTF string to an EDTFObject
>>>
>>> e = parse_edtf("1979-08~") # approx August 1979
>>> e
UncertainOrApproximate: '1979-08~'

# normalised string representation (some different EDTF strings have identical meanings)
>>>
>>> unicode(e)
u'1979-08~'

# Derive Python date objects

# lower and upper bounds that strictly adhere to the given range
>>>
>>> e.lower_strict()[:3], e.upper_strict()[:3]
((1979, 8, 1), (1979, 8, 31))

# lower and upper bounds that are padded if there's indicated uncertainty
>>>
>>> e.lower_fuzzy()[:3], e.upper_fuzzy()[:3]
((1979, 7, 1), (1979, 9, 30))

# Date intervals
>>>
>>> interval = parse_edtf("1979-08~/..")
>>> interval
Level1Interval: '1979-08~/..'

# Intervals have lower and upper EDTF objects
>>>
>>> interval.lower, interval.upper
(UncertainOrApproximate: '1979-08~', UnspecifiedIntervalSection: '..')
>>> interval.lower.lower_strict()[:3], interval.lower.upper_strict()[:3]
((1979, 8, 1), (1979, 8, 31))
>>> interval.upper.upper_strict() # '..' is interpreted to mean open interval and is returning -/+ math.inf
math.inf

# Date collections
>>>
>>> coll = parse_edtf('{1667,1668, 1670..1672}')
>>> coll
MultipleDates: '{1667, 1668, 1670..1672}'
>>> coll.objects
(Date: '1667', Date: '1668', Consecutives: '1670..1672')
```

The object returned by `parse_edtf()` is an instance of an `edtf.parser.parser_classes.EDTFObject` subclass, depending on the type of date that was parsed. These classes are:

```text
# Level 0
Date
DateAndTime
Interval

# Level 1
UncertainOrApproximate
Unspecified
Level1Interval
UnspecifiedIntervalSection
LongYear
Season

# Level 2
PartialUncertainOrApproximate
PartialUnspecified
OneOfASet
MultipleDates
Level2Interval
Level2Season
ExponentialYear
```

All of these implement `upper/lower_strict/fuzzy()` methods to derive `struct_time` objects, except of UnspecifiedIntervalSection, that can also return math.inf value

The `*Interval` instances have `upper` and `lower` properties that are themselves `EDTFObject` instances.

`OneOfASet` and `MultipleDates` instances have an `objects` property that is a list of all of the EDTF dates parsed in the set or list.

## EDTF Specification Inclusions

The library includes implementation of levels 0, 1 and 2 of the EDTF spec.

Test coverage includes every example given in the spec table of features.

### Level 0 ISO 8601 Features

* Date:

```python
>>> parse_edtf('1979-08') # August 1979
Date: '1979-08'
```

* Date and Time:

```python
>>> parse_edtf('2004-01-01T10:10:10+05:00')
DateAndTime: '2004-01-01T10:10:10+05:00'
```

* Interval (start/end):

```python
>>> parse_edtf('1979-08-28/1979-09-25') # From August 28 to September 25 1979
Interval: '1979-08-28/1979-09-25'
```

### Level 1 Extensions

* Uncertain/Approximate dates:

```python
>>> parse_edtf('1979-08-28~') # Approximately August 28th 1979
UncertainOrApproximate: '1979-08-28~'
```

* Unspecified dates:

```python
>>> parse_edtf('1979-08-XX') # An unknown day in August 1979
Unspecified: '1979-08-XX'
>>> parse_edtf('1979-XX') # Some month in 1979
Unspecified: '1979-XX'
```

* Extended intervals:

```python
>>> parse_edtf('1984-06-02?/2004-08-08~')
Level1Interval: '1984-06-02?/2004-08-08~'
```

* Years exceeding four digits:

```python
>>> parse_edtf('Y-12000') # 12000 years BCE
LongYear: 'Y-12000'
```

* Season:

```python
>>> parse_edtf('1979-22') # Summer 1979
Season: '1979-22'
```

### Level 2 Extensions

* Partial uncertain/approximate:

```python
>>> parse_edtf('2004-06~-11') # year certain, month/day approximate.
PartialUncertainOrApproximate: '2004-06~-11'
```

* Partial unspecified:

```python
>>> parse_edtf('1979-XX-28') # The 28th day of an uncertain month in 1979
PartialUnspecified: '1979-XX-28'
```

* One of a set:

```python
>>> parse_edtf("[..1760-12-03,1762]")
OneOfASet: '[..1760-12-03, 1762]'
```

* Multiple dates:

```python
>>> parse_edtf('{1667,1668, 1670..1672}')
MultipleDates: '{1667, 1668, 1670..1672}'
```

* Level 2 Extended intervals:

```python
>>> parse_edtf('2004-06-~01/2004-06-~20')
Level2Interval: '2004-06-~01/2004-06-~20'
```

* Year requiring more than 4 digits - exponential form:

```python
>>> e = parse_edtf('Y-17E7')
ExponentialYear: 'Y-17E7'
>>> e.estimated()
-170000000
```

* Significant digits:

```python
# '1950S2': some year between 1900 and 1999, estimated to be 1950
>>> d = parse_edtf('1950S2')
Date: '1950S2'
>>> d.lower_fuzzy()[:3]
(1900, 1, 1)
>>> d.upper_fuzzy()[:3]
(1999, 12, 31)
# 'Y171010000S3': some year between 171000000 and 171999999 estimated to be 171010000, with 3 significant digits.
>>> l = parse_edtf('Y171010000S3')
LongYear: 'Y171010000S3'
>>> l.estimated()
171010000
>>> l.lower_fuzzy()[:3]
(171000000, 1, 1)
>>> l.upper_fuzzy()[:3]
(171999999, 12, 31)
# 'Y3388E2S3': some year in exponential notation between 338000 and 338999, estimated to be 338800
>>> e = parse_edtf('Y3388E2S3')
ExponentialYear: 'Y3388E2S3S3'
>>> e.estimated()
338800
>>> e.lower_fuzzy()[:3]
(338000, 1, 1)
>>> e.upper_fuzzy()[:3]
(338999, 12, 31)
```

### Natural language representation

The library includes a basic English natural language parser (it's not yet smart enough to work with occasions such as 'Easter', or in other languages):

```python
>>> from edtf import text_to_edtf
>>> text_to_edtf("circa August 1979")
'1979-08~'
```

Note that the result is a string, not an `ETDFObject`.

The parser can parse strings such as:

```text
'January 12, 1940' => '1940-01-12'
'90' => '1990' #implied century
'January 2008' => '2008-01'
'the year 1800' => '1800'
'10/7/2008' => '2008-10-07' # in a full-specced date, assume US ordering

# uncertain/approximate
'1860?' => '1860?'
'1862 (uncertain)' => '1862?'
'circa Feb 1812' => '1812-02~'
'c.1860' => '1860~' #with or without .
'ca1860' => '1860~'
'approx 1860' => '1860~'
'ca. 1860s' => '186X~'
'circa 1840s' => '184X~'
'ca. 1860s?' => '186X?~'
'c1800s?' => '180X?~' # with uncertainty indicators, use the decade

# unspecified parts
'January 12' => 'XXXX-01-12'
'January' => 'XXXX-01'
'7/2008' => '2008-07'
'month in 1872' => '1872-XX'
'day in January 1872' => '1872-01-XX'
'day in 1872' => '1872-XX-XX'

#seasons
'Autumn 1872' => '1872-23'
'Fall 1872' => '1872-23'

# before/after
'earlier than 1928' => '/1928'
'later than 1928' => '1928/'
'before January 1928' => '/1928-01'
'after about the 1920s' => '192X~/'

#centuries
'1st century' => '00XX'
'10c' => '09XX'
'19th century?' => '18XX?'

# just showing off now...
'a day in about Spring 1849?' => '1849-21-XX?~'

# simple ranges, which aren't as accurate as they could be. The parser is
limited to only picking the first year range it finds.
'1851-1852' => '1851/1852'
'1851-1852; printed 1853-1854' => '1851/1852'
'1851-52' => '1851/1852'
'1856-ca. 1865' => '1856/1865~'
'1860s-1870s' => '186X/187X'
'1920s - early 1930s' => '192X/193X'
'1938, printed 1940s-1950s' => '1938'
```

Generating natural text from an EDTF representation is a future goal.

### What assumptions does the natural text parser make when interpreting an ambiguous date?

* "1800s" is ambiguously a century or decade. If the given date is either uncertain or approximate, the decade interpretation is used. If the date is certain and precise, the century interpretation is used.

* If the century isn't specified (`EDTF(natural_text="the '70s")`), we imply the century to be "19" if the year is greater than the current year, otherwise we imply the century to be the current century.

* US-ordered dates (mm/dd/yyyy) are assumed by default in natural language.  To change this, set `DAY_FIRST` to True in settings.

* If a natural language groups dates with a '/', it's interpreted as "or" rather than "and". The resulting EDTF text is a list bracketed by `[]` ("one of these dates") rather than `{}` (all of these dates).

## Converting to and from Python dates

Since EDTF dates are often regions, and often imprecise, we need to use a few different Python dates, depending on the circumstance. Generally, Python dates are used for sorting and filtering, and are not displayed directly to users.

### `struct_time` date representation

Because Python's `datetime` module does not support dates out side the range 1 AD to 9999 AD we return dates as `time.struct_time` objects by default instead of the `datetime.date` or `datetime.datetime` objects you might expect.

The `struct_time` representation is more difficult to work with, but can be sorted as-is which is the primary use-case, and can be converted relatively easily to `date` or `datetime` objects (provided the year is within 1 to 9999 AD) or to date objects in more flexible libraries like [astropy.time](http://docs.astropy.org/en/stable/time/index.html) for years outside these bounds.

If you are sure you are working with dates within the range supported by Python's `datetime` module, you can get these more convenient objects using the `edtf.struct_time_to_date` and `edtf.struct_time_to_datetime` functions.

> [!NOTE]
> This library previously did return `date` and `datetime` objects from methods by default before we switched to `struct_time`. See ticket <https://github.com/ixc/python-edtf/issues/26>.

### `lower_strict` and `upper_strict`

These dates indicate the earliest and latest dates that are __strictly__ in the date range, ignoring uncertainty or approximation. One way to think about this is 'if you had to pick a single date to sort by, what would it be?'.

In an ascending sort (most recent last), sort by `lower_strict` to get a natural sort order. In a descending sort (most recent first), sort by `upper_strict`:

```python
>>> e = parse_edtf('1912-04~')

>>> e.lower_strict()  # Returns struct_time
>>> time.struct_time(tm_year=1912, tm_mon=4, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0, tm_wday=0, tm_yday=0, tm_isdst=-1)

>>> e.lower_strict()[:3]  # Show only interesting parts of struct_time
(1912, 4, 01)

>>> from edtf import struct_time_to_date
>>> struct_time_to_date(e.lower_strict())  # Convert to date
datetime.date(1912, 4, 01)

>>> e.upper_strict()[:3]
(1912, 4, 30)

>>> struct_time_to_date(e.upper_strict())
datetime.date(1912, 4, 30)
```

### `lower_fuzzy` and `upper_fuzzy`

These dates indicate the earliest and latest dates that are __possible__ in the date range, for a fairly arbitrary definition of 'possibly'.

These values are useful for filtering results - i.e. testing which EDTF dates might conceivably fall into, or overlap, a desired date range.

The fuzzy dates are derived from the strict dates, plus or minus a level of padding that depends on how precise the date specfication is. For the case of approximate or uncertain dates, we (arbitrarily) pad the ostensible range by 100% of the uncertain timescale, or by a 12 weeks in the case of seasons. That is, if a date is approximate at the month scale, it is padded by a month. If it is approximate at the year scale, it is padded by a year:

```python
>>> e = parse_edtf('1912-04~')
>>> e.lower_fuzzy()[:3]  # padding is 100% of a month
(1912, 3, 1)
>>> e.upper_fuzzy()[:3]
(1912, 5, 30)

>>> e = parse_edtf('1912~')
>>> e.lower_fuzzy()[:3]  # padding is 100% of a year
(1911, 1, 1)
>>> e.upper_fuzzy()[:3]
(1913, 12, 31)
```

One can interpret uncertain or approximate dates as 'plus or minus a [level of precision]'.

If a date is both uncertain __and__ approximate, the padding is applied twice, i.e. it gets 100% * 2 padding, or 'plus or minus two [levels of precision]'.

### Qualification properties

EDTF objects support properties that provide an overview of how the object is qualified:

* `.is_uncertain (?)`
* `.is_approximate (~)`
* `.is_uncertain_and_approximate (%)`

These properties represent whether the any part of the date object is uncertain, approximate, or uncertain and approximate. For ranges, the properties are true if any part of the range (lower or upper section) is qualified as such. A date is not necessarily uncertain and approximate if it is separately both uncertain and approximate - it must have the "%" qualifier to be considered uncertain and aproximate.

```python
>>> parse_edtf("2006-06-11")
Date: '2006-06-11'
>>> parse_edtf("2006-06-11").is_uncertain
False
>>> parse_edtf("2006-06-11").is_approximate
False

>>> parse_edtf("1984?")
UncertainOrApproximate: '1984?'
>>> parse_edtf("1984?").is_approximate
False
>>> parse_edtf("1984?").is_uncertain
True
>>> parse_edtf("1984?").is_uncertain_and_approximate
False

>>> parse_edtf("1984%").is_uncertain
False
>>> parse_edtf("1984%").is_uncertain_and_approximate
True

>>> parse_edtf("1984~/2004-06")
Level1Interval: '1984~/2004-06'
>>> parse_edtf("1984~/2004-06").is_approximate
True
>>> parse_edtf("1984~/2004-06").is_uncertain
False

>>> parse_edtf("2004?-~06-~04")
PartialUncertainOrApproximate: '2004?-~06-~04'
>>> parse_edtf("2004?-~06-~04").is_approximate
True
>>> parse_edtf("2004?-~06-~04").is_uncertain
True
>>> parse_edtf("2004?-~06-~04").is_uncertain_and_approximate
False
```

### Seasons

> [!IMPORTANT]
> Seasons are interpreted as Northern Hemisphere by default. To change this, override the month mapping in [`appsettings.py`](edtf/appsettings.py).

### Comparisons

Two EDTF dates are considered equal if their `unicode()` representations are the same. An EDTF date is considered greater than another if its `lower_strict` value is later.

## Django ORM field

The `edtf.fields.EDTFField` implements a simple Django field that stores an EDTF object in the database.

To store a natural language value on your model, define another field, and set the `natural_text_field` parameter of your `EDTFField`.

When your model is saved, the `natural_text_field` value will be parsed to set the `date_edtf` value, and the underlying EDTF object will set the `_earliest` and `_latest` fields on the model to a float value representing the Julian Date.

> [!WARNING]
> The conversion to and from Julian Date numerical values can be inaccurate, especially for ancient dates back to thousands of years BC. Ideally Julian Date values should be used for range and ordering operations only where complete accuracy is not required. They should __not__ be used for definitive storage or for display after roundtrip conversions.

Example usage:

```python
from django.db import models
from edtf.fields import EDTFField

class MyModel(models.Model):
        date_display = models.CharField(
        "Date of creation (display)",
        blank=True,
        max_length=255,
        )
        date_edtf = EDTFField(
        "Date of creation (EDTF)",
        natural_text_field='date_display',
        lower_fuzzy_field='date_earliest',
        upper_fuzzy_field='date_latest',
        lower_strict_field='date_sort_ascending',
        upper_strict_field='date_sort_descending',
        blank=True,
        null=True,
        )
        # use for filtering
        date_earliest = models.FloatField(blank=True, null=True)
        date_latest = models.FloatField(blank=True, null=True)
        # use for sorting
        date_sort_ascending = models.FloatField(blank=True, null=True)
        date_sort_descending = models.FloatField(blank=True, null=True)
```

Since the `EDTFField` and the `_earliest` and `_latest` field values are set automatically, you may want to make them readonly, or not visible in your model admin.

## To develop

### Setup

* Clone the repository: `git clone https://github.com/ixc/python-edtf.git`
* Set up a virtual environment: `python3 -m venv venv`
* Install the dependencies: `pip install -r dev-requirements.txt`
* Install precommit hooks: `pre-commit install`

### Running tests

* From `python-edtf`, run the unit tests: `pytest`
* From `python-edtf`, run `pytest -m benchmark` to run the benchmarks (published [here]( https://ixc.github.io/python-edtf/dev/bench/))
* From `python-edtf/edtf_django_tests`, run the integration tests: `python manage.py test edtf_integration`
* To run CI locally, use `act`, e.g. `act pull_request` or `act --pull=false --container-architecture linux/amd64`. Some steps may require a GitHub PAT: `act pull_request --container-architecture linux/amd64 --pull=false -s GITHUB_TOKEN=<your PAT>`

### Linting and formatting

* Check linting: `ruff check --output-format=github --config pyproject.toml`
* Check formatting: `ruff format --check --config pyproject.toml`
* Fix formatting: `ruff format --config pyproject.toml`
* Linting and formatting checks and attempted fixes are also run as precommit hooks if you installed them.

### Coverage and benchmraks

Coverage reports are generated and added as comments to commits, and also visible in the actions log. Benchmarks are run on pull requests and are published [here]( https://ixc.github.io/python-edtf/dev/bench/) and also visible in the actions log.
