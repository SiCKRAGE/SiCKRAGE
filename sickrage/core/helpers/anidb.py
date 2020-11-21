import adba
import sickrage
from adba import AniDBCommandTimeoutError
from sickrage.core.exceptions import AnidbAdbaConnectionException


def set_up_anidb_connection():
    """Connect to anidb."""
    if not sickrage.app.config.anidb.enable:
        sickrage.app.log.debug('Usage of AniDB disabled. Skipping')
        return False

    if not sickrage.app.config.anidb.username and not sickrage.app.config.anidb.password:
        sickrage.app.log.debug('AniDB username and/or password are not set. Aborting anidb lookup.')
        return False

    if not sickrage.app.adba_connection:
        try:
            sickrage.app.adba_connection = adba.Connection(keepAlive=True)
        except Exception as error:
            sickrage.app.log.warning('AniDB exception msg: {0!r}'.format(error))
            return False

    try:
        if not sickrage.app.adba_connection.authed():
            sickrage.app.adba_connection.auth(sickrage.app.config.anidb.username, sickrage.app.config.anidb.password)
        else:
            return True
    except Exception as error:
        sickrage.app.log.warning('AniDB exception msg: {0!r}'.format(error))
        return False

    return sickrage.app.adba_connection.authed()


def get_release_groups_for_anime(series_name):
    """Get release groups for an anidb anime."""
    groups = []

    if set_up_anidb_connection():
        try:
            anime = adba.Anime(sickrage.app.adba_connection, name=series_name)
            groups = anime.get_groups()
        except Exception as error:
            sickrage.app.log.warning('Unable to retrieve Fansub Groups from AniDB. Error: {}'.format(error))
            raise AnidbAdbaConnectionException(error)

    return groups


def get_short_group_name(release_group):
    short_group_list = []

    try:
        group = sickrage.app.adba_connection.group(gname=release_group)
    except AniDBCommandTimeoutError:
        sickrage.app.log.debug('Timeout while loading group from AniDB. Trying next group')
    except Exception:
        sickrage.app.log.debug('Failed while loading group from AniDB. Trying next group')
    else:
        for line in group.datalines:
            if line['shortname']:
                short_group_list.append(line['shortname'])
            else:
                if release_group not in short_group_list:
                    short_group_list.append(release_group)

    return short_group_list


def short_group_names(groups):
    """
    Find AniDB short group names for release groups

    :param groups: list of groups to find short group names for
    :return: list of shortened group names
    """
    groups = groups.split(",")
    short_group_list = []

    if set_up_anidb_connection():
        for group_name in groups:
            short_group_list += get_short_group_name(group_name) or [group_name]
    else:
        short_group_list = groups

    return short_group_list


def get_anime_episode(file_path):
    """
    Look up anidb properties for an episode

    :param file_path: file to check
    :return: episode object
    """
    ep = None

    if set_up_anidb_connection():
        ep = adba.Episode(sickrage.app.adba_connection, filePath=file_path,
                          paramsF=[
                              "quality",
                              "anidb_file_name",
                              "crc32"
                          ],
                          paramsA=[
                              "epno",
                              "english_name",
                              "short_name_list",
                              "other_name",
                              "synonym_list"
                          ])

    return ep
