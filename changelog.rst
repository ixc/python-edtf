Changelog
=========

In progress (2017-05-15)
------------------------

- Greatly expanded documentation.
- Improved string methods.
- EDTF dates can be compared.
- EDTF object now stores both edtf_text and natural_text, if given.
- Django field that stores and displays EDTF, deriving it from a specified
display field, and storing derived python dates in specified ``DateField``s.
- Settings are broken out into ``appsettings.py``. These settings can be
overridden in a Django settings file.

Backwards-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``edtf_exceptions.ParseError`` is renamed ``exceptions.EDTFParseError``.
- The ``EDTF.parse_natural_text(foo)`` factory has been replaced with the
``EDTF(natural_text=foo)`` constructor.

