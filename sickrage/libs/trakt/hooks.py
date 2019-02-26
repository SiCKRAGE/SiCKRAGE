from __future__ import absolute_import, division, print_function

import os

PACKAGE_DIR = os.path.dirname(__file__)


def write_version(command):
    if not command or not hasattr(command, 'egg_version'):
        print('Invalid command state')
        return

    # Retrieve current package version
    version = command.egg_version

    if not version:
        print('No version available')
        return

    # Ensure "version.py" exists
    version_path = os.path.join(PACKAGE_DIR, 'version.py')

    if not os.path.exists(version_path):
        print('Unable to find version module')
        return

    # Read version module
    try:
        with open(version_path, 'r') as fp:
            contents = fp.read()
    except Exception as ex:
        print('Unable to read version module: %s' % (ex,))
        return

    if not contents:
        print('Unable to read version module: no lines returned')
        return

    lines = contents.split('\n')

    # Update version attribute
    for x in range(len(lines)):
        line = lines[x]

        if line.startswith('__version__ ='):
            lines[x] = '__version__ = %r' % (version,)

    # Write version module
    try:
        with open(version_path, 'w') as fp:
            fp.write('\n'.join(lines))
    except Exception as ex:
        print('Unable to write version module: %s' % (ex,))

    print('Updated version module to: %s' % (version,))
