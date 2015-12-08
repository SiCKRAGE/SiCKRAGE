import re
import urlparse

import sickbeard
from sickbeard import logger
from sickrage.helper.exceptions import ex
from sickbeard.helpers import normalize_url
from feedparser.api import parse

def getFeed(url, request_headers=None, handlers=None):
    url = normalize_url(url)

    try:
        try:
            feed = parse(url, False, False, request_headers, handlers=handlers)
            feed['entries']
            return feed
        except AttributeError:
            err_code = feed.feed['error']['code']
            err_desc = feed.feed['error']['description']
            logger.log(u'RSS ERROR:[{}] CODE:[{}]'.format(err_desc, err_code), logger.DEBUG)
    except:pass