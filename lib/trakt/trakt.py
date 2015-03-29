import requests
import json
from sickbeard import logger

from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, trakt_oauth, disable_ssl_verify=False, timeout=30):
        self.trakt_oauth = trakt_oauth
        self.verify = not disable_ssl_verify
        self.timeout = timeout if timeout else None
        self.api_url = 'https://api-v2launch.trakt.tv/'
        self.headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': trakt_oauth['client_id'],
        }

    def getToken(self, refresh=False, authorization_code=None):
        data = {
            "client_id": self.trakt_oauth['client_id'],
            "client_secret": self.trakt_oauth['client_secret'],
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
        }
       
        if refresh:
            data['grant_type'] = "refresh_token"
            data['refresh_token'] = self.trakt_oauth['refresh_token']
        else:
            data['grant_type'] = "authorization_code"
            if not None == authorization_code:
                data['code'] = authorization_code
        
        headers = {
            'Content-Type': 'application/json'
        } 
 
        resp = self.traktRequest('oauth/token', data, headers, 'POST')
        return resp

        
    def validateAccount(self):   
        resp = self.traktRequest(self.trakt_oauth['username']+"/settings",None,None,'POST')
        if 'account' in resp:
            return True
        return False

    def traktRequest(self, path, data=None, headers=None, method='GET'):
        url = self.api_url + path
        if None == headers:
            headers = self.headers
        
        if 'access_token' in self.trakt_oauth:
            headers['Authorization'] = 'Bearer ' + self.trakt_oauth['access_token']
        
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
                raise traktException(e)
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u"Retrying trakt api request: %s" % path, logger.WARNING)
                return self.traktRequest(path, data, headers, method)
            elif code == 401:
                logger.log(u"Unauthorized. Please check your Trakt settings", logger.WARNING)
                raise traktAuthException(e)
            elif code in (500,501,503,504,520,521,522):
                #http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u"Trakt may have some issues and it's unavailable. Try again later please", logger.WARNING)
                raise traktServerBusy(e)
            else:
                raise traktException(e)

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp