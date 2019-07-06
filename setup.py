import glob
import os
import shutil

from setuptools import setup, Command


def version():
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'sickrage', 'version.txt'))) as f:
        return f.read()


def requirements():
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))) as f:
        return f.read().splitlines()


def requirements_dev():
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements-dev.txt'))) as f:
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


cmd_class = {'clean': CleanCommand}

# Check for Babel availability
try:
    from babel.messages.frontend import compile_catalog, extract_messages, init_catalog, update_catalog

    cmd_class.update(dict(
        compile_catalog=compile_catalog,
        extract_messages=extract_messages,
        init_catalog=init_catalog,
        update_catalog=update_catalog
    ))
except ImportError:
    pass

setup(
    name='sickrage',
    version=version(),
    description='Automatic Video Library Manager for TV Shows',
    author='echel0n',
    author_email='echel0n@sickrage.ca',
    license='GPLv3',
    url='https://git.sickrage.ca',
    keywords=['sickrage', 'sickragetv', 'tv', 'torrent', 'nzb', 'video', 'echel0n'],
    packages=['sickrage'],
    install_requires=requirements(),
    extras_require={
        'dev': requirements_dev()
    },
    include_package_data=True,
    python_requires='>=3',
    platforms='any',
    zip_safe=False,
    test_suite='tests',
    cmdclass=cmd_class,
    entry_points={
        "console_scripts": [
            "sickrage=sickrage:main"
        ]
    },
    message_extractors={
        'sickrage/core/webserver': [
            ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'})
        ],
        'sickrage': [
            ('**.py', 'python', None)
        ],
        'src': [
            ('**/js/*.min.js', 'ignore', None),
            ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
        ],
    }
)
