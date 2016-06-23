==================================================
Send2Trash -- Send files to trash on all platforms
==================================================

Send2Trash is a small package that sends files to the Trash (or Recycle Bin) *natively* and on
*all platforms*. On OS X, it uses native ``FSMoveObjectToTrashSync`` Cocoa calls, on Windows, it
uses native (and ugly) ``SHFileOperation`` win32 calls. On other platforms, if `PyGObject`_ and
`GIO`_ are available, it will use this.  Otherwise, it will fallback to its own implementation
of the `trash specifications from freedesktop.org`_.

``ctypes`` is used to access native libraries, so no compilation is necessary.

Send2Trash supports Python 2.7 and up (Python 3 is supported).

Installation
------------

You can download it with pip::

    pip install Send2Trash

or you can download the source from http://github.com/hsoft/send2trash and install it with::

    >>> python setup.py install

Usage
-----

>>> from send2trash import send2trash
>>> send2trash('some_file')

When there's a problem ``OSError`` is raised.

.. _PyGObject: https://wiki.gnome.org/PyGObject
.. _GIO: https://developer.gnome.org/gio/
.. _trash specifications from freedesktop.org: http://freedesktop.org/wiki/Specifications/trash-spec/


Changes
=======

Version 1.3.0 -- 2013/07/19
---------------------------

* Added support for Gnome's GIO.
* Merged Python 3 and Python 2 vesion in a single codebase.

Version 1.2.0 -- 2011/03/16
---------------------------

* Improved ``plat_other`` to follow freedesktop.org trash specification.

Version 1.1.0 -- 2010/10/18
---------------------------

* Converted compiled modules to ctypes so that cross-platform compilation isn't necessary anymore.

Version 1.0.2 -- 2010/07/10
---------------------------

* Fixed bugs with external volumes in plat_other.

Version 1.0.1 -- 2010/04/19
---------------------------

* Fixed memory leak in OS X module.

Version 1.0.0 -- 2010/04/07
---------------------------

* Initial Release

