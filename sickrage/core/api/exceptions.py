class ApiError(Exception):
    """
    API Error
    """

    def __init__(self, status, message):
        self._status = status
        self._message = message

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message

    def __unicode__(self):
        return self.__class__.__name__ + ': ' + self.message


class APIResourceDoesNotExist(ApiError):
    """Custom exception when resource is not found."""
    pass


class ApiUnauthorized(ApiError):
    """Need JWT Token"""
    pass
