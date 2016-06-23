from collections import namedtuple
from datetime import datetime
import json
import os
import unittest

from yarg.package import json2package
from yarg.release import Release


class TestRelease(unittest.TestCase):

    def setUp(self):
        package = os.path.join(os.path.dirname(__file__),
                               'package.json')
        self.json = json.loads(open(package).read())
        self.package = json2package(open(package).read())

    def test_release_ids(self):
        self.assertEquals([u'0.0.0', u'0.0.2', u'0.0.15'],
                          self.package.release_ids)

    def test_release(self):
        release_id = '0.0.2'
        release = self.json['releases'][release_id]
        release_list = [Release(release_id, r) for r in release]
        self.assertEquals(release_list[0].md5_digest,
                          self.package.release(release_id)[0].md5_digest)
        self.assertEquals(release_list[1].md5_digest,
                          self.package.release(release_id)[1].md5_digest)
        self.assertEquals('3e3098611177c34706de2e10476b3e50',
                          self.package.release(release_id)[0].md5_digest)
        self.assertEquals('be198baa95116c1c9d17874428e3a0c6',
                          self.package.release(release_id)[1].md5_digest)

    def test_repr(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(u'<Release 0.0.2>', release.__repr__())

    def test_release_id(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(release_id, release.release_id)

    def test_release_id(self):
        release_id = '0.0.3'
        release = self.package.release(release_id)
        self.assertEquals(None, release)

    def test_release_uploaded(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(datetime.strptime("2014-08-16T12:21:20",
                                            "%Y-%m-%dT%H:%M:%S"),
                          release.uploaded)

    def test_release_python_version(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(u'2.7', release.python_version)

    def test_release_url(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        url = u'https://pypi.python.org/packages/2.7/y/yarg/yarg-0.0.2-py2.py3-none-any.whl'
        self.assertEquals(url, release.url)

    def test_release_md5(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        md5 = u'3e3098611177c34706de2e10476b3e50'
        self.assertEquals(md5, release.md5_digest)

    def test_release_filename(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        filename = u'yarg-0.0.2-py2.py3-none-any.whl'
        self.assertEquals(filename, release.filename)

    def test_release_size(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        size = 21596
        self.assertEquals(size, release.size)

    def test_release_unknown_package_type(self):
        release_id = '0.0.0'
        release = self.package.release(release_id)[0]
        self.assertEquals(u'wheeeel', release.package_type)

    def test_release_package_type(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(u'wheel', release.package_type)

    def test_release_has_sig(self):
        release_id = '0.0.2'
        release = self.package.release(release_id)[0]
        self.assertEquals(True, release.has_sig)

    def test_latest_release_id(self):
        self.assertEquals(u'0.0.15', self.package.latest_release_id)

    def test_latest_release(self):
        release_id = '0.0.15'
        release = self.json['releases'][release_id]
        release_list = [Release(release_id, r) for r in release]
        self.assertEquals(release_list[0].md5_digest,
                          self.package.latest_release[0].md5_digest)
        self.assertEquals(release_list[1].md5_digest,
                          self.package.latest_release[1].md5_digest)
        self.assertEquals('3e3098611177c34706de2e10476b3e51',
                          self.package.latest_release[0].md5_digest)
        self.assertEquals('be198baa95116c1c9d17874428e3a0c7',
                          self.package.latest_release[1].md5_digest)
