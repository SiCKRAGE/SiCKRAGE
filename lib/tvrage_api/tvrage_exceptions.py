#!/usr/bin/env python2
#encoding:utf-8
#author:echel0n
#project:tvrage_api
#repository:http://github.com/echel0n/tvrage_api
#license:unlicense (http://unlicense.org/)

"""Custom exceptions used or raised by tvrage_api"""

__author__ = "echel0n"
__version__ = "1.0"

__all__ = ["tvrage_error", "tvrage_userabort", "tvrage_shownotfound",
"tvrage_seasonnotfound", "tvrage_episodenotfound", "tvrage_attributenotfound"]

class tvrage_exception(Exception):
    """Any exception generated by tvrage_api
    """
    pass

class tvrage_error(tvrage_exception):
    """An error with tvrage.com (Cannot connect, for example)
    """
    pass

class tvrage_userabort(tvrage_exception):
    """User aborted the interactive selection (via
    the q command, ^c etc)
    """
    pass

class tvrage_shownotfound(tvrage_exception):
    """Show cannot be found on tvrage.com (non-existant show)
    """
    pass

class tvrage_seasonnotfound(tvrage_exception):
    """Season cannot be found on tvrage.com
    """
    pass

class tvrage_episodenotfound(tvrage_exception):
    """Episode cannot be found on tvrage.com
    """
    pass

class tvrage_attributenotfound(tvrage_exception):
    """Raised if an episode does not have the requested
    attribute (such as a episode name)
    """
    pass
