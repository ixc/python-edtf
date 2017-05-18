===========
python-edtf
===========

An implementation of EDTF format in Python.

See `http://www.loc.gov/standards/datetime/`__ for the draft specification.

To install

    pip install edtf

Includes:
=========

Level 0 ISO 8601 Features
-------------------------
* Date::

   EDTF('1979-08-28') # August 28 1979

* Interval (start/end)::

   >>> e = EDTF('1979-08-28/1979-09-25') # From August 28 to September 25 1979
   >>> e.is_interval
   True

Level 1 Extensions
------------------
* Uncertain/Approximate dates::

   EDTF('1979-08-28~') # Approximately August 28th 1979
   EDTF('1979-08-uu') # An unknown day in August 1979
   EDTF('1979-uu-28') # The 28th day of an uncertain month in 1979

* Unspecified dates::

   EDTF('1979-08') # The month of August 1979

* Years exceeding four digits::

   EDTF('y-12000') # 12000 years BCE

* Season::

   EDTF('1979-22') # Summer 1979

Level 2 Extensions
------------------
* Partial unspecified::

   EDTF('1979-uu') # Some month in 1979

* Masked precision::

   EDTF('197x') # A date in the 1970s.
   EDTF('19xx') # A date in the 1900s.


Natural language representation
-------------------------------

The ``edtf_text`` property stores the EDTF text representation of the object::

   >>> e = EDTF('1912-04-07~')
   >>> e.edtf_text
   '1912-04-07~'

Each EDTF object can optionally include a natural language equivalent, accessed
via the ``natural_text`` property::

   >>> e = EDTF(edtf_text='1912-04-07~', natural_text="Easter, 1912")
   >>> e.edtf_text
   '1912-04-07~'
   >>> e.natural_text
   'Easter, 1912'

To show a value to the public, use the ``display`` property, which returns
the ``natural_text`` value if it's defined, or else the ``edtf_text`` (not
ideal, but better than nothing until a natural text generator is included).
Calling ``unicode()`` on the object also returns the ``display`` value.

For internal purposes, both display and EDTF values can be combined into one
string, in the form ``'natural_text `edtf_text`'`` (the ``edtf_text`` value is
surrounded by backticks), and is accessed through the ``combined_text`` property.

You can initialise an EDTF object from the ``combined_text`` with
``EDTF.from_combined_text(combined_text)``.

::

   >>> e.display_text
   u'Easter, 1912'
   >>> unicode(e) # same as e.display_text
   u'Easter, 1912'
   >>> e.combined_text
   u'Easter, 1912 `1912-04-07~`'
   >>> f = EDTF.from_combined_text(e.combined_text)
   >>> f == e
   True

Parsing natural language
~~~~~~~~~~~~~~~~~~~~~~~~

The library includes a basic English natural language parser (it's not yet
smart enough to work with occasions such as 'Easter', or in other languages). If
you initialise an EDTF object with only the ``natural_text`` parameter, it will
attempt to parse into ``edtf_text``::

   >>> e = EDTF(natural_text="circa April 1912")
   >>> e.edtf_text
   u'1912-04~'
   >>> unicode(e)
   u'circa April 1912'

   >>> f = EDTF(natural_text="a long time ago") # can't be parsed
   >>> f.edtf_text
   ''
   >>> unicode(f)
   u'a long time ago'

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

Django field
============

The ``fields.EDTFField`` implements a simple Django field that stores
the ``edtf_text`` from an EDTF object.

To use the field, add ``edtf`` to your project's ``INSTALLED_APPS``.

To store a natural language value on your model, define another field, and set
the ``natural_text_field`` parameter of your ``EDTFField``::

   from django.db import models
   from edtf.fields import EDTFField

   class MyModel(models.model):
        date_display = models.CharField(
           "Date of creation (display)",
           blank=True,
           max_length=255,
        )
        date_edtf = EDTFField(
            "Date of creation (EDTF)",
            natural_text_field='date_display',
            date_earliest_field='date_earliest',
            date_latest_field='date_latest',
            sort_date_earliest_field='date_sort_ascending',
            sort_date_latest_field='date_sort_descending',
            blank=True,
            null=True,
        )
        # use for filtering
        date_earliest = models.DateField(blank=True, null=True)
        date_latest = models.DateField(blank=True, null=True)
        # use for sorting
        date_sort_ascending = models.DateField(blank=True, null=True)
        date_sort_descending = models.DateField(blank=True, null=True)


When your model is saved, the ``date_display`` value will be parsed to set
the ``date_edtf`` value, and the underlying EDTF object will set the
``_earliest`` and ``_latest`` field values.

Since the ``EDTFField`` and the ``_earliest`` and ``_latest`` field values are
set automatically, you may want to make them readonly or not visible in your
model admin.


Properties and methods
======================

There are a couple of properties that may be useful:

``precision``
-------------

Returns a string indicating how precise the date is::

            >>> EDTF('1xxx').precision
            'millenium',
            >>> EDTF('198x').precision
            'decade'
            >>> EDTF('198u').precision
            'year'

Valid values are defined in ``edtf_date.py``::

   PRECISION_MILLENIUM = "millenium"
   PRECISION_CENTURY = "century"
   PRECISION_DECADE = "decade"
   PRECISION_YEAR = "year"
   PRECISION_MONTH = "month"
   PRECISION_SEASON = "season"
   PRECISION_DAY = "day"

