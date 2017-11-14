from sickrage.core.exceptions import SickRageException


class error(SickRageException):
    """
    API Error
    """
    pass


class unauthorized(SickRageException):
    """
    Need JWT Token
    """
    pass
