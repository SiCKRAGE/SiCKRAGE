# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

import logging
import sickbeard
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
            logging.debug('RSS ERROR:[{}] CODE:[{}]'.format(
                    feed.feed[b'error'][b'description'],
                    feed.feed[b'error'][b'code']))
    except:pass
