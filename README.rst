===========
python-edtf
===========

An implementation of EDTF format in Python, together with utility functions
for parsing natural language date texts, and converting EDTF dates to related
Python ``date`` objects.

See `<http://www.loc.gov/standards/datetime/>`_ for the current draft
specification.

.. contents:: :depth: 2

Quickstart
==========

To install
----------

::

    pip install edtf

To use
------

::

   >>> from edtf import parse_edtf
   # Parse an EDTF string to an EDTFObject
   >>> e = parse_edtf("1979-08~") # approx August 1979
   >>> e
   UncertainOrApproximate: '1979-08~'
   # normalised string representation (some different EDTF strings have identical meanings)
   >>> unicode(e)
   u'1979-08~'

   # Derive Python date objects
   # lower and upper bounds that strictly adhere to the given range
   >>> e.lower_strict(), e.upper_strict()
   (datetime.date(1979, 8, 1), datetime.date(1979, 8, 31))
   # lower and upper bounds that are padded if there's indicated uncertainty
   >>> e.lower_fuzzy(), e.upper_fuzzy()
   (datetime.date(1979, 7, 1), datetime.date(1979, 9, 30))

   # Date intervals
   >>> interval = parse_edtf("1979-08~/open")
   >>> interval
   Level1Interval: '1979-08~/open'
   # Intervals have lower and upper EDTF objects.
   >>> interval.lower, interval.upper
   (UncertainOrApproximate: '1979-08~', UncertainOrApproximate: 'open')
   >>> interval.lower.upper_strict()
   datetime.date(1979, 8, 31)
   >>> interval.upper.lower_strict() #'open' is interpreted to mean 'still happening'.
   [Today's date]

   # Date collections
   >>> coll = parse_edtf('{1667,1668, 1670..1672}')
   >>> coll
   MultipleDates: '{1667, 1668, 1670..1672}'
   >>> coll.objects
   (Date: '1667', Date: '1668', Consecutives: '1670..1672')

The object returned by ``parse_edtf()`` is an instance of an
``edtf.parser.parser_classes.EDTFObject`` subclass, depending on the type
of date that was parsed. These classes are::

   # Level 0
   Date
   DateAndTime
   Interval

   # Level 1
   UncertainOrApproximate
   Unspecified
   Level1Interval
   LongYear
   Season

   # Level 2
   PartialUncertainOrApproximate
   PartialUnspecified
   OneOfASet
   MultipleDates
   MaskedPrecision
   Level2Interval
   ExponentialYear


All of these implement ``upper/lower_strict/fuzzy()``
methods to derive Python ``date`` objects.

The ``*Interval`` instances have ``upper`` and ``lower`` properties that
are themselves ``EDTFObject`` instances.

``OneOfASet`` and ``MultipleDates`` instances have an ``objects`` property that
is a list of all of the EDTF dates parsed in the set or list.

EDTF Specification Inclusions
=============================

The library includes implementation of levels 0, 1 and 2 of the EDTF spec.

Test coverage includes every example given in the spec table of features.

Level 0 ISO 8601 Features
-------------------------
* Date::

   >>> parse_edtf('1979-08') # August 1979
   Date: '1979-08'

* Date and Time::

   >>> parse_edtf('2004-01-01T10:10:10+05:00')
   DateAndTime: '2004-01-01T10:10:10+05:00'

* Interval (start/end)::

   >>> parse_edtf('1979-08-28/1979-09-25') # From August 28 to September 25 1979
   Interval: '1979-08-28/1979-09-25'

Level 1 Extensions
------------------
* Uncertain/Approximate dates::

   >>> parse_edtf('1979-08-28~') # Approximately August 28th 1979
   UncertainOrApproximate: '1979-08-28~'

* Unspecified dates::

   >>> parse_edtf('1979-08-uu') # An unknown day in August 1979
   Unspecified: '1979-08-uu'
   >>> parse_edtf('1979-uu') # Some month in 1979
   Unspecified: '1979-uu'

* Extended intervals::

   >>> parse_edtf('1984-06-02?/2004-08-08~')
   Level1Interval: '1984-06-02?/2004-08-08~'

* Years exceeding four digits::

   >>> parse_edtf('y-12000') # 12000 years BCE
   LongYear: 'y-12000'

* Season::

   >>> parse_edtf('1979-22') # Summer 1979
   Season: '1979-22'

Level 2 Extensions
------------------
* Partial uncertain/approximate::

   >>> parse_edtf('(2011)-06-04~') # year certain, month/day approximate.
   # Note that the result text is normalized
   PartialUncertainOrApproximate: '2011-(06-04)~'

* Partial unspecified::

   >>> parse_edtf('1979-uu-28') # The 28th day of an uncertain month in 1979
   PartialUnspecified: '1979-uu-28'

* One of a set::

   >>> parse_edtf("[..1760-12-03,1762]")
   OneOfASet: '[..1760-12-03, 1762]'

* Multiple dates::

   >>> parse_edtf('{1667,1668, 1670..1672}')
   MultipleDates: '{1667, 1668, 1670..1672}'

* Masked precision::

   >>> parse_edtf('197x') # A date in the 1970s.
   MaskedPrecision: '197x'

* Level 2 Extended intervals::

   >>> parse_edtf('2004-06-(01)~/2004-06-(20)~')
   Level2Interval: '2004-06-(01)~/2004-06-(20)~'

* Year requiring more than 4 digits - exponential form::

   >>> parse_edtf('y-17e7')
   ExponentialYear: 'y-17e7'

Natural language representation
-------------------------------

The library includes a basic English natural language parser (it's not yet
smart enough to work with occasions such as 'Easter', or in other languages)::

   >>> from edtf import text_to_edtf
   >>> text_to_edtf("circa August 1979")
   '1979-08~'

Note that the result is a string, not an ``ETDFObject``.

The parser can parse strings such as::

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

   # masked precision
   '1860s' => '186x' #186x has decade precision, 186u has year precision.
   '1800s' => '18xx' # without uncertainty indicators, assume century

   # masked precision + uncertainty
   'ca. 1860s' => '186x~'
   'circa 1840s' => '184x~'
   'ca. 1860s?' => '186x?~'
   'c1800s?' => '180x?~' # with uncertainty indicators, use the decade

   # unspecified parts
   'January 12' => 'uuuu-01-12'
   'January' => 'uuuu-01'
   '7/2008' => '2008-07'

   #seasons
   'Autumn 1872' => '1872-23'
   'Fall 1872' => '1872-23'

   # before/after
   'earlier than 1928' => 'unknown/1928'
   'later than 1928' => '1928/unknown'
   'before January 1928' => 'unknown/1928-01'
   'after about the 1920s' => '192x~/unknown'

   # unspecified
   'year in the 1860s' => '186u' #186x has decade precision, 186u has year precision.
   ('year in the 1800s', '18xu')
   'month in 1872' => '1872-uu'
   'day in January 1872' => '1872-01-uu'
   'day in 1872' => '1872-uu-uu'

   #centuries
   '1st century' => '00xx'
   '10c' => '09xx'
   '19th century?' => '18xx?'

   # just showing off now...
   'a day in about Spring 1849?' => '1849-21-uu?~'

   # simple ranges, which aren't as accurate as they could be. The parser is
   limited to only picking the first year range it finds.
   '1851-1852' => '1851/1852'
   '1851-1852; printed 1853-1854' => '1851/1852'
   '1851-52' => '1851/1852'
   '1856-ca. 1865' => '1856/1865~'
   '1860s-1870s' => '186x/187x'
   '1920s -early 1930s' => '192x/193x'
   '1938, printed 1940s-1950s' => '1938'


Generating natural text from an EDTF representation is a future goal.

What assumptions does the natural text parser make when interpreting an ambiguous date?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* "1800s" is ambiguously a century or decade. If the given date is either
uncertain or approximate, the decade interpretation is used. If the date is
certain and precise, the century interpretation is used.

* If the century isn't specified (``EDTF(natural_text="the '70s")``), we
imply the century to be "19" if the year is greater than the current year,
otherwise we imply the century to be the current century.

* US-ordered dates (mm/dd/yyyy) are assumed by default in natural language.
To change this, set ``DAY_FIRST`` to True in settings.

* If a natural language groups dates with a '/', it's interpreted as "or"
rather than "and". The resulting EDTF text is a list bracketed by ``[]`` ("one
of these dates") rather than ``{}`` (all of these dates).


Converting to and from Python dates
===================================

Since EDTF dates are often regions, and often imprecise, we need to use a
few different Python dates, depending on the circumstance. Generally, Python
dates are used for sorting and filtering, and are not displayed directly to
users.

``lower_strict`` and ``upper_strict``
-------------------------------------

These dates indicate the earliest and latest dates that are __strictly__ in
the date range, ignoring uncertainty or approximation. One way to think about
this is 'if you had to pick a single date to sort by, what would it be?'.

In an ascending sort (most recent last), sort by ``lower_strict`` to get a
natural sort order. In a descending sort (most recent first), sort by
``upper_strict``::

   >>> e = parse_edtf('1912-04~')
   >>> e.lower_strict()
   datetime.date(1912, 4, 01)
   >>> e.upper_strict()
   datetime.date(1912, 4, 30)

``lower_fuzzy`` and ``upper_fuzzy``
-----------------------------------

These dates indicate the earliest and latest dates that are __possible__ in
the date range, for a fairly arbitrary definition of 'possibly'.

These values are useful for filtering results - i.e. testing
which EDTF dates might conceivably fall into, or overlap, a desired date range.

The fuzzy dates are derived from the strict dates, plus or minus a level of
padding that depends on how precise the date specfication is. For the case of
approximate or uncertain dates, we (arbitrarily) pad the ostensible range by
100% of the uncertain timescale, or by a 12 weeks in the case of seasons. That
is, if a date is approximate at the month scale, it is padded by a month. If
it is approximate at the year scale, it is padded by a year::

   >>> e = parse_edtf('1912-04~')
   >>> e.lower_fuzzy()  # padding is 100% of a month
   datetime.date(1912, 3, 1)
   >>> e.upper_fuzzy()
   datetime.date(1912, 5, 30)

   >>> e = parse_edtf('1912~')
   >>> e.lower_fuzzy()  # padding is 100% of a year
   datetime.date(1911, 1, 1)
   >>> e.upper_fuzzy()
   datetime.date(1913, 12, 31)

One can interpret uncertain or approximate dates as 'plus or minus a
[level of precision]'.

If a date is both uncertain __and__ approximate, the padding is applied twice,
i.e. it gets 100% * 2 padding, or 'plus or minus two [levels of precision]'.

Long years
----------

Since EDTF covers a much greater timespan than Python ``date`` objects, it is
easy to exceed the bounds of valid Python ``date``s. In this case, the returned
dates are clamped to ``date.MIN`` and ``date.MAX``.

Future revisions will include numerical interpretations of dates for better
sortability.

Seasons
-------

Seasons are interpreted as Northern Hemisphere by default. To change this,
override the month mapping in ``appsettings.py``.

Comparisons
===========

Two EDTF dates are considered equal if their unicode() representations are the
same. An EDTF date is considered greater than another if its ``lower_strict``
value is later.

Django ORM field
================

The ``edtf.fields.EDTFField`` implements a simple Django field that stores
an EDTF object in the database.

To store a natural language value on your model, define another field, and set
the ``natural_text_field`` parameter of your ``EDTFField``.

When your model is saved, the ``natural_text_field`` value will be parsed to set
the ``date_edtf`` value, and the underlying EDTF object will set the
``_earliest`` and ``_latest`` fields on the model.

::

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
        date_earliest = models.DateField(blank=True, null=True)
        date_latest = models.DateField(blank=True, null=True)
        # use for sorting
        date_sort_ascending = models.DateField(blank=True, null=True)
        date_sort_descending = models.DateField(blank=True, null=True)


Since the ``EDTFField`` and the ``_earliest`` and ``_latest`` field values are
set automatically, you may want to make them readonly, or not visible in your
model admin.
