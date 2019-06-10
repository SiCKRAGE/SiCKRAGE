class ApiError(Exception):
    """
    API Error
    """
    pass


class ApiUnauthorized(ApiError):
    """
    Need JWT Token
    """
    pass
