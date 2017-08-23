from __future__ import absolute_import, division, print_function

from six.moves.urllib_parse import urlencode


def setdefault(d, defaults, func=None):
    for key, value in defaults.items():
        if func and not func(key, value):
            continue

        d.setdefault(key, value)


def has_attribute(obj, name):
    try:
        object.__getattribute__(obj, name)
        return True
    except AttributeError:
        return False


def build_url(*args, **kwargs):
    parameters = [
        (key, value)
        for (key, value) in kwargs.items()
        if value
    ]

    return ''.join([
        '/'.join([str(x) for x in args]),
        ('?' + urlencode(parameters)) if parameters else ''
    ])
