GuessIt
=======

.. image:: http://img.shields.io/pypi/v/guessit.svg
    :target: https://pypi.python.org/pypi/guessit
    :alt: Latest Version

.. image:: http://img.shields.io/badge/license-LGPLv3-blue.svg
    :target: https://pypi.python.org/pypi/guessit
    :alt: License

.. image:: http://img.shields.io/travis/guessit-io/guessit/1.x.svg
    :target: https://travis-ci.org/guessit-io/guessit
    :alt: Build Status

.. image:: http://img.shields.io/coveralls/guessit-io/guessit/1.x.svg
    :target: https://coveralls.io/github/guessit-io/guessit?branch=1.x
    :alt: Coveralls

.. image:: https://img.shields.io/badge/Hu-Board-7965cc.svg
    :target: https://huboard.com/guessit-io/guessit
    :alt: HuBoard

`HuBoard <https://huboard.com/guessit-io/guessit>`_


GuessIt is a python library that extracts as much information as
possible from a video filenames.

It has a very powerful matcher that allows to guess a lot of
metadata from a video using its filename only. This matcher works with
both movies and tv shows episodes.

For example, GuessIt can do the following::

    $ guessit "Treme.1x03.Right.Place,.Wrong.Time.HDTV.XviD-NoTV.avi"
    For: Treme.1x03.Right.Place,.Wrong.Time.HDTV.XviD-NoTV.avi
    GuessIt found: {
        [1.00] "mimetype": "video/x-msvideo",
        [0.80] "episodeNumber": 3,
        [0.80] "videoCodec": "XviD",
        [1.00] "container": "avi",
        [1.00] "format": "HDTV",
        [0.70] "series": "Treme",
        [0.50] "title": "Right Place, Wrong Time",
        [0.80] "releaseGroup": "NoTV",
        [0.80] "season": 1,
        [1.00] "type": "episode"
    }

Important note
--------------
GuessIt 2 has been rewriten from scratch and is currently in Alpha. GuessIt is now a release name parser only, and
support for additional features like hashes computations has been dropped.

To migrate from guessit ``0.x`` or ``1.x``, please read
`MIGRATION.rst <https://github.com/guessit-io/guessit/blob/master/MIGRATION.rst>`_.

Previous version of GuessIt is still available in ``1.x`` branch and using ``pip install guessit<2``, but won't be
maintained anymore.


Install
-------

Installing GuessIt is simple with `pip <http://www.pip-installer.org/>`_::

    $ pip install "guessit<2"

You can now launch a demo::

    $ guessit -d

and guess your own filename::

    $ guessit "Breaking.Bad.S05E08.720p.MP4.BDRip.[KoTuWa].mkv"
    For: Breaking.Bad.S05E08.720p.MP4.BDRip.[KoTuWa].mkv
    GuessIt found: {
        [1.00] "mimetype": "video/x-matroska",
        [1.00] "episodeNumber": 8,
        [0.30] "container": "mkv",
        [1.00] "format": "BluRay",
        [0.70] "series": "Breaking Bad",
        [1.00] "releaseGroup": "KoTuWa",
        [1.00] "screenSize": "720p",
        [1.00] "season": 5,
        [1.00] "type": "episode"
    }



Filename matcher
----------------

The filename matcher is based on pattern matching and is able to recognize many properties from the filename,
like ``title``, ``year``, ``series``, ``episodeNumber``, ``seasonNumber``,
``videoCodec``, ``screenSize``, ``language``. Guessed values are cleaned up and given in a readable format
which may not match exactly the raw filename.

The full list of available properties can be seen in the
`main documentation <http://guessit.readthedocs.org/en/latest/user/properties.html>`_.


Other features
--------------

GuessIt also allows you to compute a whole lot of hashes from a file,
namely all the ones you can find in the hashlib python module (md5,
sha1, ...), but also the Media Player Classic hash that is used (amongst
others) by OpenSubtitles and SMPlayer, as well as the ed2k hash.

If you have the 'guess-language' python package installed, GuessIt can also
analyze a subtitle file's contents and detect which language it is written in.

If you have the 'enzyme' python package installed, GuessIt can also detect the
properties from the actual video file metadata.


Usage
-----

