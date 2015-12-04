import sys
import os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

import test_lib as test

from sickbeard import config

class QualityTests(test.SiCKRAGETestCase):

    def test_clean_url(self):
        self.assertEqual(config.clean_url("https://subdomain.domain.tld/endpoint"), "https://subdomain.domain.tld/endpoint")
        self.assertEqual(config.clean_url("google.com/xml.rpc"), "http://google.com/xml.rpc")
        self.assertEqual(config.clean_url("google.com"), "http://google.com/")
        self.assertEqual(config.clean_url("http://www.example.com/folder/"), "http://www.example.com/folder/")
        self.assertEqual(config.clean_url("scgi:///home/user/.config/path/socket"), "scgi:///home/user/.config/path/socket")

if __name__ == '__main__':
    print "=================="
    print "STARTING - CONFIG TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(QualityTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
