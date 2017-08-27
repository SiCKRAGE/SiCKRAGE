from __future__ import absolute_import, division, print_function

import calendar
import logging
import time
from datetime import datetime, timedelta
from threading import Thread

import requests
from trakt.core.emitter import Emitter
from trakt.interfaces.base import Interface

log = logging.getLogger(__name__)


class DeviceOAuthInterface(Interface):
    path = 'oauth/device'

    def code(self, **kwargs):
        client_id = self.client.configuration['client.id']

        if not client_id:
            raise ValueError('"client.id" configuration parameter is required')

        response = self.http.post(
            'code',
            data={
                'client_id': client_id
            }
        )

        data = self.get_data(response, **kwargs)

        if isinstance(data, requests.Response):
            return data

        if not data:
            return None

        return data

    def poll(self, device_code, expires_in, interval, **kwargs):
        """Construct the device authentication poller.

        :param device_code: Device authentication code
        :type device_code: str

        :param expires_in: Device authentication code expiry (in seconds)
        :type         in: int

        :param interval: Device authentication poll interval
        :type interval: int

        :rtype: DeviceOAuthPoller
        """
        return DeviceOAuthPoller(self.client, device_code, expires_in, interval)

    def token(self, device_code, **kwargs):
        client_id = self.client.configuration['client.id']
        client_secret = self.client.configuration['client.secret']

        if not client_id:
            raise ValueError('"client.id" and "client.secret" configuration parameters are required')

        response = self.http.post(
            'token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,

                'code': device_code
            }
        )

        data = self.get_data(response, **kwargs)

        if isinstance(data, requests.Response):
            return data

        if not data:
            return None

        return data


class DeviceOAuthPoller(Interface, Emitter):
    def __init__(self, client, device_code, expires_in, interval):
        super(DeviceOAuthPoller, self).__init__(client)

        self.device_code = device_code
        self.expires_in = expires_in
        self.interval = interval

        # Calculate code expiry date/time
        self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)

        # Private attributes
        self._abort = False
        self._active = False
        self._running = False
        self._thread = None

    @property
    def active(self):
        return self._active

    def has_expired(self):
        return datetime.utcnow() > self.expires_at

    def start(self, daemon=None):
        if self._active or self._thread:
            raise Exception('Poller already started')

        # Construct thread process wrapper
        def wrapper():
            try:
                self._process()
            except Exception as ex:
                log.warn('Exception raised in DeviceOAuthPoller: %s', ex, exc_info=True)
            finally:
                self._active = False
                self._running = False

                if self._abort:
                    self.emit('aborted')

        # Construct poller thread
        self._thread = Thread(
            target=wrapper,
            name='%s:%s' % (DeviceOAuthPoller.__module__, DeviceOAuthPoller.__name__)
        )

        # Set `daemon` state
        if daemon is not None:
            self._thread.daemon = daemon

        # Start polling
        self._abort = False
        self._active = True
        self._running = True
        self._thread.start()

    def stop(self):
        # Flag as thread abort
        self._abort = True

        # Flag thread to stop
        self._running = False

    def _process(self):
        while self._running:
            # Ensure code hasn't expired yet
            if self.has_expired():
                self.emit('expired')
                break

            # Trigger "poll" event, check if we should continue polling
            if not self._should_poll():
                self.stop()
                break

            # Poll for token
            response = self.client['oauth/device'].token(self.device_code, parse=False)

            if response:
                # Parse authorization
                data = self.get_data(response)

                if 'created_at' not in data:
                    data['created_at'] = calendar.timegm(datetime.utcnow().utctimetuple())

                # Authentication complete
                self.emit('authenticated', data)
                break

            # Sleep for defined interval
            time.sleep(self.interval)

    def _poll_callback(self, state=True):
        self._abort = not state

    def _should_poll(self):
        # Assume poller should abort if `callback` isn't fired
        self._abort = True

        # Trigger "poll" event
        self.emit('poll', self._poll_callback)

        # Continue polling if `abort` flag isn't set
        return not self._abort
