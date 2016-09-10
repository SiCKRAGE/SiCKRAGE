import io
import os
import shutil

from setuptools import setup, Command

# Get the version number
with io.open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'sickrage', 'version.txt'))) as f:
    version = f.read()


def requires():
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))) as f:
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
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), 'dist')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), '*.pyc')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), '*.tgz')), ignore_errors=True)
        shutil.rmtree(os.path.abspath(os.path.join(os.path.dirname(__file__), 'sickrage.egg-info')), ignore_errors=True)


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
        'clean': CleanCommand
    },
    entry_points={
        "console_scripts": [
            "sickrage=sickrage:main"
        ]
    }
)
