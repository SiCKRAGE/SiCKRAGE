yarg(1) -- A semi hard Cornish cheese, also queries PyPI
========================================================

.. image:: https://img.shields.io/travis/kura/yarg.svg?style=flat

.. image:: https://img.shields.io/coveralls/kura/yarg.svg?style=flat

.. image:: https://pypip.in/version/yarg/badge.svg?style=flat

.. image:: https://pypip.in/download/yarg/badge.svg?style=flat

.. image:: https://pypip.in/py_versions/yarg/badge.svg?style=flat

.. image:: https://pypip.in/implementation/yarg/badge.svg?style=flat

.. image:: https://pypip.in/status/yarg/badge.svg?style=flat

.. image:: https://pypip.in/wheel/yarg/badge.svg?style=flat

.. image:: https://pypip.in/license/yarg/badge.svg?style=flat

Yarg is a PyPI client.

.. code-block:: python

    >>> import yarg
    >>> package = yarg.get("yarg")
    >>> package.name
    u'yarg'
    >>> package.author
    Author(name=u'Kura', email=u'kura@kura.io')

Full documentation is at <https://yarg.readthedocs.org>.

Yarg is released under the `MIT license
<https://github.com/kura/yarg/blob/master/LICENSE>`_. The `source code is on
GitHub <https://github.com/kura/yarg>`_ and `issues are also tracked on
GitHub <https://github.com/kura/yarg/issues>`_.


Release History
===============

0.1.8 (2014-08-10)
------------------

Splatting bugs
~~~~~~~~~~~~~~

- Integration issue with Python 3, requests, yarg and JSON. Attempt to decode
  requests response if decode attribute exists.

0.1.6 & 0.1.7 (2014-08-10)
--------------------------

Splatting bugs
~~~~~~~~~~~~~~

- Bug in setup.py causing installs to fail for sdist (source) releases.

0.1.5 (2014-08-10)
------------------

API changes
~~~~~~~~~~~

- Changed sort order of `yarg.package.Package.release_ids` to sort
  based on the upload time of the release ID.

Splatting bugs
~~~~~~~~~~~~~~

- `yarg.package.Package.latest_release_id` will now return the latest
  release ID from the PyPI info source, rather than the final list item in
  `yarg.package.Package.release_ids`.

  Addtionally `yarg.package.Package.latest_release` will do the same as
  it gets the latest release information from
  `yarg.package.Package.latest_release_id`.

0.1.4 (2014-08-09)
------------------

API changes
~~~~~~~~~~~

- New method `yarg.newest_packages` for querying new packages
  from the PyPI RSS feed.
- New method `yarg.latest_updated_packages` for querying
  the latest updated packages from the PyPI RSS feed.

Other
~~~~~

- Additional test coverage
- Additional documentation coverage

0.1.2 (2014-08-08)
------------------

Bug fixes
~~~~~~~~~

- `yarg.get` will now raise an Exception for errors **including**
  300 and above. Previously only raised for above 300.
- Fix an issue on Python 3.X and PyPy3 where
  `yarg.exceptions.HTTPError` was using a method that was
  removed in Python 3.
- Added dictionary key lookups for `home_page`, `bugtrack_url`
  and `docs_url`. Caused `KeyError` exceptions if they were not
  returned by PyPI.

Other
~~~~~

- More test coverage.

0.1.1 (2014-08-08)
------------------

API changes
~~~~~~~~~~~

- New `yarg.package.Package` property `has_wheel`.
- New `yarg.package.Package` property `has_egg`.
- New `yarg.package.Package` property `has_source`.
- New `yarg.package.Package` property `python_versions`.
- New `yarg.package.Package` property `python_implementations`.
- Added `yarg.exceptions.HTTPError` to `yarg.__init__`
  for easier access.
- Added `yarg.json2package` to `yarg.__init__` to expose it for
  use.

0.1.0 (2014-08-08)
------------------

- Initial release


