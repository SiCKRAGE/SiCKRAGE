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


from tornado.escape import json_encode
from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import try_int, checkbox_to_value
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.search_providers import NewznabProvider, TorrentRssProvider, SearchProviderType


class ConfigProvidersHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/providers.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Search Providers'),
                           header=_('Search Providers'),
                           topmenu='config',
                           controller='config',
                           action='providers')


class CanAddNewznabProviderHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        name = self.get_argument('name')

        provider_obj = NewznabProvider(name, '')
        if provider_obj.id not in sickrage.app.search_providers.newznab():
            return self.write(json_encode({'success': provider_obj.id}))
        return self.write(json_encode({'error': 'Provider Name already exists as ' + name}))


class CanAddTorrentRssProviderHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        name = self.get_argument('name')
        url = self.get_argument('url')
        cookies = self.get_argument('cookies')
        title_tag = self.get_argument('titleTAG')

        providerObj = TorrentRssProvider(name, url, cookies, title_tag)
        if providerObj.id not in sickrage.app.search_providers.torrentrss():
            validate = providerObj.validateRSS()
            if validate['result']:
                return self.write(json_encode({'success': providerObj.id}))
            return self.write(json_encode({'error': validate['message']}))
        return self.write(json_encode({'error': 'Provider name already exists as {}'.format(name)}))


class GetNewznabCategoriesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        """
        name = self.get_argument('name')
        url = self.get_argument('url')
        key = self.get_argument('key')

        temp_provider = NewznabProvider(name, url, key)
        success, tv_categories, error = temp_provider.get_newznab_categories()

        return self.write(json_encode({'success': success, 'tv_categories': tv_categories, 'error': error}))


class SaveProvidersHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        results = []

        # custom search providers
        for curProviderStr in self.get_argument('provider_strings', '').split('!!!'):
            if not len(curProviderStr):
                continue

            cur_provider_type, cur_provider_data = curProviderStr.split('|', 1)
            if SearchProviderType(cur_provider_type) == SearchProviderType.NEWZNAB:
                cur_name, cur_url, cur_key, cur_cat = cur_provider_data.split('|')
                provider_obj = NewznabProvider(cur_name, cur_url, cur_key, cur_cat)
                sickrage.app.search_providers.newznab().update(**{provider_obj.id: provider_obj})
            elif SearchProviderType(cur_provider_type) == SearchProviderType.TORRENT_RSS:
                cur_name, cur_url, cur_cookies, cur_title_tag = cur_provider_data.split('|')
                provider_obj = TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)
                sickrage.app.search_providers.torrentrss().update(**{provider_obj.id: provider_obj})

        # remove deleted custom search providers
        for p in sickrage.app.search_providers.all().copy():
            if p not in [x.split(':')[0] for x in self.get_argument('provider_order', '').split('!!!')]:
                provider_obj = sickrage.app.search_providers.all()[p]
                if provider_obj.provider_type in [SearchProviderType.TORRENT_RSS, SearchProviderType.NEWZNAB] and not provider_obj.default:
                    provider_obj.provider_deleted = True

        # enable/disable/sort search providers
        for curProviderIdx, curProviderStr in enumerate(self.get_argument('provider_order', '').split('!!!')):
            cur_provider, cur_enabled = curProviderStr.split(':')
            if cur_provider in sickrage.app.search_providers.all():
                cur_prov_obj = sickrage.app.search_providers.all()[cur_provider]
                cur_prov_obj.sort_order = curProviderIdx
                cur_prov_obj.enabled = bool(try_int(cur_enabled))

        # search provider settings
        for providerID, provider_obj in sickrage.app.search_providers.all().items():
            provider_obj.search_mode = self.get_argument(providerID + '_search_mode', 'eponly').strip()
            provider_obj.search_fallback = checkbox_to_value(self.get_argument(providerID + '_search_fallback', None) or False)
            provider_obj.enable_daily = checkbox_to_value(self.get_argument(providerID + '_enable_daily', None) or False)
            provider_obj.enable_backlog = checkbox_to_value(self.get_argument(providerID + '_enable_backlog', None) or False)
            provider_obj.cookies = self.get_argument(providerID + '_cookies', '').strip().rstrip(';')

            if provider_obj.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS]:
                provider_obj.ratio = int(self.get_argument(providerID + '_ratio', None) or 0)
            elif provider_obj.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB]:
                provider_obj.username = self.get_argument(providerID + '_username', '').strip()
                provider_obj.api_key = self.get_argument(providerID + '_api_key', '').strip()
                provider_obj.key = self.get_argument(providerID + '_key', '').strip()

            custom_settings = {
                'minseed': int(self.get_argument(providerID + '_minseed', None) or 0),
                'minleech': int(self.get_argument(providerID + '_minleech', None) or 0),
                'digest': self.get_argument(providerID + '_digest', '').strip(),
                'hash': self.get_argument(providerID + '_hash', '').strip(),
                'api_key': self.get_argument(providerID + '_api_key', '').strip(),
                'username': self.get_argument(providerID + '_username', '').strip(),
                'password': self.get_argument(providerID + '_password', '').strip(),
                'passkey': self.get_argument(providerID + '_passkey', '').strip(),
                'pin': self.get_argument(providerID + '_pin', '').strip(),
                'confirmed': checkbox_to_value(self.get_argument(providerID + '_confirmed', None) or False),
                'ranked': checkbox_to_value(self.get_argument(providerID + '_ranked', None) or False),
                'engrelease': checkbox_to_value(self.get_argument(providerID + '_engrelease', None) or False),
                'onlyspasearch': checkbox_to_value(self.get_argument(providerID + '_onlyspasearch', None) or False),
                'sorting': self.get_argument(providerID + '_sorting', 'seeders').strip(),
                'freeleech': checkbox_to_value(self.get_argument(providerID + '_freeleech', None) or False),
                'reject_m2ts': checkbox_to_value(self.get_argument(providerID + '_reject_m2ts', None) or False),
                # 'cat': int(self.get_argument(providerID + '_cat', None) or 0),
                'subtitle': checkbox_to_value(self.get_argument(providerID + '_subtitle', None) or False),
                'custom_url': self.get_argument(providerID + '_custom_url', '').strip()
            }

            # update provider object
            provider_obj.custom_settings.update((k, v) for k, v in custom_settings.items() if k in provider_obj.custom_settings)

        # save provider settings
        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[PROVIDERS] Configuration Saved to Database'))

        return self.redirect("/config/providers/")
