# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import json
from urllib.parse import urljoin

import sickrage
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websession import WebSession
from sickrage.core.databases.main import MainDB
from sickrage.search_providers import SearchProviderType


class SabNZBd(object):
    @staticmethod
    def sendNZB(nzb):
        """
        Sends an NZB to SABnzbd via the API.
        :param nzb: The NZBSearchResult object to send to SAB
        """

        show_object = find_show(nzb.series_id, nzb.series_provider_id)
        if not show_object:
            return False

        category = sickrage.app.config.sabnzbd.category
        if show_object.is_anime:
            category = sickrage.app.config.sabnzbd.category_anime

        # if it aired more than 7 days ago, override with the backlog category IDs
        for episode__number in nzb.episodes:
            episode_object = show_object.get_episode(nzb.season, episode__number)
            if datetime.date.today() - episode_object.airdate > datetime.timedelta(days=7):
                category = sickrage.app.config.sabnzbd.category_anime_backlog if episode_object.show.is_anime else sickrage.app.config.sabnzbd.category_backlog

        # set up a dict with the URL params in it
        params = {'output': 'json'}
        if sickrage.app.config.sabnzbd.username:
            params['ma_username'] = sickrage.app.config.sabnzbd.username
        if sickrage.app.config.sabnzbd.password:
            params['ma_password'] = sickrage.app.config.sabnzbd.password
        if sickrage.app.config.sabnzbd.apikey:
            params['apikey'] = sickrage.app.config.sabnzbd.apikey

        if category:
            params['cat'] = category

        if nzb.priority:
            params['priority'] = 2 if sickrage.app.config.sabnzbd.forced else 1

        sickrage.app.log.info('Sending NZB to SABnzbd')
        url = urljoin(sickrage.app.config.sabnzbd.host, 'api')

        try:
            jdata = None

            if nzb.provider_type == SearchProviderType.NZB:
                params['mode'] = 'addurl'
                params['name'] = nzb.url
                jdata = WebSession().get(url, params=params, verify=False).json()
            elif nzb.provider_type == SearchProviderType.NZBDATA:
                params['mode'] = 'addfile'
                multiPartParams = {'nzbfile': (nzb.name + '.nzb', nzb.extraInfo[0])}
                jdata = WebSession().get(url, params=params, file=multiPartParams, verify=False).json()

            if not jdata:
                raise Exception
        except Exception:
            sickrage.app.log.info('Error connecting to sab, no data returned')
            return False

        sickrage.app.log.debug('Result text from SAB: {}'.format(jdata))

        result, error_ = SabNZBd._check_sab_response(jdata)
        return result

    @staticmethod
    def _check_sab_response(jdata):
        """
        Check response from SAB
        :param jdata: Response from requests api call
        :return: a list of (Boolean, string) which is True if SAB is not reporting an error
        """
        error = jdata.get('error')

        if error:
            sickrage.app.log.warning("SABnzbd Error: {}".format(error))

        return not error, error or json.dumps(jdata)

    @staticmethod
    def get_sab_access_method(host=None):
        """
        Find out how we should connect to SAB
        :param host: hostname where SAB lives
        :return: (boolean, string) with True if method was successful
        """
        params = {
            'mode': 'auth',
            'output': 'json',
            'ma_username': sickrage.app.config.sabnzbd.username,
            'ma_password': sickrage.app.config.sabnzbd.username,
            'apikey': sickrage.app.config.sabnzbd.apikey
        }

        url = urljoin(host, 'api')

        try:
            data = WebSession().get(url, params=params, verify=False).json()
            if not data:
                return False, data
        except Exception:
            return False, ""

        return SabNZBd._check_sab_response(data)

    @staticmethod
    def test_authentication(host=None, username=None, password=None, apikey=None):
        """
        Sends a simple API request to SAB to determine if the given connection information is connect
        :param host: The host where SAB is running (incl port)
        :param username: The username to use for the HTTP request
        :param password: The password to use for the HTTP request
        :param apikey: The API key to provide to SAB
        :return: A tuple containing the success boolean and a message
        """

        # build up the URL parameters
        params = {
            'mode': 'queue',
            'output': 'json',
            'ma_username': username,
            'ma_password': password,
            'apikey': apikey
        }

        url = urljoin(host, 'api')

        try:
            # check the result and determine if it's good or not
            data = WebSession().get(url, params=params, verify=False).json()
            if not data:
                return False, data

            result, sab_text = SabNZBd._check_sab_response(data)
            if not result:
                return False, sab_text
        except Exception:
            return False, ""

        return True, 'Success'
