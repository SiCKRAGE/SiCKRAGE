import os
import shutil
import sys

from setuptools import setup, Command

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload clean')
    sys.exit()

# Get the version number
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sickrage', 'version.txt')) as f:
    version = f.read()


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'build'), ignore_errors=True)
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dist'), ignore_errors=True)
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), '*.pyc'), ignore_errors=True)
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), '*.tgz'), ignore_errors=True)
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sickrage.egg-info'), ignore_errors=True)


setup(
        cmdclass={'clean': CleanCommand},
        name='sickrage',
        version=version,
        description='Automatic Video Library Manager for TV Shows',
        author='echel0n',
        author_email='sickrage.tv@gmail.com',
        url='https://github.com/SiCKRAGETV/SickRage',
        keywords=['sickrage', 'sickragetv', 'tv', 'torrent', 'nzb', 'video'],
        packages=["sickrage"],
        include_package_data=True,
        zip_safe=False,
        test_suite='tests',
        entry_points={
            "console_scripts": [
                "sickrage=sickrage:main",
            ]
        },
)
