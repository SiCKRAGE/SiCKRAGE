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
from abc import ABC

from tornado.escape import json_encode
from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import try_int, checkbox_to_value
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.providers import NewznabProvider, TorrentRssProvider


class ConfigProvidersHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.render('config/providers.mako',
                           submenu=ConfigHandler.menu,
                           title=_('Config - Search Providers'),
                           header=_('Search Providers'),
                           topmenu='config',
                           controller='config',
                           action='providers')


class CanAddNewznabProviderHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        name = self.get_argument('name')

        provider_obj = NewznabProvider(name, '')
        if provider_obj.id not in sickrage.app.search_providers.newznab():
            return self.write(json_encode({'success': provider_obj.id}))
        return self.write(json_encode({'error': 'Provider Name already exists as ' + name}))


class CanAddTorrentRssProviderHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
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


class GetNewznabCategoriesHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
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


class SaveProvidersHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        results = []

        # custom providers
        custom_providers = ''
        for curProviderStr in self.get_argument('provider_strings', '').split('!!!'):
            if not len(curProviderStr):
                continue

            custom_providers += '{}!!!'.format(curProviderStr)
            cur_type, cur_provider_data = curProviderStr.split('|', 1)

            if cur_type == "newznab":
                cur_name, cur_url, cur_key, cur_cat = cur_provider_data.split('|')
                provider_obj = NewznabProvider(cur_name, cur_url, cur_key, cur_cat)
                provider_obj.name = cur_name
                provider_obj.key = cur_key
                provider_obj.catIDs = cur_cat
                sickrage.app.search_providers.newznab().update(**{provider_obj.id: provider_obj})
            elif cur_type == "torrentrss":
                cur_name, cur_url, cur_cookies, cur_title_tag = cur_provider_data.split('|')
                provider_obj = TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)
                provider_obj.name = cur_name
                provider_obj.cookies = cur_cookies
                provider_obj.titleTAG = cur_title_tag
                sickrage.app.search_providers.torrentrss().update(**{provider_obj.id: provider_obj})

        sickrage.app.config.custom_providers = custom_providers

        # remove providers
        for p in list(set(sickrage.app.search_providers.provider_order).difference(
                [x.split(':')[0] for x in self.get_argument('provider_order', '').split('!!!')])):
            provider_obj = sickrage.app.search_providers.all()[p]
            del sickrage.app.search_providers[provider_obj.type][p]

        # enable/disable/sort providers
        sickrage.app.search_providers.provider_order = []
        for curProviderStr in self.get_argument('provider_order', '').split('!!!'):
            cur_provider, cur_enabled = curProviderStr.split(':')
            sickrage.app.search_providers.provider_order += [cur_provider]
            if cur_provider in sickrage.app.search_providers.all():
                cur_prov_obj = sickrage.app.search_providers.all()[cur_provider]
                cur_prov_obj.enabled = bool(try_int(cur_enabled))

        # dynamically load provider settings
        for providerID, provider_obj in sickrage.app.search_providers.all().items():
            try:
                provider_settings = {
                    'minseed': try_int(self.get_argument(providerID + '_minseed', 0)),
                    'minleech': try_int(self.get_argument(providerID + '_minleech', 0)),
                    'ratio': str(self.get_argument(providerID + '_ratio', '')).strip(),
                    'digest': str(self.get_argument(providerID + '_digest', '')).strip(),
                    'hash': str(self.get_argument(providerID + '_hash', '')).strip(),
                    'key': str(self.get_argument(providerID + '_key', '')).strip(),
                    'api_key': str(self.get_argument(providerID + '_api_key', '')).strip(),
                    'username': str(self.get_argument(providerID + '_username', '')).strip(),
                    'password': str(self.get_argument(providerID + '_password', '')).strip(),
                    'passkey': str(self.get_argument(providerID + '_passkey', '')).strip(),
                    'pin': str(self.get_argument(providerID + '_pin', '')).strip(),
                    'confirmed': checkbox_to_value(self.get_argument(providerID + '_confirmed', 0)),
                    'ranked': checkbox_to_value(self.get_argument(providerID + '_ranked', 0)),
                    'engrelease': checkbox_to_value(self.get_argument(providerID + '_engrelease', 0)),
                    'onlyspasearch': checkbox_to_value(self.get_argument(providerID + '_onlyspasearch', 0)),
                    'sorting': str(self.get_argument(providerID + '_sorting', 'seeders')).strip(),
                    'freeleech': checkbox_to_value(self.get_argument(providerID + '_freeleech', 0)),
                    'reject_m2ts': checkbox_to_value(self.get_argument(providerID + '_reject_m2ts', 0)),
                    'search_mode': str(self.get_argument(providerID + '_search_mode', 'eponly')).strip(),
                    'search_fallback': checkbox_to_value(self.get_argument(providerID + '_search_fallback', 0)),
                    'enable_daily': checkbox_to_value(self.get_argument(providerID + '_enable_daily', 0)),
                    'enable_backlog': checkbox_to_value(self.get_argument(providerID + '_enable_backlog', 0)),
                    'cat': try_int(self.get_argument(providerID + '_cat', 0)),
                    'subtitle': checkbox_to_value(self.get_argument(providerID + '_subtitle', 0)),
                    'cookies': str(self.get_argument(providerID + '_cookies', '')).strip().rstrip(';'),
                    'custom_url': str(self.get_argument(providerID + '_custom_url', '')).strip()
                }

                # update provider object
                [setattr(provider_obj, k, v) for k, v in provider_settings.items() if hasattr(provider_obj, k)]
            except Exception as e:
                continue

        # save provider settings
        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[PROVIDERS] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/providers/")
