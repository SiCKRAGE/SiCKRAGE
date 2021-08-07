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

from google.protobuf.json_format import MessageToDict
from tornado.ioloop import IOLoop

import sickrage
from sickrage.core.amqp import AMQPBase
from sickrage.protos.announcement_v1_pb2 import CreatedAnnouncementResponse, DeletedAnnouncementResponse
from sickrage.protos.network_timezone_v1_pb2 import SavedNetworkTimezoneResponse, DeletedNetworkTimezoneResponse
from sickrage.protos.search_provider_url_v1_pb2 import SavedSearchProviderUrlResponse
from sickrage.protos.server_certificate_v1_pb2 import SavedServerCertificateResponse
from sickrage.protos.updates_v1_pb2 import UpdatedAppResponse


class AMQPConsumer(AMQPBase):
    def __init__(self):
        super(AMQPConsumer, self).__init__()

    @property
    def events(self):
        return {
            'server_ssl_certificate.saved': {
                'event_msg': SavedServerCertificateResponse(),
                'event_cmd': sickrage.app.wserver.load_ssl_certificate,
            },
            'network_timezone.saved': {
                'event_msg': SavedNetworkTimezoneResponse(),
                'event_cmd': sickrage.app.tz_updater.update_network_timezone,
            },
            'network_timezone.deleted': {
                'event_msg': DeletedNetworkTimezoneResponse(),
                'event_cmd': sickrage.app.tz_updater.delete_network_timezone,
            },
            'search_provider_url.saved': {
                'event_msg': SavedSearchProviderUrlResponse(),
                'event_cmd': sickrage.app.search_providers.update_url,
            },
            'app.updated': {
                'event_msg': UpdatedAppResponse(),
                'event_cmd': sickrage.app.version_updater.task,
            },
            'announcement.created': {
                'event_msg': CreatedAnnouncementResponse(),
                'event_cmd': sickrage.app.announcements.add,
            },
            'announcement.deleted': {
                'event_msg': DeletedAnnouncementResponse(),
                'event_cmd': sickrage.app.announcements.clear,
            },
        }

    def on_channel_open(self, channel):
        self._channel = channel
        self._channel.basic_qos(callback=self.on_qos_applied, prefetch_count=self._prefetch_count)

    def on_qos_applied(self, method):
        self.start_consuming()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        try:
            if basic_deliver.exchange in self.events:
                event = self.events[basic_deliver.exchange]

                message = event['event_msg']
                message.ParseFromString(body)
                message_kwargs = MessageToDict(message, including_default_value_fields=True, preserving_proto_field_name=True)

                sickrage.app.log.debug(
                    f"Received AMQP event: {basic_deliver.exchange} :: {message_kwargs!r}"
                )

                IOLoop.current().spawn_callback(event['event_cmd'], **message_kwargs)
        except Exception as e:
            sickrage.app.log.debug(f"AMQP exchange: {basic_deliver.exchange} message caused an exception: {e!r}")
        finally:
            self._channel.basic_ack(basic_deliver.delivery_tag)

    def start_consuming(self):
        sickrage.app.log.info('Connected to SiCKRAGE AMQP server')

        try:
            self._consumer_tag = self._channel.basic_consume(
                on_message_callback=self.on_message,
                queue=f'{sickrage.app.config.user.sub_id}.{sickrage.app.config.general.server_id}',
            )
        except Exception as e:
            sickrage.app.log.debug(f'Exception happened during consuming AMQP messages: {e!r}')
            IOLoop.current().call_later(5, self.reconnect)
