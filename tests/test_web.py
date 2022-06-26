import json
import os
import shutil
import unittest

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.testing import AsyncTestCase, gen_test

import sickrage
from sickrage.core import Core


class TestWeb(AsyncTestCase):
    def setUp(self):
        super(TestWeb, self).setUp()
        sickrage.app = Core()
        sickrage.app.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
        sickrage.app.cache_dir = os.path.join(sickrage.app.data_dir, 'cache')
        sickrage.app.config_file = os.path.join(sickrage.app.data_dir, 'config.ini')
        sickrage.app.db_type = 'sqlite'
        sickrage.app.web_host = '0.0.0.0'

    def tearDown(self):
        sickrage.app.shutdown()
        super(TestWeb, self).tearDown()
        if os.path.exists(sickrage.app.data_dir):
            shutil.rmtree(sickrage.app.data_dir)

    @gen_test
    def test_http_isalive(self):
        sickrage.app.start()
        client = AsyncHTTPClient(self.io_loop)
        response = yield client.fetch(HTTPRequest(f"http://localhost:8081/home/is-alive?srcallback=jsonp"))
        self.assertEqual(200, response.code)
        self.assertTrue(str(sickrage.app.pid) in response.body.decode())

    @gen_test
    def test_api_v1_ping(self):
        sickrage.app.start()
        client = AsyncHTTPClient(self.io_loop)
        response = yield client.fetch(HTTPRequest(f"http://localhost:8081/api/v1/{sickrage.app.config.general.api_v1_key}/?cmd=sr.ping"))
        self.assertEqual(200, response.code)

        j = json.loads(response.body)
        self.assertEqual(sickrage.app.pid, j['data']['pid'])


if __name__ == '__main__':
    unittest.main()
