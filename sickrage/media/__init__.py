from __future__ import unicode_literals

__all__ = ['ShowBanner', 'ShowFanArt', 'ShowNetworkLogo', 'ShowPoster']

from tornado.escape import url_escape
from ShowPoster import ShowPoster
from ShowFanArt import ShowFanArt
from ShowBanner import ShowBanner
from ShowNetworkLogo import ShowNetworkLogo

def showImage(show=None, which=None):
    media = None
    media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]

    try:
        if which[0:6] == 'banner':
            media = ShowBanner(show, media_format)
        elif which[0:6] == 'fanart':
            media = ShowFanArt(show, media_format)
        elif which[0:6] == 'poster':
            media = ShowPoster(show, media_format)
        elif which[0:7] == 'network':
            media = ShowNetworkLogo(show, media_format)

        static_url = url_escape(media.get_media, False)
        return static_url
    except:pass
