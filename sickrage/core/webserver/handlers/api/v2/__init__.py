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
import json
import os
import traceback
from abc import ABC

import sickrage
from sickrage.core import WANTED, SKIPPED
from sickrage.core.common import statusStrings, UNKNOWN, UNAIRED, SNATCHED, DOWNLOADED, ARCHIVED, IGNORED, SNATCHED_PROPER, SUBTITLED, FAILED, SNATCHED_BEST, \
    MISSED, Overview, SearchFormats, qualityPresetStrings, Quality
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.indexers import IndexerApi


class APIv2BaseHandler(BaseHandler, ABC):
    def prepare(self):
        super(APIv2BaseHandler, self).prepare()

        method_name = self.request.method.lower()
        if method_name == 'options':
            return

        certs = sickrage.app.auth_server.certs()
        auth_header = self.request.headers.get('Authorization')

        if auth_header:
            if 'bearer' in auth_header.lower():
                try:
                    token = auth_header.strip('Bearer').strip()
                    decoded_auth_token = sickrage.app.auth_server.decode_token(token, certs)

                    if not sickrage.app.config.sub_id:
                        sickrage.app.config.sub_id = decoded_auth_token.get('sub')
                        sickrage.app.config.save()

                    if sickrage.app.config.sub_id != decoded_auth_token.get('sub'):
                        return self.send_error(401, error='user is not authorized')

                    if sickrage.app.config.enable_sickrage_api and not sickrage.app.api.token:
                        sickrage.app.api.exchange_token(token)

                    # internal_connections = "{}://{}:{}{}".format(self.request.protocol,
                    #                                              get_internal_ip(),
                    #                                              sickrage.app.config.web_port,
                    #                                              sickrage.app.config.web_root)
                    #
                    # external_connections = "{}://{}:{}{}".format(self.request.protocol,
                    #                                              get_external_ip(),
                    #                                              sickrage.app.config.web_port,
                    #                                              sickrage.app.config.web_root)
                    #
                    # connections = ','.join([internal_connections, external_connections])
                    #
                    # if not re.match(r'[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}', sickrage.app.config.server_id or ""):
                    #     server_id = sickrage.app.api.account.register_server(connections)
                    #     if server_id:
                    #         sickrage.app.config.server_id = server_id
                    #         sickrage.app.config.save()
                    # else:
                    #     sickrage.app.api.account.update_server(sickrage.app.config.server_id, connections)

                    self.current_user = decoded_auth_token
                except Exception:
                    return self.send_error(401, error='failed to decode token')
            else:
                return self.send_error(401, error='invalid authorization request')
        else:
            return self.send_error(401, error='authorization header missing')

    def get_current_user(self):
        return self.current_user

    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)

        if status_code == 500:
            excp = kwargs['exc_info'][1]
            tb = kwargs['exc_info'][2]
            stack = traceback.extract_tb(tb)
            clean_stack = [i for i in stack if i[0][-6:] != 'gen.py' and i[0][-13:] != 'concurrent.py']
            error_msg = '{}\n  Exception: {}'.format(''.join(traceback.format_list(clean_stack)), excp)

            sickrage.app.log.debug(error_msg)
        else:
            error_msg = kwargs.get('reason', '')

        self.write_json({'error': error_msg})

    def set_default_headers(self):
        super(APIv2BaseHandler, self).set_default_headers()
        self.set_header('Content-Type', 'application/json')

    def write_json(self, response):
        self.write(json.dumps(response))


class PingHandler(APIv2BaseHandler, ABC):
    def get(self, *args, **kwargs):
        return self.write_json({'message': 'pong'})


class ConfigStateHandler(APIv2BaseHandler, ABC):
    def get(self, *args, **kwargs):
        config_data = sickrage.app.config.config_data
        config_data['constants'] = {
            'episode_status_strings': statusStrings,
            'episode_status_keys': {
                'UNKNOWN': UNKNOWN,
                'UNAIRED': UNAIRED,
                'SNATCHED': SNATCHED,
                'WANTED': WANTED,
                'DOWNLOADED': DOWNLOADED,
                'SKIPPED': SKIPPED,
                'ARCHIVED': ARCHIVED,
                'IGNORED': IGNORED,
                'SNATCHED_PROPER': SNATCHED_PROPER,
                'SUBTITLED': SUBTITLED,
                'FAILED': FAILED,
                'SNATCHED_BEST': SNATCHED_BEST,
                'MISSED': MISSED
            },
            'overview_strings': Overview.overviewStrings,
            'show_search_formats': SearchFormats.search_format_strings,
            'qualities': {
                'presets': qualityPresetStrings,
                'strings': Quality.qualityStrings,
                'combined': Quality.combinedQualityStrings,
                'css': Quality.cssClassStrings,
                'snatched': Quality.SNATCHED,
                'downloaded': Quality.DOWNLOADED
            }
        }

        return self.write_json(config_data)


class RetrieveSeriesMetadataHandler(APIv2BaseHandler, ABC):
    def get(self):
        series_directory = self.get_argument('seriesDirectory', None)
        if not series_directory:
            return self.send_error(400, error="Missing seriesDirectory parameter")

        json_data = {
            'rootDirectory': os.path.dirname(series_directory),
            'seriesDirectory': series_directory,
            'seriesId': '',
            'seriesName': '',
            'indexerSlug': ''
        }

        for cur_provider in sickrage.app.metadata_providers.values():
            series_id, series_name, indexer = cur_provider.retrieve_show_metadata(series_directory)

            if not json_data['seriesId'] and series_id:
                json_data['seriesId'] = series_id

            if not json_data['seriesName'] and series_name:
                json_data['seriesName'] = series_name

            if not json_data['indexerSlug'] and indexer:
                json_data['indexerSlug'] = IndexerApi(indexer).slug

        self.write_json(json_data)
