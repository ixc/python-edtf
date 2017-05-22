Changelog
=========

2.0 (2017-05-22)
----------------

- Complete EDTF spec parser implemented using ``pyparsing``.
- Expanded documentation.
- Django field that stores and displays EDTF, deriving it from a specified
display field, and storing derived python dates in specified ``DateField``s.
- Settings are broken out into ``appsettings.py``. These settings can be
overridden in a Django settings file.
