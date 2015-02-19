import requests
import json
from sickbeard import logger

class TraktAPI():
    def __init__(self, apikey, username=None, password=None, disable_ssl_verify=False, timeout=30):
        self.username = username
        self.password = password
        self.verify = not disable_ssl_verify
        self.timeout = timeout if timeout else None
        self.api_url = 'https://api.trakt.tv/'
        self.headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': apikey,
        }

    def validateAccount(self):
        if hasattr(self, 'token'):
            del(self.token)
        data = {
            'login': self.username,
            'password': self.password
        }
        try:
            resp = requests.request('POST', self.api_url+"auth/login", headers=self.headers,
                data=json.dumps(data), timeout=self.timeout, verify=self.verify)
            resp.raise_for_status()
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise Exception
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u"Retrying trakt api request: auth/login", logger.WARNING)
                return self.validateAccount()
            else:
                logger.log(e, logger.WARNING)
        if 'token' in resp:
            self.token = resp['token']
            return True
        return False

    def traktRequest(self, path, data=None, method='GET'):
        url = self.api_url + path
        headers = self.headers
        if not getattr(self, 'token', None):
            self.validateAccount()
        headers['trakt-user-login'] = self.username
        headers['trakt-user-token'] = self.token

        # request the URL from trakt and parse the result as json
        try:
            resp = requests.request(method, url, headers=headers, timeout=self.timeout,
                data=json.dumps(data) if data else [], verify=self.verify)

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise Exception
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u"Retrying trakt api request: %s" % path, logger.WARNING)
                return self.traktRequest(path, data, method)
            else:
                logger.log(e, logger.WARNING)

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                logger.log(resp['message'],logger.ERROR)
            if 'error' in resp:
                logger.log(resp['error'],logger.ERROR)
            else:
                logger.log(U"Unknown Error",logger.ERROR)

        return resp
