import json

from tornado.websocket import WebSocketHandler, WebSocketClosedError

import sickrage

clients = set()


class WebSocketUIHandler(WebSocketHandler):
    """WebSocket handler to send and receive data to and from a web client."""

    def check_origin(self, origin):
        """Allow alternate origins."""
        return True

    def open(self, *args, **kwargs):
        """Client connected to the WebSocket."""
        clients.add(self)

        for n in sickrage.app.alerts.get_notifications(self.request.remote_ip):
            try:
                self.write_message(WebSocketMessage('notification', n.data).json())
            except WebSocketClosedError:
                pass

    def on_message(self, message):
        """Received a message from the client."""
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

    def __init__(self, event, data):
        """
        Construct a new WebSocket message.
        :param event: A string representing the type of message (e.g. notification)
        :param data: A JSON-serializable object containing the message data.
        """
        self.event = event
        self.data = data

    @property
    def content(self):
        """Get the message content."""
        return {
            'event': self.event,
            'data': self.data
        }

    def json(self):
        """Return the message content as a JSON-serialized string."""
        return json.dumps(self.content)

    def push(self):
        """Push the message to all connected WebSocket clients."""
        if not clients:
            return

        for client in clients:
            sickrage.app.io_loop.add_callback(client.write_message, self.json())
