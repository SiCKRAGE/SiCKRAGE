"""
The httplib2 algorithms ported for use with requests.
"""
import re
import calendar
import time
import datetime

from requests.structures import CaseInsensitiveDict

from .cache import DictCache
from .compat import parsedate_tz
from .serialize import Serializer

URI = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")


def parse_uri(uri):
    """Parses a URI using the regex given in Appendix B of RFC 3986.

        (scheme, authority, path, query, fragment) = parse_uri(uri)
    """
    groups = URI.match(uri).groups()
    return (groups[1], groups[3], groups[4], groups[6], groups[8])


class CacheController(object):
    """An interface to see if request should cached or not.
    """
    def __init__(self, cache=None, cache_etags=True, serializer=None):
        self.cache = cache or DictCache()
        self.cache_etags = cache_etags
        self.serializer = serializer or Serializer()

    def _urlnorm(self, uri):
        """Normalize the URL to create a safe key for the cache"""
        (scheme, authority, path, query, fragment) = parse_uri(uri)
        if not scheme or not authority:
            raise Exception("Only absolute URIs are allowed. uri = %s" % uri)
        authority = authority.lower()
        scheme = scheme.lower()
        if not path:
            path = "/"

        # Could do syntax based normalization of the URI before
        # computing the digest. See Section 6.2.2 of Std 66.
        request_uri = query and "?".join([path, query]) or path
        scheme = scheme.lower()
        defrag_uri = scheme + "://" + authority + request_uri

        return defrag_uri

    def cache_url(self, uri):
        return self._urlnorm(uri)

    def parse_cache_control(self, headers):
        """
        Parse the cache control headers returning a dictionary with values
        for the different directives.
        """
        retval = {}

        cc_header = 'cache-control'
        if 'Cache-Control' in headers:
            cc_header = 'Cache-Control'

        if cc_header in headers:
            parts = headers[cc_header].split(',')
            parts_with_args = [
                tuple([x.strip().lower() for x in part.split("=", 1)])
                for part in parts if -1 != part.find("=")]
            parts_wo_args = [(name.strip().lower(), 1)
                             for name in parts if -1 == name.find("=")]
            retval = dict(parts_with_args + parts_wo_args)
        return retval

    def cached_request(self, request):
        cache_url = self.cache_url(request.url)
        cc = self.parse_cache_control(request.headers)

        # non-caching states
        no_cache = True if 'no-cache' in cc else False
        if 'max-age' in cc and cc['max-age'] == 0:
            no_cache = True

        # Bail out if no-cache was set
        if no_cache:
            return False

        # It is in the cache, so lets see if it is going to be
        # fresh enough
        resp = self.serializer.loads(request, self.cache.get(cache_url))

        # Check to see if we have a cached object
        if not resp:
            return False

        headers = CaseInsensitiveDict(resp.headers)

        now = time.time()
        date = calendar.timegm(
            parsedate_tz(headers['date'])
        )
        current_age = max(0, now - date)

        # TODO: There is an assumption that the result will be a
        # urllib3 response object. This may not be best since we
        # could probably avoid instantiating or constructing the
        # response until we know we need it.
        resp_cc = self.parse_cache_control(headers)

        # determine freshness
        freshness_lifetime = 0
        if 'max-age' in resp_cc and resp_cc['max-age'].isdigit():
            freshness_lifetime = int(resp_cc['max-age'])
        elif 'expires' in headers:
            expires = parsedate_tz(headers['expires'])
            if expires is not None:
                expire_time = calendar.timegm(expires) - date
                freshness_lifetime = max(0, expire_time)

        # determine if we are setting freshness limit in the req
        if 'max-age' in cc:
            try:
                freshness_lifetime = int(cc['max-age'])
            except ValueError:
                freshness_lifetime = 0

        if 'min-fresh' in cc:
            try:
                min_fresh = int(cc['min-fresh'])
            except ValueError:
                min_fresh = 0
            # adjust our current age by our min fresh
            current_age += min_fresh

        # see how fresh we actually are
        fresh = (freshness_lifetime > current_age)

        if fresh:
            return resp

        # we're not fresh. If we don't have an Etag, clear it out
        if 'etag' not in headers:
            self.cache.delete(cache_url)

        # return the original handler
        return False

    def conditional_headers(self, request):
        cache_url = self.cache_url(request.url)
        resp = self.serializer.loads(request, self.cache.get(cache_url))
        new_headers = {}

        if resp:
            headers = CaseInsensitiveDict(resp.headers)

            if 'etag' in headers:
                new_headers['If-None-Match'] = headers['ETag']

            if 'last-modified' in headers:
                new_headers['If-Modified-Since'] = headers['Last-Modified']

        return new_headers

    def cache_response(self, request, response):
        """
        Algorithm for caching requests.

        This assumes a requests Response object.
        """
        # From httplib2: Don't cache 206's since we aren't going to
        # handle byte range requests
        if response.status not in [200, 203]:
            return

        # Cache Session Params
        cache_auto = getattr(request, 'cache_auto', False)
        cache_urls = getattr(request, 'cache_urls', [])
        cache_max_age = getattr(request, 'cache_max_age', None)

        response_headers = CaseInsensitiveDict(response.headers)

        # Check if we are wanting to cache responses from specific urls only
        cache_url = self.cache_url(request.url)
        if len(cache_urls) > 0 and not any(s in cache_url for s in cache_urls):
                return

        cc_req = self.parse_cache_control(request.headers)
        cc = self.parse_cache_control(response_headers)

        # Delete it from the cache if we happen to have it stored there
        no_store = cc.get('no-store') or cc_req.get('no-store')
        if no_store and self.cache.get(cache_url):
            self.cache.delete(cache_url)

        # If we've been given an etag, then keep the response
        if self.cache_etags and 'etag' in response_headers:
            self.cache.set(cache_url, self.serializer.dumps(request, response))

        # If we want to cache sites not setup with cache headers then add the proper headers and keep the response
        elif cache_auto and not cc and response_headers:
            headers = {'Cache-Control': 'public,max-age=%d' % int(cache_max_age or 900)}
            response.headers.update(headers)

            if 'expires' not in response_headers:
                if getattr(response_headers, 'expires', None) is None:
                    expires = datetime.datetime.utcnow() + datetime.timedelta(days=1)
                    expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    headers = {'Expires': expires}
                    response.headers.update(headers)

            self.cache.set(cache_url, self.serializer.dumps(request, response))

        # Add to the cache if the response headers demand it. If there
        # is no date header then we can't do anything about expiring
        # the cache.
        elif 'date' in response_headers:
            # cache when there is a max-age > 0
            if cc and cc.get('max-age'):
                if int(cc['max-age']) > 0:
                    if isinstance(cache_max_age, int):
                        cc['max-age'] = int(cache_max_age)
                        response.headers['cache-control'] = ''.join(['%s=%s' % (key, value) for (key, value) in cc.items()])
                    self.cache.set(cache_url, self.serializer.dumps(request, response))

            # If the request can expire, it means we should cache it
            # in the meantime.
            elif 'expires' in response_headers:
                if response_headers['expires']:
                    self.cache.set(
                        cache_url,
                        self.serializer.dumps(request, response),
                    )

    def update_cached_response(self, request, response):
        """On a 304 we will get a new set of headers that we want to
        update our cached value with, assuming we have one.

        This should only ever be called when we've sent an ETag and
        gotten a 304 as the response.
        """
        cache_url = self.cache_url(request.url)

        cached_response = self.serializer.loads(request, self.cache.get(cache_url))

        if not cached_response:
            # we didn't have a cached response
            return response

        # did so lets update our headers
        cached_response.headers.update(response.headers)

        # we want a 200 b/c we have content via the cache
        cached_response.status = 200

        # update our cache
        self.cache.set(
            cache_url,
            self.serializer.dumps(request, cached_response),
        )

        return cached_response