guessit can be use from command line::

    $ guessit
    usage: guessit [-h] [-t TYPE] [-n] [-c] [-X DISABLED_TRANSFORMERS] [-v]
                   [-P SHOW_PROPERTY] [-u] [-a] [-y] [-f INPUT_FILE] [-d] [-p]
                   [-V] [-s] [--version] [-b] [-i INFO] [-S EXPECTED_SERIES]
                   [-T EXPECTED_TITLE] [-Y] [-D] [-L ALLOWED_LANGUAGES] [-E]
                   [-C ALLOWED_COUNTRIES] [-G EXPECTED_GROUP]
                   [filename [filename ...]]

    positional arguments:
      filename              Filename or release name to guess

    optional arguments:
      -h, --help            show this help message and exit

    Naming:
      -t TYPE, --type TYPE  The suggested file type: movie, episode. If undefined,
                            type will be guessed.
      -n, --name-only       Parse files as name only. Disable folder parsing,
                            extension parsing, and file content analysis.
      -c, --split-camel     Split camel case part of filename.
      -X DISABLED_TRANSFORMERS, --disabled-transformer DISABLED_TRANSFORMERS
                            Transformer to disable (can be used multiple time)
      -S EXPECTED_SERIES, --expected-series EXPECTED_SERIES
                            Expected series to parse (can be used multiple times)
      -T EXPECTED_TITLE, --expected-title EXPECTED_TITLE
                            Expected title (can be used multiple times)
      -Y, --date-year-first
                            If short date is found, consider the first digits as
                            the year.
      -D, --date-day-first  If short date is found, consider the second digits as
                            the day.
      -L ALLOWED_LANGUAGES, --allowed-languages ALLOWED_LANGUAGES
                            Allowed language (can be used multiple times)
      -E, --episode-prefer-number
                            Guess "serie.213.avi" as the episodeNumber 213.
                            Without this option, it will be guessed as season 2,
                            episodeNumber 13
      -C ALLOWED_COUNTRIES, --allowed-country ALLOWED_COUNTRIES
                            Allowed country (can be used multiple times)
      -G EXPECTED_GROUP, --expected-group EXPECTED_GROUP
                            Expected release group (can be used multiple times)

    Output:
      -v, --verbose         Display debug output
      -P SHOW_PROPERTY, --show-property SHOW_PROPERTY
                            Display the value of a single property (title, series,
                            videoCodec, year, type ...)
      -u, --unidentified    Display the unidentified parts.
      -a, --advanced        Display advanced information for filename guesses, as
                            json output
      -y, --yaml            Display information for filename guesses as yaml
                            output (like unit-test)
      -f INPUT_FILE, --input-file INPUT_FILE
                            Read filenames from an input file.
      -d, --demo            Run a few builtin tests instead of analyzing a file

    Information:
      -p, --properties      Display properties that can be guessed.
      -V, --values          Display property values that can be guessed.
      -s, --transformers    Display transformers that can be used.
      --version             Display the guessit version.

    guessit.io:
      -b, --bug             Submit a wrong detection to the guessit.io service

    Other features:
      -i INFO, --info INFO  The desired information type: filename, video,
                            hash_mpc or a hash from python's hashlib module, such
                            as hash_md5, hash_sha1, ...; or a list of any of them,
                            comma-separated


It can also be used as a python module::

    >>> from guessit import guess_file_info
    >>> guess_file_info('Treme.1x03.Right.Place,.Wrong.Time.HDTV.XviD-NoTV.avi')
    {u'mimetype': 'video/x-msvideo', u'episodeNumber': 3, u'videoCodec': u'XviD', u'container': u'avi', u'format':     u'HDTV', u'series': u'Treme', u'title': u'Right Place, Wrong Time', u'releaseGroup': u'NoTV', u'season': 1, u'type': u'episode'}


Support
-------

The project website for GuessIt is hosted at `ReadTheDocs <http://guessit.readthedocs.org/>`_.
There you will also find the User guide and Developer documentation.

This project is hosted on GitHub: `<https://github.com/guessit-io/guessit>`_

Please report issues and/or feature requests via the `bug tracker <https://github.com/guessit-io/guessit/issues>`_.

You can also report issues using the command-line tool::

    $ guessit --bug "filename.that.fails.avi"


Contribute
----------

GuessIt is under active development, and contributions are more than welcome!

#. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
   There is a Contributor Friendly tag for issues that should be ideal for people who are not very
   familiar with the codebase yet.
#. Fork `the repository`_ on Github to start making your changes to the **1.x**
   branch (or branch off of it).
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published. :)

.. _the repository: https://github.com/guessit-io/guessit

License
-------

GuessIt is licensed under the `LGPLv3 license <http://www.gnu.org/licenses/lgpl.html>`_.


History
=======

1.0.3 (2016-01-31)
------------------
* Fix issue causing a crash with some releaseGroup match (ValueError: ... is not in list).

1.0.2 (2015-11-05)
------------------
* Latest stable version from guessit ``1.x``, consider upgrading to ``2.x``
* Fix RST syntax errors for pypi readme display
* Fix issue in subtitle suffix

0.11.0 (2015-09-04)
-------------------

* Fixed year-season episodes with 'x' separator
* Fixed name guessing when a subdirectory contains a number
* Fixed possible IndexError in release_group plugin
* Fixed infinite recursion when multiple languages from same node are ignored in the second pass
* Added skip of language guess for 2-3 letters directories
* Added exclusion of common words from title guessing
* Added a higher confidence on filename over directories


