#!/usr/bin/env python3
# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

"""
Test Provider Result Parsing
When recording new cassettes:
    Set overwrite_cassettes = True
    Delete the cassette yml file with the same base filename as this file in the cassettes dir next to this file
    Be sure to adjust the self.search_strings so they return results. They must be identical to search strings generated by SickRage
"""

import os
import re
import unittest
from functools import wraps

from vcr_unittest import VCRMixin

import sickrage
import tests
from sickrage.core.helpers import validate_url
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow
from sickrage.core.websession import WebSession

overwrite_cassettes = False

disabled_providers = ['bitcannon', 'torrent9']

disabled_provider_tests = {
    'Cpasbien': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'Torrent9': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'TorrentProject': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'TokyoToshokan': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'LimeTorrents': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'SkyTorrents': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'ilCorsaroNero': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'HorribleSubs': ['test_season_search'],
    'NyaaTorrents': ['test_season_search'],
    'Newpct': ['test_season_search'],
}

test_string_overrides = {
    'Cpasbien': {'ID': 268592, 'Name': 'The 100', 'Season': 2, 'Episode': 16, 'ABS': 0, 'Anime': False},
    'Torrent9': {'ID': 72108, 'Name': 'NCIS', 'Season': 14, 'Episode': 9, 'ABS': 0, 'Anime': False},
    'NyaaTorrents': {'ID': 295068, 'Name': 'Dragon Ball Super', 'Season': 5, 'Episode': 40, 'ABS': 116, 'Anime': True},
    'TokyoToshokan': {'ID': 295068, 'Name': 'Dragon Ball Super', 'Season': 5, 'Episode': 40, 'ABS': 116, 'Anime': True},
    'HorribleSubs': {'ID': 295068, 'Name': 'Dragon Ball Super', 'Season': 5, 'Episode': 40, 'ABS': 116, 'Anime': True},
    'Newpct': {'ID': 153021, 'Name': 'The Walking Dead', 'Season': 8, 'Episode': 6, 'ABS': 0, 'Anime': False},
    'EliteTorrent': {'ID': 82066, 'Name': 'Fringe', 'Season': 5, 'Episode': 11, 'ABS': 0, 'Anime': False},
    'Rarbg': {'ID': 153021, 'Name': 'The Walking Dead', 'Season': 8, 'Episode': 6, 'ABS': 0, 'Anime': False},
}

magnet_regex = re.compile(r'magnet:\?xt=urn:btih:\w{32,40}(:?&dn=[\w. %+-]+)*(:?&tr=(:?tcp|https?|udp)[\w%. +-]+)*')