``is_interval``
---------------

Returns ``True`` if the EDTF date is an interval of two EDTF dates.


Converting to and from Python dates
===================================

Since EDTF dates are often regions, and often imprecise, we need to use a
few different Python dates, depending on the circumstance. Generally, Python
dates are used for sorting and filtering, not displaying directly to users.

`date_earliest` and `date_latest`
---------------------------------

These dates indicate the earliest and latest dates that are __conceivably__ in
the date range. These values are useful for filtering results - i.e. testing
which EDTF dates might conceivably fall into, or overlap, a desired date range.

For the case of approximate or uncertain dates, we arbitrarily pad the
ostensible range by 100% of the uncertain timescale. That is, if a date is
approximate at the month scale, it is padded by a month. If it is
approximate at the year scale, it is padded by a year::

   >>> e = EDTF('1912-04~')
   >>> e.date_earliest()  # padding is 50% of a month
   datetime.date(1912, 03, 16)
   >>> e.date_latest()
   datetime.date(1912, 05, 15)

   >>> e = EDTF('1912~')
   >>> e.date_earliest()  # padding is 50% of a year
   datetime.date(1911, 07, 01)
   >>> e.date_latest()
   datetime.date(1913, 06, 30)

One can interpret uncertain or approximate dates as 'plus or minus a
[level of precision]'.

If a date is both uncertain __and__ approximate, the padding is applied twice,
i.e. it gets 100% * 2 padding, or 'plus or minus two [levels of precision]'.


`sort_date_earliest` and `sort_date_latest`
-------------------------------------------

These dates indicate the earliest and latest dates that are __decidedly__ in
the date range, ignoring uncertainty or approximation. One way to think about
this is 'if you had to pick a single date to sort by, what would it be?'.

In an ascending sort (most recent last), sort by `sort_date_earliest` to get a
natural sort order. In a descending sort (most recent first), sort by
`sort_date_latest`::

   >>> e = EDTF('1912-04~')
   >>> e.sort_date_earliest()
   datetime.date(1912, 4, 01)
   >>> e.sort_date_latest()
   datetime.date(1912, 4, 30)


Long years
----------

Since EDTF covers a much greater timespan than Python ``date`` objects, it is
easy to exceed the bounds of valid Python ``date``s. In this case, the returned
dates are clamped to ``date.MIN`` and ``date.MAX``.

Seasons
-------

Seasons are interpreted as Northern Hemisphere by default. To change this,
override the month mapping in ``appsettings.py``.

Comparisons
===========

Two EDTF dates are considered equal if their ``edtf_text`` values are the same.
``natural_text`` values are ignored.

And EDTF date is considered greater than another if its ``sort_date_earliest``
value is later.


Parts of the spec still to be implemented:
==========================================

Level 0 ISO 8601 Features
-------------------------
* Times
* Interval (start/end)

Level 1 Extensions
------------------
* L1 Extended Interval

Level 2 Extensions
------------------
* partial uncertain/approximate
* one of a set
* multiple dates
* L2 extended Interval
* Year requiring more than 4 digits - Exponential form

Proposed changes
----------------
* Season qualifiers

What assumptions does the natural text parser make when interpreting an
-----------------------------------------------------------------------
ambiguous date?
---------------

* "1800s" is ambiguously a century or decade. If the given date is either
uncertain or approximate, the decade interpretation is used. If the date is
certain and precise, the century interpretation is used.

* If the century isn't specified (``EDTF(natural_text="the '70s")``), we
imply the century to be "19" if the year is greater than the current year,
otherwise we imply the century to be the current century.

* US-ordered dates (mm/dd/yyyy) are assumed by default in natural language.
To change this, set ``DAY_FIRST`` to True.

What assumptions does the library make when deriving Python ``date``s from an
-----------------------------------------------------------------------------
EDTF value?
-----------

* In date ranges where one bound is ``'unknown'``, an arbitrary amount of time is
added to get a Python date from the other bound. The amount depends on the
precision of the known date::

           if precision == PRECISION_DAY:
               return relativedelta(months=1)
           if precision == PRECISION_MONTH:
               return relativedelta(years=1)
           if precision == PRECISION_SEASON:
               return relativedelta(months=18)
           if precision == PRECISION_YEAR:
               return relativedelta(years=5)
           if precision == PRECISION_DECADE:
               return relativedelta(years=25)
           if precision == PRECISION_CENTURY:
               return relativedelta(years=250)
           if precision == PRECISION_MILLENIUM:
               return relativedelta(years=2500)

If both ends are ``'unknown'``, the equivalent Python dates are
``date.min`` and ``date.max``.

* If the date ranges where one end is ``'open'``, the equivalent Python date is
interpreted as ``date.min`` and ``date.max`` depending on whether the open date
is the start/end date.

TODO
====

Before release:
- Integrate parser work

After release:
- update requirements from gk collections

* Tests for field
* Generate the natural text
* Modify ``year/month/day`` properties to always return strings.
* Return an integer value, based on years, to sort by, so as to avoid
overflowing ``date`` values.
* Parameterise the fuzziness constant
* Convert from EDTF to natural language (using localized format specifiers)
* Localize the precision strings
* Localize the parser
* Add operators and arithmetic to EDTF objects
* Make US day/month order a setting
