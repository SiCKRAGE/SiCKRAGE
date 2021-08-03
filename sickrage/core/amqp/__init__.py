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
import ssl
from ssl import SSLCertVerificationError

import pika
from google.protobuf.json_format import MessageToDict
from pika.adapters.tornado_connection import TornadoConnection
from pika.adapters.utils.connection_workflow import AMQPConnectorException
from pika.exceptions import StreamLostError, AMQPConnectionError
from tornado.ioloop import IOLoop

import sickrage
from sickrage.protos.announcement_v1_pb2 import CreatedAnnouncementResponse, DeletedAnnouncementResponse
from sickrage.protos.network_timezone_v1_pb2 import SavedNetworkTimezoneResponse, DeletedNetworkTimezoneResponse
from sickrage.protos.search_provider_url_v1_pb2 import SavedSearchProviderUrlResponse
from sickrage.protos.server_certificate_v1_pb2 import SavedServerCertificateResponse
from sickrage.protos.updates_v1_pb2 import UpdatedAppResponse


class AMQPClient(object):
    def __init__(self):
        self._name = 'AMQP'
        self._amqp_host = 'rmq.sickrage.ca'
        self._amqp_port = 5671
        self._amqp_vhost = 'sickrage-app'
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._prefetch_count = 100

        IOLoop.current().add_callback(self.connect)

    @property
    def events(self):
        return {
            'server_ssl_certificate.saved': {
                'event_type': SavedServerCertificateResponse(),
                'event_cmd': sickrage.app.wserver.load_ssl_certificate,
            },
            'network_timezone.saved': {
                'event_type': SavedNetworkTimezoneResponse(),
                'event_cmd': sickrage.app.tz_updater.update_network_timezone,
            },
            'network_timezone.deleted': {
                'event_type': DeletedNetworkTimezoneResponse(),
                'event_cmd': sickrage.app.tz_updater.delete_network_timezone,
            },
            'search_provider_url.saved': {
                'event_type': SavedSearchProviderUrlResponse(),
                'event_cmd': sickrage.app.search_providers.update_url,
            },
            'app.updated': {
                'event_type': UpdatedAppResponse(),
                'event_cmd': sickrage.app.version_updater.task,
            },
            'announcement.created': {
                'event_type': CreatedAnnouncementResponse(),
                'event_cmd': sickrage.app.announcements.add,
            },
            'announcement.deleted': {
                'event_type': DeletedAnnouncementResponse(),
                'event_cmd': sickrage.app.announcements.clear,
            },
        }

    def connect(self):
        if not sickrage.app.api.token or not sickrage.app.config.general.server_id:
            IOLoop.current().call_later(5, self.reconnect)
            return

        if sickrage.app.api.token_time_remaining < (int(sickrage.app.api.token['expires_in']) / 2):
            if not sickrage.app.api.refresh_token():
                IOLoop.current().call_later(5, self.reconnect)
                return

        try:
            credentials = pika.credentials.PlainCredentials(username='sickrage', password=sickrage.app.api.token["access_token"])

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            parameters = pika.ConnectionParameters(
                host=self._amqp_host,
                port=self._amqp_port,
                virtual_host=self._amqp_vhost,
                credentials=credentials,
                socket_timeout=300,
                ssl_options=pika.SSLOptions(context)
            )

            TornadoConnection(
                parameters,
                on_open_callback=self.on_connection_open,
                on_close_callback=self.on_connection_close,
                on_open_error_callback=self.on_connection_open_error
            )
        except (AMQPConnectorException, AMQPConnectionError, SSLCertVerificationError):
            sickrage.app.log.debug("AMQP connection error, attempting to reconnect")
            IOLoop.current().call_later(5, self.reconnect)

    def disconnect(self):
        if self._channel and not self._channel.is_closed:
            try:
                self._channel.close()
            except StreamLostError:
                pass

        if self._connection and not self._connection.is_closed:
            try:
                self._connection.close()
            except StreamLostError:
                pass

        self._channel = None
        self._connection = None

    def on_connection_close(self, connection, reason):
        if not self._closing:
            sickrage.app.log.debug("AMQP connection closed, attempting to reconnect")
            IOLoop.current().call_later(5, self.reconnect)

    def on_connection_open(self, connection):
        self._connection = connection
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, connection, reason):
        sickrage.app.log.debug("AMQP connection open failed, attempting to reconnect")
        IOLoop.current().call_later(5, self.reconnect)

    def reconnect(self):
        if not self._closing:
            self.disconnect()
            self.connect()

    def on_channel_open(self, channel):
        self._channel = channel
        self._channel.basic_qos(callback=self.on_qos_applied, prefetch_count=self._prefetch_count)

    def on_qos_applied(self, method):
        self.start_consuming()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        try:
            if basic_deliver.exchange in self.events:
                event = self.events[basic_deliver.exchange]

                message = event['event_type']
                message.ParseFromString(body)
                message_kwargs = MessageToDict(message, including_default_value_fields=True, preserving_proto_field_name=True)

                sickrage.app.log.debug(
                    f"Received AMQP response: {basic_deliver.exchange} :: {message_kwargs!r}"
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

    def stop(self):
        self._closing = True
        self.disconnect()
