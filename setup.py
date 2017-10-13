import glob
import io
import os
import shutil

from babel.messages import frontend as babel
from setuptools import setup, Command

# Get the version number
with io.open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'sickrage', 'version.txt'))) as f:
    version = f.read()


def requires():
    with io.open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))) as f:
        return f.read().splitlines()


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), 'build')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), '*.pyc')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), '*.tgz')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), 'sickrage.egg-info')), ignore_errors=True)
        [os.remove(f) for f in glob.glob("dist/sickrage-*")]

setup(
    name='sickrage',
    version=version,
    description='Automatic Video Library Manager for TV Shows',
    author='echel0n',
    author_email='echel0n@sickrage.ca',
    license='GPLv3',
    url='https://git.sickrage.ca',
    keywords=['sickrage', 'sickragetv', 'tv', 'torrent', 'nzb', 'video', 'echel0n'],
    packages=['sickrage'],
    install_requires=requires(),
    include_package_data=True,
    platforms='any',
    zip_safe=False,
    test_suite='tests',
    cmdclass={
        'clean': CleanCommand,
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    },
    entry_points={
        "console_scripts": [
            "sickrage=sickrage:main"
        ]
    },
    message_extractors={
        'sickrage/core/webserver/gui/default': [
            ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'})
        ],
        'sickrage': [
            ('**.py', 'python', None)
        ],
        'dist': [
            ('**/js/*.min.js', 'ignore', None),
            ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
        ],
    }
)
