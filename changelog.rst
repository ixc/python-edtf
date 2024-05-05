Changelog
=========

In development
--------------


5.0.0 (2023-10-04)
------------------

* Breaking Changes: Implementation of the newer specifications from `https://www.loc.gov/standards/datetime/`::

    Differences
    This specification differs from the earlier draft as follows:

    - the unspecified date character (formerly lower case ‘u’) is superseded by the character (upper case) 'X';
    - Masked precision is eliminated;
    - the uncertain and approximate qualifiers, '?' and '~',  when applied together, are combined into a single qualifier character '%';
    - “qualification from the left” is introduced and replaces the grouping mechanism using parentheses;
    - the extended interval syntax  keywords 'unknown' and 'open' have been replaced with null and the double-dot notation ['..'] respectively;
    - the year prefix 'y' and the exponential indicator 'e', both previously lowercase, are now 'Y' and 'E' (uppercase); and
    - the significant digit indicator 'p' is now 'S' (uppercase).

* Renaming of the project to edtf2: As this project seems to have no longer support from the creator `The Interaction Consortium` we decided to fork it and release it under a new name by our own


4.0 (2018-05-31)
----------------

* Remove 1 AD - 9999 AD restriction on date ranges imposed by Python's
  ``datetime`` module (#26).

  **WARNING**: This involves a breaking API change where the following methods
  return a ``time.struct_time`` object instead of ``datetime.date`` or
  ``datetime.datetime`` objects::

      lower_strict()
      upper_strict()
      lower_fuzzy()
      upper_fuzzy()

* Add `jdutil` library code by Matt Davis at
  `https://gist.github.com/jiffyclub/1294443`_ to convert dates to numerical
  float representations.

* Update `EDTFField` to store derived upper/lower strict/fuzzy date values as
  numerical values to Django's `FloatField` fields, when available, to permit
  storage of arbitrary date/time values.

  The older approach where `DateField` fields are used instead is still
  supported but not recommended, since this usage will break for date/time
  values outside the range 1 AD to 9999 AD.


3.0 (2018-02-13)
----------------

* Python 3 compatibility.
  PR: https://github.com/ixc/python-edtf/pull/25
  Author: https://github.com/ahankinson


2.7 (2018-01-09)
----------------

* Fix lower/upper fuzzy values for outlier date values


2.6 (2017-08-07)
----------------

* EDTF fields are now cleared when their source fields go.
* Improved clarity of parser errors.
* Improved parser accuracy and resilience (#20, #22).


2.5 (2017-06-08)
----------------

*  Order-of-magnitude performance improvement in parsing.
*  EDTFFields are now serialised EDTF objects, rather than unparsed EDTF text
   strings.

2.0 (2017-05-22)
----------------

The Interaction Consortium is pleased to announce an all-new version 2.0 of
``python-edtf``.

This version features a full implementation of the EDTF grammar, meaning
all valid EDTF strings can be parsed into Python objects.

We've also included a Django EDTF field that allows EDTF dates to be used in
Django models. The field can parse natural text equivalents from another field,
and it can generate python date values to store in other fields.

Features
~~~~~~~~

*  Complete EDTF spec parser implemented using ``pyparsing``.
*  Expanded documentation.
*  Django field that stores and displays EDTF, deriving it from a specified
   display field, and storing derived python dates in specified ``DateField``s.
*  Settings are broken out into ``appsettings.py``. These settings can be
   overridden in a Django settings file.
*  Instituted changelog

Backwards-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The API is completely revised since 0.9.3, so almost all code needs
updating. In brief::

   EDTF(str) => parse_edtf(str)
   EDTF.from_natural_language(str) => parse_edtf(text_to_edtf(str))
   date_earliest() => lower_fuzzy()
   date_latest() => upper_fuzzy()
   sort_date_earliest() => lower_strict()
   sort_date_latest() => upper_strict()
