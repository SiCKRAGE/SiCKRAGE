# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re
from xml.etree import ElementTree

import sickrage
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websession import WebSession
from sickrage.search_providers import NZBDataSearchProviderResult


def getSeasonNZBs(name, urlData, season):
    """
    Split a season NZB into episodes

    :param name: NZB name
    :param urlData: URL to get data from
    :param season: Season to check
    :return: dict of (episode files, xml matches)
    """
    try:
        nzbElement = ElementTree.fromstring(urlData)
    except SyntaxError:
        sickrage.app.log.error("Unable to parse the XML of " + name + ", not splitting it")
        return {}, ''

    filename = name.replace(".nzb", "")

    regex = '([\w\._\ ]+)[\. ]S%02d[\. ]([\w\._\-\ ]+)[\- ]([\w_\-\ ]+?)' % season

    sceneNameMatch = re.search(regex, filename, re.I)
    if sceneNameMatch:
        showName, qualitySection, groupName = sceneNameMatch.groups()
    else:
        sickrage.app.log.error("Unable to parse " + name + " into a scene name. If it's a valid, log a bug.")
        return {}, ''

    regex = '(' + re.escape(showName) + '\.S%02d(?:[E0-9]+)\.[\w\._]+\-\w+' % season + ')'
    regex = regex.replace(' ', '.')

    epFiles = {}
    xmlns = None

    for curFile in nzbElement.getchildren():
        xmlnsMatch = re.match("{(http://[A-Za-z0-9_./]+/nzb)\}file", curFile.tag)
        if not xmlnsMatch:
            continue
        else:
            xmlns = xmlnsMatch.group(1)
        match = re.search(regex, curFile.get("subject"), re.I)
        if not match:
            # print curFile.get("subject"), "doesn't match", regex
            continue
        curEp = match.group(1)
        if curEp not in epFiles:
            epFiles[curEp] = [curFile]
        else:
            epFiles[curEp].append(curFile)

    return epFiles, xmlns


def createNZBString(fileElements, xmlns):
    rootElement = ElementTree.Element("nzb")
    if xmlns:
        rootElement.set("xmlns", xmlns)

    for curFile in fileElements:
        rootElement.append(stripNS(curFile, xmlns))

    return ElementTree.tostring(rootElement)


def saveNZB(nzbName, nzbString):
    """
    Save NZB to disk

    :param nzbName: Filename/path to write to
    :param nzbString: Content to write in file
    """
    try:
        with open(nzbName + ".nzb", 'w') as nzb_fh:
            nzb_fh.write(nzbString)

    except EnvironmentError as e:
        sickrage.app.log.warning("Unable to save NZB: {}".format(e))


def stripNS(element, ns):
    element.tag = element.tag.replace("{" + ns + "}", "")
    for curChild in element.getchildren():
        stripNS(curChild, ns)

    return element


def split_nzb_result(result):
    """
    Split result into separate episodes

    :param result: search result object
    :return: False upon failure, a list of episode objects otherwise
    """
    try:
        url_data = WebSession().get(result.url, needBytes=True).text
    except Exception:
        sickrage.app.log.error("Unable to load url " + result.url + ", can't download season NZB")
        return False

    # parse the season ep name
    try:
        parse_result = NameParser(False, series_id=result.series_id, series_provider_id=result.series_provider_id).parse(result.name)
    except InvalidNameException:
        sickrage.app.log.debug("Unable to parse the filename " + result.name + " into a valid episode")
        return False
    except InvalidShowException:
        sickrage.app.log.debug("Unable to parse the filename " + result.name + " into a valid show")
        return False

    # bust it up
    season = parse_result.season_number if parse_result.season_number is not None else 1
    separate_nzbs, xmlns = getSeasonNZBs(result.name, url_data, season)

    result_list = []
    for newNZB in separate_nzbs:
        sickrage.app.log.debug("Split out {} from {}".format(newNZB, result.name))

        # parse the name
        try:
            parse_result = NameParser(False, series_id=result.series_id, series_provider_id=result.series_provider_id).parse(newNZB)
        except InvalidNameException:
            sickrage.app.log.debug("Unable to parse the filename {} into a valid episode".format(newNZB))
            return False
        except InvalidShowException:
            sickrage.app.log.debug("Unable to parse the filename {} into a valid show".format(newNZB))
            return False

        # make sure the result is sane
        if (parse_result.season_number is not None and parse_result.season_number != season) or (parse_result.season_number is None and season != 1):
            sickrage.app.log.warning("Found {} inside {} but it doesn't seem to belong to the same season, ignoring it".format(newNZB, result.name))
            continue
        elif len(parse_result.episode_numbers) == 0:
            sickrage.app.log.warning("Found {} inside {} but it doesn't seem to be a valid episode NZB, ignoring it".format(newNZB, result.name))
            continue

        want_ep = True
        for epNo in parse_result.episode_numbers:
            show_object = find_show(parse_result.series_id, parse_result.series_provider_id)
            if not show_object.want_episode(parse_result.season_number, epNo, result.quality):
                sickrage.app.log.info("Ignoring result {} because we don't want an episode that is {}".format(newNZB, result.quality.display_name))
                want_ep = False
                break

        if not want_ep:
            continue

        # make a result
        cur_result = NZBDataSearchProviderResult(season, parse_result.episode_numbers)
        cur_result.name = newNZB
        cur_result.provider = result.provider
        cur_result.quality = result.quality
        cur_result.extraInfo = [createNZBString(separate_nzbs[newNZB], xmlns)]

        result_list.append(cur_result)

    return result_list
