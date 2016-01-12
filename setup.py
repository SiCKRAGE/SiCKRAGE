try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
        name='sickrage',
        version='5.0.2',
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
