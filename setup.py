import glob
import os
import sys

from setuptools import setup, find_packages

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload')
    sys.exit()

# Get the version number
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sickrage', 'version.txt')) as f:
    version = f.read()

# Get requirements
requirements = []
for file in glob.glob(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'requirements', '*.txt')):
    with open(file) as f:
        requirements += f.readlines()

setup(
        name='sickrage',
        version=version,
        description='Automatic Video Library Manager for TV Shows',
        author='echel0n',
        author_email='sickrage.tv@gmail.com',
        url='https://github.com/SiCKRAGETV/SickRage',
        keywords=['sickrage', 'sickragetv', 'sickrage', 'tv', 'torrent', 'nzb'],
        install_requires=requirements,
        packages=find_packages(),
        py_modules=["SiCKRAGE", "SickBeard"],
        zip_safe=False,
        include_package_data=True,
        test_suite='tests',
        entry_points={
            "console_scripts": [
                "sickrage=sickrage:main",
            ]
        },
)
