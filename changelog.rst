Changelog
=========

In development
--------------

*Nothing yet*

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
