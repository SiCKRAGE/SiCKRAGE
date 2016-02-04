# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import feedparser
from feedparser import FeedParserDict

import sickrage
from core.helpers import normalize_url

def getFeed(url, request_headers=None, handlers=None):
    feed = FeedParserDict()
    try:
        try:
            feed = feedparser.parse(normalize_url(url), False, False, request_headers, handlers=handlers)
        except AttributeError:
            sickrage.srCore.LOGGER.debug('RSS ERROR:[{}] CODE:[{}]'.format(
                    feed.feed[b'error'][b'description'], feed.feed[b'error'][b'code']))
    except:pass

    return feed
