class APIError(Exception):
    """
    API Error
    """

    def __init__(self, status, message, response):
        self._status = status
        self._message = message
        self._response = response

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message

    @property
    def response(self):
        return self._response

    def __unicode__(self):
        return self.__class__.__name__ + ': ' + self.message

    def __repr__(self):
        return self.__unicode__()


class APIResourceDoesNotExist(APIError):
    """Custom exception when resource is not found."""
    pass


class APIUnauthorized(APIError):
    """Need JWT Token"""
    pass


class APITokenExpired(APIError):
    """JWT Token Expired"""
    pass
