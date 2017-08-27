from __future__ import absolute_import, division, print_function

import logging

from six.moves.urllib.parse import urlsplit, urlunsplit, parse_qsl
from trakt.core.errors import log_request_error
from trakt.core.helpers import try_convert

log = logging.getLogger(__name__)


class PaginationIterator(object):
    def __init__(self, client, response):
        self.client = client
        self.response = response

        # Retrieve pagination headers
        self.per_page = try_convert(response.headers.get('x-pagination-limit'), int)
        self.total_items = try_convert(response.headers.get('x-pagination-item-count'), int)
        self.total_pages = try_convert(response.headers.get('x-pagination-page-count'), int)

        # Parse request url
        scheme, netloc, path, query = urlsplit(self.response.request.url)[:4]

        self.url = urlunsplit([scheme, netloc, path, '', ''])
        self.query = dict(parse_qsl(query))

    def fetch(self, page, per_page=None):
        if int(page) == int(self.query.get('page', 1)):
            return self.response

        if per_page is None:
            per_page = self.per_page or 10

        # Retrieve request details
        request = self.response.request.copy()

        # Build query parameters
        query = self.query.copy()

        if page != 1:
            query['page'] = page

        if per_page != 10:
            query['limit'] = per_page

        # Construct request
        request.prepare_url(self.url, query)

        # Send request
        return self.client.http.send(request)

    def get(self, page):
        response = self.fetch(page)

        if response is None:
            log.warn('Request failed (no response returned)')
            return None

        if response.status_code < 200 or response.status_code >= 300:
            log_request_error(log, response)
            return None

        # Parse response, return data
        content_type = response.headers.get('content-type')

        if content_type and content_type.startswith('application/json'):
            # Try parse json response
            try:
                data = response.json()
            except Exception as e:
                log.warning('Unable to parse page: %s', e)
                return None
        else:
            log.warning('Received a page with an invalid content type: %r', content_type)
            return None

        return data

    def __iter__(self):
        # Retrieve current page number
        current = int(self.query.get('page', 1))

        # Fetch pages
        while current <= self.total_pages:
            items = self.get(current)

            if not items:
                log.warning('Unable to retrieve page #%d, pagination iterator cancelled', current)
                break

            for item in items:
                yield item

            current += 1
