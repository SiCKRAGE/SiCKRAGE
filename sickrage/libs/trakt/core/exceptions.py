from __future__ import absolute_import, division, print_function

from trakt.core.errors import ERRORS


class RequestFailedError(Exception):
    pass


class RequestError(Exception):
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code if response is not None else None

        self.error = ERRORS.get(self.status_code, ('Unknown', 'Unknown'))

        # Call super class with message
        super(RequestError, self).__init__('%s - "%s"' % self.error)


class ClientError(RequestError):
    pass


class ServerError(RequestError):
    pass
