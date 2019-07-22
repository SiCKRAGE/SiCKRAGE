# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


class SiCKRAGEException(Exception):
    """
    Generic SiCKRAGE Exception - should never be thrown, only sub-classed
    """


class AuthException(SiCKRAGEException):
    """
    Your authentication information are incorrect
    """


class CantRefreshShowException(SiCKRAGEException):
    """
    The show can't be refreshed right now
    """


class CantRemoveShowException(SiCKRAGEException):
    """
    The show can't removed right now
    """


class CantUpdateShowException(SiCKRAGEException):
    """
    The show can't be updated right now
    """


class EpisodeDeletedException(SiCKRAGEException):
    """
    This episode has been deleted
    """


class EpisodeNotFoundException(SiCKRAGEException):
    """
    The episode wasn't found on the Indexer
    """


class EpisodePostProcessingFailedException(SiCKRAGEException):
    """
    The episode post-processing failed
    """


class EpisodeDirectoryNotFoundException(SiCKRAGEException):
    """
    The episode directory was not found
    """


class FailedPostProcessingFailedException(SiCKRAGEException):
    """
    The failed post-processing failed
    """


class MultipleEpisodesInDatabaseException(SiCKRAGEException):
    """
    Multiple episodes were found in the database! The database must be fixed first
    """


class MultipleShowsInDatabaseException(SiCKRAGEException):
    """
    Multiple shows were found in the database! The database must be fixed first
    """


class MultipleShowObjectsException(SiCKRAGEException):
    """
    Multiple objects for the same show were found! Something is very wrong
    """


class NoNFOException(SiCKRAGEException):
    """
    No NFO was found
    """


class ShowNotFoundException(SiCKRAGEException):
    """
    The show wasn't found
    """


class NoFreeSpaceException(SiCKRAGEException):
    """
    No free space left
    """


class AnidbAdbaConnectionException(SiCKRAGEException):
    """
    Connection exceptions raised while trying to communicate with the Anidb UDP api.
    More info on the api: https://wiki.anidb.net/w/API.
    """
