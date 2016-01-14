from sys import path

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

# Get the version number
with open(path.join(path.abspath(path.dirname(__file__)), 'version.txt')) as f:
    version = f.read()

setup(
        name='sickrage',
        version=version,
        description='Automatic Video Library Manager for TV Shows',
        author='echel0n',
        author_email='sickrage.tv@gmail.com',
        url='https://github.com/SiCKRAGETV/SickRage',
        keywords=['sickrage', 'sickragetv', 'sickrage', 'tv', 'torrent', 'nzb'],

        py_modules=["sickrage"],

        packages=['sickrage',
                  'sickrage.sickrage',
                  'sickrage.gui',
                  'sickrage.contrib',
                  'sickrage.runscripts',
                  'sickrage.tests'],

        package_dir={'sickrage': '.',
                     'sickrage.sickrage': 'sickrage',
                     'sickrage.gui': 'gui',
                     'sickrage.contrib': 'contrib',
                     'sickrage.runscripts': 'runscripts',
                     'sickrage.tests': 'tests',
                     },

        zip_safe=False,
        include_package_data=True,
        test_suite='tests',
        entry_points={
            "console_scripts": [
                "sickrage=sickrage:main",
            ]
        },
)
