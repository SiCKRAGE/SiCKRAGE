# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import urllib
import datetime

from sickbeard import db
import logging
from sickbeard.common import Quality
from sickbeard.common import WANTED, FAILED
from sickrage.helper.encoding import ss
from sickrage.helper.exceptions import EpisodeNotFoundException, ex
from sickrage.show.History import History


def prepareFailedName(release):
    """Standardizes release name for failed DB"""

    fixed = urllib.unquote(release)
    if fixed.endswith(".nzb"):
        fixed = fixed.rpartition(".")[0]

    fixed = re.sub("[\.\-\+\ ]", "_", fixed)
    fixed = ss(fixed)

    return fixed


def logFailed(release):
    log_str = ""
    size = -1
    provider = ""

    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select("SELECT * FROM history WHERE RELEASE=?", [release])

    if len(sql_results) == 0:
        logging.warning(
                "Release not found in snatch history.")
    elif len(sql_results) > 1:
        logging.warning("Multiple logged snatches found for release")
        sizes = len(set(x[b"size"] for x in sql_results))
        providers = len(set(x[b"provider"] for x in sql_results))
        if sizes == 1:
            logging.warning("However, they're all the same size. Continuing with found size.")
            size = sql_results[0][b"size"]
        else:
            logging.warning(
                    "They also vary in size. Deleting the logged snatches and recording this release with no size/provider")
            for result in sql_results:
                deleteLoggedSnatch(result[b"release"], result[b"size"], result[b"provider"])

        if providers == 1:
            logging.info("They're also from the same provider. Using it as well.")
            provider = sql_results[0][b"provider"]
    else:
        size = sql_results[0][b"size"]
        provider = sql_results[0][b"provider"]

    if not hasFailed(release, size, provider):
        myDB = db.DBConnection('failed.db')
        myDB.action("INSERT INTO failed (release, size, provider) VALUES (?, ?, ?)", [release, size, provider])

    deleteLoggedSnatch(release, size, provider)

    return log_str


def logSuccess(release):
    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE RELEASE=?", [release])


def hasFailed(release, size, provider="%"):
    """
    Returns True if a release has previously failed.

    If provider is given, return True only if the release is found
    with that specific provider. Otherwise, return True if the release
    is found with any provider.

    :param release: Release name to record failure
    :param size: Size of release
    :param provider: Specific provider to search (defaults to all providers)
    :return: True if a release has previously failed.
    """

    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select(
            "SELECT * FROM failed WHERE RELEASE=? AND size=? AND provider LIKE ?",
            [release, size, provider])

    return (len(sql_results) > 0)


def revertEpisode(epObj):
    """Restore the episodes of a failed download to their original state"""
    myDB = db.DBConnection('failed.db')
    sql_results = myDB.select("SELECT * FROM history WHERE showid=? AND season=?",
                              [epObj.show.indexerid, epObj.season])

    history_eps = dict([(res[b"episode"], res) for res in sql_results])

    try:
        logging.info("Reverting episode (%s, %s): %s" % (epObj.season, epObj.episode, epObj.name))
        with epObj.lock:
            if epObj.episode in history_eps:
                logging.info("Found in history")
                epObj.status = history_eps[epObj.episode][b'old_status']
            else:
                logging.warning("WARNING: Episode not found in history. Setting it back to WANTED")
                epObj.status = WANTED
                epObj.saveToDB()

    except EpisodeNotFoundException as e:
        logging.warning("Unable to create episode, please set its status manually: {}".format(ex(e)))


def markFailed(epObj):
    """
    Mark an episode as failed

    :param epObj: Episode object to mark as failed
    :return: empty string
    """
    log_str = ""

    try:
        with epObj.lock:
            quality = Quality.splitCompositeStatus(epObj.status)[1]
            epObj.status = Quality.compositeStatus(FAILED, quality)
            epObj.saveToDB()

    except EpisodeNotFoundException as e:
        logging.warning("Unable to get episode, please set its status manually: {}".format(ex(e)))

    return log_str


def logSnatch(searchResult):
    """
    Logs a successful snatch

    :param searchResult: Search result that was successful
    """
    logDate = datetime.datetime.today().strftime(History.date_format)
    release = prepareFailedName(searchResult.name)

    providerClass = searchResult.provider
    if providerClass is not None:
        provider = providerClass.name
    else:
        provider = "unknown"

    show_obj = searchResult.episodes[0].show

    myDB = db.DBConnection('failed.db')
    for episode in searchResult.episodes:
        myDB.action(
                "INSERT INTO history (date, size, release, provider, showid, season, episode, old_status)"
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [logDate, searchResult.size, release, provider, show_obj.indexerid, episode.season, episode.episode,
                 episode.status])


def deleteLoggedSnatch(release, size, provider):
    """
    Remove a snatch from history

    :param release: release to delete
    :param size: Size of release
    :param provider: Provider to delete it from
    """
    release = prepareFailedName(release)

    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE RELEASE=? AND size=? AND provider=?",
                [release, size, provider])


def trimHistory():
    """Trims history table to 1 month of history from today"""
    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE date < " + str(
            (datetime.datetime.today() - datetime.timedelta(days=30)).strftime(History.date_format)))


def findRelease(epObj):
    """
    Find releases in history by show ID and season.
    Return None for release if multiple found or no release found.
    """

    release = None
    provider = None

    # Clear old snatches for this release if any exist
    myDB = db.DBConnection('failed.db')
    myDB.action("DELETE FROM history WHERE showid=" + str(epObj.show.indexerid) + " AND season=" + str(
            epObj.season) + " AND episode=" + str(
            epObj.episode) + " AND date < (SELECT max(date) FROM history WHERE showid=" + str(
            epObj.show.indexerid) + " AND season=" + str(epObj.season) + " AND episode=" + str(epObj.episode) + ")")

    # Search for release in snatch history
    results = myDB.select("SELECT RELEASE, provider, DATE FROM history WHERE showid=? AND season=? AND episode=?",
                          [epObj.show.indexerid, epObj.season, epObj.episode])

    for result in results:
        release = str(result[b"release"])
        provider = str(result[b"provider"])
        date = result[b"date"]

        # Clear any incomplete snatch records for this release if any exist
        myDB.action("DELETE FROM history WHERE RELEASE=? AND DATE!=?", [release, date])

        # Found a previously failed release
        logging.debug("Failed release found for season (%s): (%s)" % (epObj.season, result[b"release"]))
        return (release, provider)

    # Release was not found
    logging.debug("No releases found for season (%s) of (%s)" % (epObj.season, epObj.show.indexerid))
    return (release, provider)
