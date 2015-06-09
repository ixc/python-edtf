===========
python-edtf
===========

A partial implementation of EDTF format in Python.

See <http://www.loc.gov/standards/datetime/> for the draft specification.

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
>>> e = EDTF('1898-uu~') #approximately a month in 1898
>>> e.earliest_date()
datetime.date(1897, 12, 16)
>>> e.latest_date()
datetime.date(1899, 1, 16)
>>> e.sort_date() # defaults to be at the end of the range
datetime.date(1898, 12, 31)
>>> e.is_interval
False

>>> i = EDTF('1898/1903-08-30') # between 1898 and August 30th 1903
>>> i.earliest_date()
datetime.date(1898, 1, 1)
>>> i.latest_date()
datetime.date(1903, 8, 30)
>>> i.sort_date()
datetime.date(1898, 12, 31)
>>> i.is_interval
True

>>> p = EDTF.from_natural_text("circa April 1912")
>>> unicode(p)
u'1912-04~'
>>> p.sort_date()
datetime.date(1912, 4, 30)
