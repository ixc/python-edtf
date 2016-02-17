===========
python-edtf
===========

A partial implementation of EDTF format in Python.

See <http://www.loc.gov/standards/datetime/> for the draft specification.

To install

    pip install edtf

Includes:
=========

Level 0 ISO 8601 Features
-------------------------
* Date
* Interval (start/end)

Level 1 Extensions
------------------
* Uncertain/Approximate dates
* Unspecified dates
* Year exceeding four digits
* Season

Level 2 Extensions
------------------
* Partial unspecified
* Masked precision

Also
----
* A rough and ready plain text parser
* Basic conversion to python dates for sorting and range testing

Does not include (ie still to be implemented):
==============================================

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

Usage
=====

>>> from edtf import EDTF
>>> e = EDTF('1898-uu~')  # approximately a month in 1898
>>> e.date_earliest()  # approximate dates get a bit of padding
datetime.date(1897, 12, 16)
>>> e.date_latest()
datetime.date(1899, 1, 16)
>>> e.sort_date_earliest() # defaults to be at the start of the range
datetime.date(1898, 01, 01)
>>> e.sort_date_latest() # defaults to be at the end of the range
datetime.date(1898, 12, 31)
>>> e.is_interval
False

>>> i = EDTF('1898/1903-08-30')  # between 1898 and August 30th 1903
>>> i.earliest_date()
datetime.date(1898, 1, 1)
>>> i.date_latest()
datetime.date(1903, 8, 30)
>>> i.sort_date_earliest()
datetime.date(1898, 01, 01)
>>> i.sort_date_latest()
datetime.date(1903, 08, 30)
>>> i.is_interval
True

>>> p = EDTF.from_natural_text("circa April 1912")
>>> unicode(p)
u'1912-04~'
>>> p.sort_date_earliest()
datetime.date(1912, 4, 01)
>>> p.sort_date_latest()
datetime.date(1912, 4, 30)

What is the difference between earliest_date and sort_date_earliest?
--------------------------------------------------------------------

``sort_date_earliest`` and ``sort_date_latest`` are the "if you had to pick one day what would it be" values. So for
circa dates, they're normally the first or last day in the circa'd range.

In the example above, ``EDTF.from_natural_text("circa April 1912")`` produces ``1912-04-01`` or ``1912-04-30`` depending
on whether earliest or latest. Which one you choose depends on whether you want circa dates to appear before or after
more precise results in a sorted list.

``date_earliest`` and ``date_latest`` are the earliest/latest dates an EDTF date could reasonably be. These are
intended to be used for filtering for imprecise dates that may overlap a given range (ie "show me works that might
have been made in 1818").

The meaning of 'could reasonably be' is **arbitrarily defined**. If a date is approximate *xor* uncertain, we add about
50% of the precision in each direction. So for months that are approximate, we +/- half a month to the earliest and
latest dates. E.g.

>>> i = EDTF('2004-06?')  # approx june 2004
>>> i.earliest_date()  # half a month earlier than the specified month
datetime.date(2004, 5, 16)
>>> i.date_latest()  # half a month later than the specified month
datetime.date(2004, 7, 16)

If an EDTF is both approximate *and* uncertain, we add 100% of the precision in each direction. So for months that are
both approximate and uncertain, we +/- a whole month, e.g:

>>> i = EDTF('1984?~')  # approx 1984, but uncertain
>>> i.earliest_date()  # a whole year earlier than the specified year
datetime.date(1983, 1, 1)
>>> i.date_latest()  # a whole year later than the specified year
datetime.date(1985, 12, 31)


See ``tests.py`` for more.

What assumptions does ``from_natural_text`` make when interpreting an ambiguous date?
--------------------------------------------------------//---------------------------

- We're interpreting "1800s" to be a century, and "ca. 1800s" to be a decade.
- We imply the century to be "19" if it's not given, and the year is less than the current year.

