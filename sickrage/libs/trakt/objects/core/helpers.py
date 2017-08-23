from __future__ import absolute_import, division, print_function


def update_attributes(obj, dictionary, keys):
    if not dictionary:
        return

    for key in keys:
        if key not in dictionary:
            continue

        value = dictionary[key]

        if getattr(obj, key) is not None and value is None:
            continue

        if type(value) is dict:
            continue

        setattr(obj, key, dictionary[key])