0.10.4 (2015-08-19)
-------------------
* Added ``LD``/``MD`` properties
* Added better support for ``episodeList``
* Added more rules for filetype autodetection
* Added support for ``episodeList`` on weak episode patterns
* Added ``partList`` property (list for ``part`` property)
* Added vob to supported file extensions
* Added more ignore words to language detection
* Added string options support for API methods (will be parsed like command-line)
* Added better subtitle detection (prefix priority over suffix)
* Fixed ``version`` property no detected when detached from ``episodeNumber``
* Fixed ``releaseGroup`` property no detected when prefixed by ``screenSize``
* Fixed single digit detected as an ``episodeNumber``
* Fixed an internal issue in matcher causing absolute and relative group spans confusion
* Fixed an internal issue in properties container causing invalid ordering of found patterns
* Fixed raw value for some properties (--advanced)
* Use pytest as test runner
* Remove support for python 2.6


0.10.3 (2015-04-04)
-------------------

* Fix issues related to unicode encoding/decoding
* Fix possible crashes in guess_video_rexps
* Fix invalid guess result when crc32 contains 6 digits than can be parsed as a date


0.10.2 (2015-03-08)
-------------------

* Use common words to resolve conflicts on strings
* Bump babelfish version
* Fix setuptools deprecation warning
* Package argparse dependency only if python<2.7


0.10.1 (2015-01-05)
-------------------

* Avoid word Stay to be recognized as AY subtitle
* Fixed exception when no unidentified leaves remains
* Avoid usage of deprecated EntryPoint.load() require argument
* Fixed invalid raw data for some properties (title, series and maybe others)


0.10.0 (2014-12-27)
-------------------
* Fixed exception when serie title starts with Ep
* Fixed exception when trying to parse a full length country name
* Removed deprecated optparse module, replaced by argparse


0.9.4 (2014-11-10)
------------------

* Fixed exception when filename contains multiple languages ISO codes
* Fixed transformers initialization logging
* Fixed possible exception in language transformer
* Added more words to common english words


0.9.3 (2014-09-14)
------------------

* Added ``Preair`` and ``Remux`` to ``other`` property
* Better detection of ``audioProfile`` = ``HD`` / ``HDMA`` for ``audioCodec`` = ``DTS``
* Better detection of ``format``` = ``BluRay`` (when followed by Rip)
* Recognize ``RC`` as ``R5``
* Recognize ``WEB-HD```and ``ẀEB`` as ``WEB-DL``


0.9.2 (2014-09-13)
------------------

* Added support of option registration on transformers
* Better detection of ``releaseGroup`` when using ``expected-series`` or ``expected-title`` option
* Better ``audioChannel`` = ``5.1`` / ``7.1`` guessing (``6ch``, ``8ch``)
* Fixed usage not showing when invalid options were passed
* Added ``PAL``, ``SECAM`` and ``NTSC`` to ``other`` possible values
* Recognize DVD-9 and DVD-5 as ``format`` = ``DVD`` property


0.9.1 (2014-09-06)
------------------

* Added ``--unidentified`` option to display unidentified parts of the filename
  This option affects command line only - From API `unidentified` properties will
  always be grabbed regardless this settings
* Better guessing of ``releaseGroup`` property
* Added ``mHD`` and ``HDLight`` to ``other properties``
* Better guessing of ``format`` = ``DVD`` property (DVD-R pattern)
* Some ``info`` logs changed to ``debug`` for quiet integration
* Small fixes


0.9.0 (2014-09-05)
------------------

* Better auto-detection of anime episodes, containing a ``crc32`` or a digits ``episodeNumber``.
* Better listing of options on ``guessit -h``
* Added ``--allowed-countries`` and ``--allowed-languages`` to avoid two or three
  letters words to be guessed as ``country`` or ``language``
* Added ``--disabled-transformers`` option to disable transformer plugin at runtime.
* Added ``--episode-prefer-number`` option, for ``guess -t episode 'serie.123.avi'``
  to return ``episodeNumber`` = ``123`` instead of ``season`` = ``1`` + ``episodeNumber`` = 23``
