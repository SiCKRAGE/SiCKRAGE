import re
import urlparse

import sickbeard
import logging
from sickrage.helper.exceptions import ex
from sickbeard.helpers import normalize_url
from feedparser.api import parse


def getFeed(url, request_headers=None, handlers=None):
    url = normalize_url(url)

    try:
        try:
            feed = parse(url, False, False, request_headers, handlers=handlers)
            feed[b'entries']
            return feed
        except AttributeError:
            err_code = feed.feed[b'error'][b'code']
            err_desc = feed.feed[b'error'][b'description']
            logging.debug('RSS ERROR:[{}] CODE:[{}]'.format(err_desc, err_code))
    except:
        pass
