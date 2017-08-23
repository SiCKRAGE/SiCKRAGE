from __future__ import absolute_import, division, print_function

from trakt.interfaces import auth
from trakt.interfaces import calendars
from trakt.interfaces import movies
from trakt.interfaces import oauth
from trakt.interfaces import scrobble
from trakt.interfaces import search
from trakt.interfaces import shows
from trakt.interfaces import sync
from trakt.interfaces import users

INTERFACES = [
    # /
    auth.AuthInterface,
    oauth.OAuthInterface,
    oauth.DeviceOAuthInterface,
    oauth.PinOAuthInterface,

    scrobble.ScrobbleInterface,
    search.SearchInterface,

    # /calendars/
    calendars.AllCalendarsInterface,
    calendars.MyCalendarsInterface,

    # /sync/
    sync.SyncInterface,
    sync.SyncCollectionInterface,
    sync.SyncHistoryInterface,
    sync.SyncPlaybackInterface,
    sync.SyncRatingsInterface,
    sync.SyncWatchedInterface,
    sync.SyncWatchlistInterface,

    # /shows/
    shows.ShowsInterface,

    # /movies/
    movies.MoviesInterface,

    # /users/
    users.UsersInterface,
    users.UsersSettingsInterface,

    # /users/lists/
    users.UsersListsInterface,
    users.UsersListInterface
]


def get_interfaces():
    for interface in INTERFACES:
        if not interface.path:
            continue

        path = interface.path.strip('/')

        if path:
            path = path.split('/')
        else:
            path = []

        yield path, interface


def construct_map(client, d=None, interfaces=None):
    if d is None:
        d = {}

    if interfaces is None:
        interfaces = get_interfaces()

    for path, interface in interfaces:
        if len(path) == 0:
            continue

        key = path.pop(0)

        if len(path) == 0:
            d[key] = interface(client)
            continue

        value = d.get(key, {})

        if type(value) is not dict:
            value = {None: value}

        construct_map(client, value, [(path, interface)])

        d[key] = value

    return d