* Added ``--split-camel`` option (now disabled by default)
* Added ``episodeCount`` and ``seasonCount`` properties (x-of-n notation)
* Added ``--date-year-first``` and ``--date-day-first`` options
* Added ``--expected-title``, ``--expected-series`` and ``--expected-groups``
  to help finding values when those properties are known
* Added ``10bit`` value to ``videoProfile``
* Added ``--show-property`` option to only show a single property
* Added ``--input-file`` option to parse a list of
* Added ``--version`` option
* Added ``ass`` to subtitle extensions
* Added ``Fansub`` value for ``other`` property
* Added more date formats support with ``dateutil`` dependency
* Added customizable ``clean_function`` (API)
* Added ``default_options`` (API)
* Fixed ``--yaml`` option to support ``language`` and ``country``
* Fixed ``transformers.add_transformer()`` function (API)


0.8 (2014-07-06)
----------------

* New webservice that allows to use GuessIt just by sending a POST request to
  the http://guessit.io/guess url
* Command-line util can now report bugs to the http://guessit.io/bugs service
  by specifying the ``-b`` or ``--bug`` flag
* GuessIt can now use the Enzyme python package to detect metadata out of the
  actual video file metadata instead of the filename
* Finished transition to ``babelfish.Language`` and ``babelfish.Country``
* New property: ``duration`` which returns the duration of the video in seconds
  This requires the Enzyme package to work
* New property: ``fileSize`` which returns the size of the file in bytes
* Renamed property ``special`` to ``episodeDetails``
* Added support for Python 3.4
* Optimization and bugfixes


0.7.1 (2014-03-03)
------------------

* New property "special": values can be trailer, pilot, unaired
* New options for the guessit cmdline util: ``-y``, ``--yaml`` outputs the
  result in yaml format and ``-n``, ``--name-only`` analyzes the input as simple
  text (instead of filename)
* Added properties formatters and validators
* Removed support for python 3.2
* A healthy amount of code cleanup/refactoring and fixes :)


0.7 (2014-01-29)
----------------

* New plugin API that allows to register custom patterns / transformers
* Uses Babelfish for language and country detection
* Added Quality API to rate file quality from guessed property values
* Better and more accurate overall detection
* Added roman and word numeral detection
* Added 'videoProfile' and 'audioProfile' property
* Moved boolean properties to 'other' property value ('is3D' became 'other' = '3D')
* Added more possible values for various properties.
* Added command line option to list available properties and values
* Fixes for Python3 support


0.6.2 (2013-11-08)
------------------

* Added support for nfo files
* GuessIt can now output advanced information as json ('-a' on the command line)
* Better language detection
* Added new property: 'is3D'


0.6.1 (2013-09-18)
------------------

* New property "idNumber" that tries to identify a hash value or a
  serial number
* The usual bugfixes


0.6 (2013-07-16)
----------------

* Better packaging: unittests and doc included in source tarball
* Fixes everywhere: unicode, release group detection, language detection, ...
* A few speed optimizations


0.5.4 (2013-02-11)
------------------

* guessit can be installed as a system wide script (thanks @dplarson)
* Enhanced logging facilities
* Fixes for episode number and country detection


0.5.3 (2012-11-01)
------------------

* GuessIt can now optionally act as a wrapper around the 'guess-language' python
  module, and thus provide detection of the natural language in which a body of
  text is written

* Lots of fixes everywhere, mostly for properties and release group detection


0.5.2 (2012-10-02)
------------------

* Much improved auto-detection of filetype
* Fixed some issues with the detection of release groups


0.5.1 (2012-09-23)
------------------

* now detects 'country' property; also detect 'year' property for series
* more patterns and bugfixes


0.5 (2012-07-29)
----------------

* Python3 compatibility
* the usual assortment of bugfixes


0.4.2 (2012-05-19)
------------------

* added Language.tmdb language code property for TheMovieDB
* added ability to recognize list of episodes
* bugfixes for Language.__nonzero__ and episode regexps


0.4.1 (2012-05-12)
------------------

* bugfixes for unicode, paths on Windows, autodetection, and language issues


0.4 (2012-04-28)
----------------

* much improved language detection, now also detect language variants
* supports more video filetypes (thanks to Rob McMullen)


0.3.1 (2012-03-15)
------------------

* fixed package installation from PyPI
* better imports for the transformations (thanks Diaoul!)
* some small language fixes

0.3 (2012-03-12)
----------------

* fix to recognize 1080p format (thanks to Jonathan Lauwers)

0.3b2 (2012-03-02)
------------------

* fixed the package installation

0.3b1 (2012-03-01)
------------------

* refactored quite a bit, code is much cleaner now
* fixed quite a few tests
* re-vamped the documentation, wrote some more

0.2 (2011-05-27)
----------------

* new parser/matcher completely replaced the old one
* quite a few more unittests and fixes


0.2b1 (2011-05-20)
------------------

* brand new parser/matcher that is much more flexible and powerful
* lots of cleaning and a bunch of unittests


0.1 (2011-05-10)
----------------

* fixed a few minor issues & heuristics


0.1b2 (2011-03-12)
------------------

* Added PyPI trove classifiers
* fixed version number in setup.py


0.1b1 (2011-03-12)
------------------

* first pre-release version; imported from Smewt with a few enhancements already
  in there.


