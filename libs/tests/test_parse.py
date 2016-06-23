from datetime import datetime
import os
import unittest

from mock import call, MagicMock, patch

from yarg import newest_packages, latest_updated_packages, HTTPError
from yarg.parse import _get, Package


class GoodNewestResponse(object):
    status_code = 200
    xml = os.path.join(os.path.dirname(__file__),
                           'newest.xml')
    content = open(xml).read()


class GoodUpdatedResponse(object):
    status_code = 200
    xml = os.path.join(os.path.dirname(__file__),
                           'updated.xml')
    content = open(xml).read()


class BadResponse(object):
    status_code = 300
    reason = "Mocked"


class TestParse(unittest.TestCase):

    def setUp(self):
        self.newest = self.setup_newest()
        self.updated = self.setup_updated()

    def setup_newest(self):
        item1 = {'name': 'gobble',
                 'url': 'http://pypi.python.org/pypi/gobble',
                 'description': 'Automatic functional testing for CLI apps.',
                 'date': '09 Aug 2014 06:57:42 GMT'}
        item2 = {'name': 'flask_autorest',
                 'url': 'http://pypi.python.org/pypi/flask_autorest',
                 'description': 'auto create restful apis for database, with the help of dataset.',
                 'date': '09 Aug 2014 05:24:58 GMT'}
        item3 = {'name': 'ranrod',
                 'url': 'http://pypi.python.org/pypi/ranrod',
                 'description': 'download route53 hosted zones as local json files',
                 'date': '09 Aug 2014 05:20:21 GMT'}
        return [Package(item1), Package(item2), Package(item3)]

    def setup_updated(self):
        item1 = {'name': 'pycoin',
                 'version': '0.50',
                 'url': 'http://pypi.python.org/pypi/pycoin/0.50',
                 'description': 'Utilities for Bitcoin and altcoin addresses and transaction manipulation.',
                 'date': '09 Aug 2014 08:40:20 GMT'}
        item2 = {'name': 'django-signup',
                 'version': '0.6.0',
                 'url': 'http://pypi.python.org/pypi/django-signup/0.6.0',
                 'description': 'A user registration app for Django with support for custom user models',
                 'date': '09 Aug 2014 08:33:53 GMT'}
        item3 = {'name': 'pyADC',
                 'version': '0.1.3',
                 'url': 'http://pypi.python.org/pypi/pyADC/0.1.3',
                 'description': 'Python implementation of the ADC(S) Protocol for Direct Connect.',
                 'date': '09 Aug 2014 08:19:56 GMT'}
        return [Package(item1), Package(item2), Package(item3)]

    @patch('requests.get', return_value=BadResponse)
    def test_newest_packages_bad_get(self, get_mock):
        # Python 2.6....
        try:
            newest_packages()
        except HTTPError as e:
            self.assertEqual(300, e.status_code)
            self.assertEqual(e.status_code, e.errno)
            self.assertEqual(e.reason, e.message)

    @patch('requests.get', return_value=BadResponse)
    def test_updated_packages_bad_get(self, get_mock):
        # Python 2.6....
        try:
            latest_updated_packages()
        except HTTPError as e:
            self.assertEqual(300, e.status_code)
            self.assertEqual(e.status_code, e.errno)
            self.assertEqual(e.reason, e.message)

    @patch('requests.get', return_value=GoodNewestResponse)
    def test_newest_packages(self, get_mock):
        p = newest_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=packages_rss'),
                         get_mock.call_args)
        self.assertEqual(self.newest[0].name, p[0].name)
        self.assertEqual(self.newest[1].name, p[1].name)
        self.assertEqual(self.newest[2].name, p[2].name)

    @patch('requests.get', return_value=GoodNewestResponse)
    def test_newest_package(self, get_mock):
        p = newest_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=packages_rss'),
                         get_mock.call_args)
        self.assertEqual('gobble', p[0].name)
        self.assertEqual('http://pypi.python.org/pypi/gobble', p[0].url)
        self.assertEqual('Automatic functional testing for CLI apps.',
                         p[0].description)
        self.assertEqual(datetime.strptime('09 Aug 2014 06:57:42 GMT',
                                           "%d %b %Y %H:%M:%S %Z"),
                         p[0].date)

    @patch('requests.get', return_value=GoodNewestResponse)
    def test_newest_package_repr(self, get_mock):
        p = newest_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=packages_rss'),
                         get_mock.call_args)
        self.assertEqual('<Package gobble>', p[0].__repr__())

    @patch('requests.get', return_value=GoodNewestResponse)
    def test_newest_package_version(self, get_mock):
        p = newest_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=packages_rss'),
                         get_mock.call_args)
        self.assertEqual(None, p[0].version)

    @patch('requests.get', return_value=GoodUpdatedResponse)
    def test_updated_packages(self, get_mock):
        p = latest_updated_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=rss'),
                         get_mock.call_args)
        self.assertEqual(self.updated[0].name, p[0].name)
        self.assertEqual(self.updated[0].version, p[0].version)
        self.assertEqual(self.updated[1].name, p[1].name)
        self.assertEqual(self.updated[1].version, p[1].version)
        self.assertEqual(self.updated[2].name, p[2].name)
        self.assertEqual(self.updated[2].version, p[2].version)

    @patch('requests.get', return_value=GoodUpdatedResponse)
    def test_updated_package(self, get_mock):
        p = latest_updated_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=rss'),
                         get_mock.call_args)
        self.assertEqual('pycoin', p[0].name)
        self.assertEqual('0.50', p[0].version)
        self.assertEqual('http://pypi.python.org/pypi/pycoin/0.50', p[0].url)
        self.assertEqual('Utilities for Bitcoin and altcoin addresses and transaction manipulation.',
                         p[0].description)
        self.assertEqual(datetime.strptime('09 Aug 2014 08:40:20 GMT',
                                           "%d %b %Y %H:%M:%S %Z"),
                         p[0].date)

    @patch('requests.get', return_value=GoodUpdatedResponse)
    def test_updated_package_repr(self, get_mock):
        p = latest_updated_packages()
        self.assertEqual(call('https://pypi.python.org/pypi?%3Aaction=rss'),
                         get_mock.call_args)
        self.assertEqual('<Package pycoin>', p[0].__repr__())
