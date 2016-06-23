import unittest

from yarg import HTTPError


class TestHTTPErrorWithReason(unittest.TestCase):

    def setUp(self):
        self.error = HTTPError(status_code=300,
                               reason="Test")

    def test_repr(self):
        self.assertEqual('<HTTPError 300 Test>',
                         self.error.__repr__())

    def test_str(self):
        self.assertEqual('<HTTPError 300 Test>',
                         self.error.__str__())

class TestHTTPErrorNoReason(unittest.TestCase):

    def setUp(self):
        self.error = HTTPError()

    def test_repr(self):
        self.assertEqual('<HTTPError>',
                         self.error.__repr__())

    def test_str(self):
        self.assertEqual('<HTTPError>',
                         self.error.__str__())
