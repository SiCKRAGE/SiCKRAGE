#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import codecs
import collections
import functools
import locale
import sys
import types
from itertools import imap
from os import name

import six

import sickbeard


def encodingInit():
    # map the following codecs to utf-8
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp1252' else None)

    # get locale encoding
    try:
        locale.setlocale(locale.LC_ALL, "")
        sickbeard.SYS_ENCODING = locale.getpreferredencoding()
    except (locale.Error, IOError):
        sickbeard.SYS_ENCODING = None

    # enforce UTF-8
    if not sickbeard.SYS_ENCODING or codecs.lookup(sickbeard.SYS_ENCODING).name == 'ascii':
        sickbeard.SYS_ENCODING = 'UTF-8'

    # wrap i/o in unicode
    sys.stdout = codecs.getwriter(sickbeard.SYS_ENCODING)(sys.stdout)
    sys.stdin = codecs.getreader(sickbeard.SYS_ENCODING)(sys.stdin)


def ek(f, *args, **kwargs):
    """
    Encoding Kludge: Call function with arguments and unicode-encode output

    :param function:  Function to call
    :param args:  Arguments for function
    :param kwargs:  Arguments for function
    :return: Unicode-converted function output (string, list or tuple, depends on input)
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if name == 'nt':
            result = f(*args, **kwargs)
        else:
            result = f(*[ss(x) if isinstance(x, (six.text_type, six.binary_type)) else x for x in args], **kwargs)

        def _wrapper(result, *args, **kwargs):
            try:
                if isinstance(result, six.string_types):
                    return uu(result)
                elif isinstance(result, collections.Mapping):
                    return dict(imap(_wrapper, result.items()))
                elif isinstance(result, collections.Iterable) and isinstance(result, types.GeneratorType):
                    return filter(lambda x: x is not None, imap(_wrapper, result))
                elif isinstance(result, collections.Iterable) and isinstance(result, (types.TupleType, types.ListType)):
                    return type(result)(filter(lambda x: x is not None, imap(_wrapper, result)))
            except:
                pass

            return result

        return _wrapper(result, *args, **kwargs)

    return wrapper(*args, **kwargs)


def uu(s, encoding="utf-8", errors="strict"):
    """ Convert, at all consts, 'text' to a `unicode` object.
    """

    if isinstance(s, six.text_type):
        return s

    try:
        if not isinstance(s, six.string_types):
            if six.PY3:
                if isinstance(s, six.binary_type):
                    s = six.text_type(s, encoding, errors)
                else:
                    s = six.text_type(s)
            elif hasattr(s, '__unicode__'):
                s = six.text_type(s)
            else:
                s = six.text_type(six.binary_type(s), encoding, errors)
        else:
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        pass

    return s


def ss(s, encoding="utf-8", errors="strict"):
    """ Convert 'text' to a `str` object.
    """

    if isinstance(s, six.binary_type):
        if encoding == "utf-8":
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)

    if not isinstance(s, six.string_types):
        try:
            if six.PY3:
                return six.text_type(s).encode(encoding)
            else:
                return six.binary_type(s)
        except UnicodeEncodeError:
            return six.text_type(s).encode(encoding, errors)
    else:
        return s.encode(encoding, errors)
