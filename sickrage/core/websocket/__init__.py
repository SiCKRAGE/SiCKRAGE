import json
from queue import Queue

from jose import JWTError, ExpiredSignatureError
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler

import sickrage

clients = set()
message_queue = Queue()


class WebSocketUIHandler(WebSocketHandler):
    """WebSocket handler to send and receive data to and from a web client."""

    def check_origin(self, origin):
        """Allow alternate origins."""
        return True

    def open(self, *args, **kwargs):
        """Client connected to the WebSocket."""
        clients.add(self)
        while not message_queue.empty():
            self.write_message(message_queue.get())

    def on_message(self, message):
        """Received a message from the client."""
        json_message = json.loads(message)
        if json_message.get('initial', False):
            certs = sickrage.app.auth_server.certs()
            auth_token = json_message['token']

            try:
                decoded_token = sickrage.app.auth_server.decode_token(auth_token, certs)
                if sickrage.app.config.user.sub_id != decoded_token.get('sub'):
                    clients.remove(self)
                    self.close(401, 'Not Authorized')
            except ExpiredSignatureError:
                clients.remove(self)
                self.close(401, 'Token expired')
            except JWTError as e:
                clients.remove(self)
                self.close(401, f'Improper JWT token supplied, {e!r}')
        else:
            sickrage.app.log.debug('WebSocket received message from {}: {}'.format(self.request.remote_ip, message))

    def data_received(self, chunk):
        """Received a streamed data chunk from the client."""
        super(WebSocketUIHandler, self).data_received(chunk)

    def on_close(self):
        """Client disconnected from the WebSocket."""
        clients.remove(self)

    def __repr__(self):
        """Client representation."""
        return '<{} Client: {}>'.format(type(self).__name__, self.request.remote_ip)


class WebSocketMessage(object):
    """Represents a WebSocket message."""

    def __init__(self, message_type, data):
        """
        Construct a new WebSocket message.
        :param message_type: A string representing the type of message (e.g. notification)
        :param data: A JSON-serializable object containing the message data.
        """
        self.type = message_type
        self.data = data

    @property
    def content(self):
        """Get the message content."""
        return {
            'type': self.type,
            'data': self.data
        }

    def json(self):
        """Return the message content as a JSON-serialized string."""
        return json.dumps(self.content)

    def push(self):
        """Push the message to all connected WebSocket clients."""
        # message_queue.put(self.json())
        for client in clients.copy():
            try:
                message = self.json()
                IOLoop.current().run_in_executor(None, client.write_message, message)
            except AssertionError:
                continue