class ProviderTests(type):
    class ProviderTest(VCRMixin, tests.SiCKRAGETestDBCase):
        provider = None

        def setUp(self):
            super(ProviderTests.ProviderTest, self).setUp()
            self.show = TVShow(test_string_overrides.get(self.provider.name, {'ID': 82066})['ID'], 1, "eng")
            self.show.name = test_string_overrides.get(self.provider.name, {'Name': 'Fringe'})['Name']
            self.show.anime = test_string_overrides.get(self.provider.name, {'Anime': False})['Anime']

            self.ep = TVEpisode(self.show,
                                test_string_overrides.get(self.provider.name, {'Season': 1})['Season'],
                                test_string_overrides.get(self.provider.name, {'Episode': 1})['Episode'])
            self.ep.absolute_number = test_string_overrides.get(self.provider.name, {'ABS': 0})['ABS']
            self.ep.scene_season = self.ep.season
            self.ep.scene_episode = self.ep.episode
            self.ep.scene_absolute_number = self.ep.absolute_number

            self.provider.username = self.username
            self.provider.password = self.password

        @property
        def username(self):  # pylint: disable=no-self-use
            # TODO: Make this read usernames from somewhere
            return ''

        @property
        def password(self):  # pylint: disable=no-self-use
            # TODO: Make this read passwords from somewhere
            return ''

        def search_strings(self, mode):
            _search_strings = {
                'RSS': self.provider.cache.search_strings['RSS'],
                'Episode': self.provider._get_episode_search_strings(self.ep)[0]['Episode'],
                'Season': self.provider._get_season_search_strings(self.ep)[0]['Season']
            }
            return {mode: _search_strings[mode]}

        def magic_skip(func):
            @wraps(func)
            def magic(self, *args, **kwargs):
                if func.__name__ in disabled_provider_tests.get(self.provider.name, []):
                    self.skipTest('Test is programmatically disabled for provider {}'.format(self.provider.name))
                func(self, *args, **kwargs)

            return magic

        def skipIfPrivate(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                if self.provider.private:
                    self.skipTest('Private providers unsupported')
                func(self, *args, **kwargs)

            return wrapper

        def _get_vcr_kwargs(self):
            """Don't allow the suite to write to cassettes unless we say so"""
            if overwrite_cassettes:
                return {'record_mode': 'new_episodes'}
            return {'record_mode': 'once'}

        def _get_cassette_name(self):
            """Returns the filename to use for the cassette"""
            return os.path.join(self.TESTDIR, 'providers/cassettes/{}.yaml'.format(self.provider.id))

        def shortDescription(self):
            if self._testMethodDoc and self.provider:
                return self._testMethodDoc.replace('the provider', self.provider.name)
            return None

        @magic_skip
        @skipIfPrivate
        def test_rss_search(self):
            """Check that the provider parses rss search results"""
            results = self.provider.search(self.search_strings('RSS'), ep_obj=self.ep)

            if self.provider.enable_daily:
                self.assertTrue(self.cassette.requests)
                self.assertTrue(results, self.cassette.requests[-1].url)
                self.assertTrue(len(self.cassette))

        @magic_skip
        @skipIfPrivate
        def test_episode_search(self):
            """Check that the provider parses episode search results"""
            results = self.provider.search(self.search_strings('Episode'), ep_obj=self.ep)

            self.assertTrue(self.cassette.requests)
            self.assertTrue(results, results)
            self.assertTrue(results, self.cassette.requests[-1].url)
            self.assertTrue(len(self.cassette))

        @magic_skip
        @skipIfPrivate
        def test_season_search(self):
            """Check that the provider parses season search results"""
            results = self.provider.search(self.search_strings('Season'), ep_obj=self.ep)

            self.assertTrue(self.cassette.requests)
            self.assertTrue(results, self.cassette.requests[-1].url)
            self.assertTrue(len(self.cassette))

        def test_url(self):
            resp = WebSession(cache=False).get(self.provider.url, timeout=30)
            self.assertTrue(self.provider.url in resp.url,
                            '{} redirected to {}'.format(self.provider.url, resp.url))
            self.assertTrue(resp.status_code in [200, 403],
                            '{} returned a status code of {}'.format(resp.url, resp.status_code))

        @skipIfPrivate
        @unittest.skip('Not yet implemented')
        def test_cache_update(self):
            """Check that the provider's cache parses rss search results"""
            self.provider.cache.update()

        @skipIfPrivate
        def test_result_values(self):
            """Check that the provider returns results in proper format"""
            results = self.provider.search(self.search_strings('Episode'), ep_obj=self.ep)
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertEqual(sorted(result.keys()), ['leechers', 'link', 'seeders', 'size', 'title'])

                self.assertIsInstance(result['title'], str)
                self.assertIsInstance(result['link'], str)
                self.assertIsInstance(result['seeders'], int)
                self.assertIsInstance(result['leechers'], int)
                self.assertIsInstance(result['size'], int)

                self.assertTrue(len(result['title']))
                self.assertTrue(len(result['link']))
                self.assertTrue(result['seeders'] >= 0)
                self.assertTrue(result['leechers'] >= 0)
                self.assertTrue(result['size'] >= -1)

                if result['link'].startswith('magnet'):
                    self.assertTrue(magnet_regex.match(result['link']))
                else:
                    self.assertTrue(validate_url(result['link']))

                self.assertIsInstance(self.provider._get_size(result), int)
                self.assertTrue(all(self.provider._get_title_and_url(result)))
                self.assertTrue(self.provider._get_size(result))

        @unittest.skip('Not yet implemented')
        def test_season_search_strings_format(self):
            """Check format of the provider's season search strings"""
            pass

        @unittest.skip('Not yet implemented')
        def test_episode_search_strings_format(self):
            """Check format of the provider's season search strings"""
            pass


for providerID, providerObj in sickrage.app.search_providers.torrent().items():
    if not providerID in disabled_providers:
        klassname = "{}Tests".format(providerObj.name)
        globals()[klassname] = type(klassname, (ProviderTests.ProviderTest,), {'provider': providerObj})

if __name__ == '__main__':
    print("=========================")
    print("STARTING - PROVIDER TESTS")
    print("=========================")
    print("######################################################################")
    unittest.main()
