# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Jonathon Saine <thezoggy@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import io
import os
import re
import threading
import time
import traceback
import urllib

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tornado.concurrent import run_on_executor
from tornado.escape import json_encode, recursive_unicode
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

import sickrage
from core.caches import image_cache
from core.classes import AllShowsListUI
from core.common import ARCHIVED, DOWNLOADED, FAILED, IGNORED, \
    Overview, Quality, SKIPPED, SNATCHED, SNATCHED_PROPER, UNAIRED, UNKNOWN, \
    WANTED, dateFormat, dateTimeFormat, get_quality_string, statusStrings, \
    timeFormat
from core.databases import cache_db, failed_db, main_db
from core.exceptions import CantUpdateShowException, \
    ShowDirectoryNotFoundException
from core.helpers import chmodAsParent, findCertainShow, makeDir, \
    pretty_filesize, sanitizeFileName, srdatetime, tryInt
from core.media.banner import Banner
from core.media.fanart import FanArt
from core.media.network import Network
from core.media.poster import Poster
from core.process_tv import processDir
from core.queues.search import BacklogQueueItem, ManualSearchQueueItem
from core.searchers import subtitle_searcher
from core.tv.show import TVShow
from core.tv.show.coming_episodes import ComingEpisodes
from core.tv.show.history import History
from core.ui import notifications
from core.updaters import tz_updater
from indexers.indexer_exceptions import indexer_error, \
    indexer_showincomplete, indexer_shownotfound

indexer_ids = ["indexerid", "tvdbid"]

RESULT_SUCCESS = 10  # only use inside the run methods
RESULT_FAILURE = 20  # only use inside the run methods
RESULT_TIMEOUT = 30  # not used yet :(
RESULT_ERROR = 40  # only use outside of the run methods !
RESULT_FATAL = 50  # only use in Api.default() ! this is the "we encountered an internal error" error
RESULT_DENIED = 60  # only use in Api.default() ! this is the access denied error

result_type_map = {
    RESULT_SUCCESS: "success",
    RESULT_FAILURE: "failure",
    RESULT_TIMEOUT: "timeout",
    RESULT_ERROR: "error",
    RESULT_FATAL: "fatal",
    RESULT_DENIED: "denied",
}


class KeyHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        super(KeyHandler, self).__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        api_key = None

        try:
            username = sickrage.srConfig.WEB_USERNAME
            password = sickrage.srConfig.WEB_PASSWORD

            if (self.get_argument('u', None) == username or not username) and \
                    (self.get_argument('p', None) == password or not password):
                api_key = sickrage.srConfig.API_KEY

            self.finish({'success': api_key is not None, 'api_key': api_key})
        except Exception:
            sickrage.srLogger.error('Failed doing key request: %s' % (traceback.format_exc()))
            self.finish({'success': False, 'error': 'Failed returning results'})


# basically everything except RESULT_SUCCESS / success is bad
class ApiHandler(RequestHandler):
    """ api class that returns json results """
    version = 5  # use an int since float-point is unpredictable

    def __init__(self, application, request, *args, **kwargs):
        super(ApiHandler, self).__init__(application, request)
        self.io_loop = IOLoop.instance()
        self.executor = ThreadPoolExecutor(50)

    def initialize(self):
        super(ApiHandler, self).initialize()

    @coroutine
    def prepare(self, *args, **kwargs):
        args = args[1:]
        kwargs = {k: (v, ''.join(v))[isinstance(v, list) and len(v) == 1] for k, v in
                  recursive_unicode(self.request.arguments.items())}

        # set the output callback
        # default json
        outputCallbackDict = {
            'default': self._out_as_json,
            'image': self._out_as_image,
        }

        accessMsg = "API :: " + self.request.remote_ip + " - gave correct API KEY. ACCESS GRANTED"
        sickrage.srLogger.debug(accessMsg)

        # set the original call_dispatcher as the local _call_dispatcher
        _call_dispatcher = self.call_dispatcher
        # if profile was set wrap "_call_dispatcher" in the profile function
        if 'profile' in kwargs:
            from profilehooks import profile

            _call_dispatcher = profile(_call_dispatcher, immediate=True)
            del kwargs[b"profile"]

        try:
            outDict = yield self.async_call(_call_dispatcher, *args, **kwargs)
        except Exception as e:  # real internal error oohhh nooo :(
            sickrage.srLogger.error("API :: {}".format(e.message))
            errorData = {
                "error_msg": e,
                "args": args,
                "kwargs": kwargs
            }
            outDict = _responds(RESULT_FATAL, errorData,
                                "SiCKRAGE encountered an internal error! Please report to the Devs")

        if 'outputType' in outDict:
            outputCallback = outputCallbackDict[outDict[b'outputType']]
        else:
            outputCallback = outputCallbackDict[b'default']

        try:
            if not self._finished:
                self.finish(outputCallback(outDict))
        except:
            pass

    @run_on_executor
    def async_call(self, function, *args, **kwargs):
        threading.currentThread().setName("API")
        return recursive_unicode(function(
            **{k: (v, ''.join(v))[isinstance(v, list) and len(v) == 1] for k, v in recursive_unicode(kwargs.items())}))

    def _out_as_image(self, _dict):
        self.set_header('Content-Type', _dict[b'image'].get_media_type())
        return _dict[b'image'].get_media

    def _out_as_json(self, _dict):
        self.set_header("Content-Type", "application/json;charset=UTF-8")
        try:
            out = json_encode(_dict)
            callback = self.get_query_argument('callback', None) or self.get_query_argument('jsonp', None)
            if callback is not None:
                out = callback + '(' + out + ');'  # wrap with JSONP call if requested
        except Exception as e:  # if we fail to generate the output fake an error
            sickrage.srLogger.debug("API :: " + traceback.format_exc())
            out = '{"result": "%s", "message": "error while composing output: %s"}' % \
                  (result_type_map[RESULT_ERROR], e)
        return out

    def call_dispatcher(self, *args, **kwargs):
        """ calls the appropriate CMD class
            looks for a cmd in args and kwargs
            or calls the TVDBShorthandWrapper when the first args element is a number
            or returns an error that there is no such cmd
        """
        sickrage.srLogger.debug("API :: all args: '" + str(args) + "'")
        sickrage.srLogger.debug("API :: all kwargs: '" + str(kwargs) + "'")

        try:
            cmds = kwargs.pop('cmd', args[0] if len(args) else "").split('|') or []
        except Exception as e:
            cmds = []

        outDict = {}
        multiCmds = bool(len(cmds) > 1)
        for cmd in cmds:
            curArgs, curKwargs = self.filter_params(cmd, *args, **kwargs)
            cmdIndex = None
            if len(cmd.split("_")) > 1:  # was a index used for this cmd ?
                cmd, cmdIndex = cmd.split("_")  # this gives us the clear cmd and the index

            sickrage.srLogger.debug("API :: " + cmd + ": curKwargs " + str(curKwargs))
            if not (multiCmds and cmd in ('show.getbanner', 'show.getfanart', 'show.getnetworklogo',
                                          'show.getposter')):  # skip these cmd while chaining
                try:
                    if cmd in self.function_mapper:
                        # call function and get response back
                        curOutDict = self.function_mapper[cmd](self.application, self.request, *curArgs,
                                                               **curKwargs).run()
                    elif _is_int(cmd):
                        curOutDict = TVDBShorthandWrapper(cmd, self.application, self.request, *curArgs,
                                                          **curKwargs).run()
                    else:
                        curOutDict = _responds(RESULT_ERROR, "No such cmd: '" + cmd + "'")
                except ApiError as e:  # Api errors that we raised, they are harmless
                    curOutDict = _responds(RESULT_ERROR, msg=e.message)
            else:  # if someone chained one of the forbiden cmds they will get an error for this one cmd
                curOutDict = _responds(RESULT_ERROR, msg="The cmd '" + cmd + "' is not supported while chaining")

            if multiCmds:
                # note: if multiple same cmds are issued but one has not an index defined it will override all others
                # or the other way around, this depends on the order of the cmds
                # this is not a bug
                if cmdIndex is None:  # do we need a index dict for this cmd ?
                    outDict[cmd] = curOutDict
                else:
                    if cmd not in outDict:
                        outDict[cmd] = {}
                    outDict[cmd][cmdIndex] = curOutDict

                outDict = _responds(RESULT_SUCCESS, outDict)
            else:
                outDict = curOutDict

            return outDict

        return CMD_SiCKRAGE(*args, **kwargs).run()

    def filter_params(self, cmd, *args, **kwargs):
        """ return only params kwargs that are for cmd
            and rename them to a clean version (remove "<cmd>_")
            args are shared across all cmds

            all args and kwarks are lowerd

            cmd are separated by "|" e.g. &cmd=shows|future
            kwargs are namespaced with "." e.g. show.indexerid=101501
            if a karg has no namespace asing it anyways (global)

            full e.g.
            /api?apikey=1234&cmd=show.seasonlist_asd|show.seasonlist_2&show.seasonlist_asd.indexerid=101501&show.seasonlist_2.indexerid=79488&sort=asc

            two calls of show.seasonlist
            one has the index "asd" the other one "2"
            the "indexerid" kwargs / params have the indexed cmd as a namspace
            and the kwarg / param "sort" is a used as a global
        """
        curArgs = []
        for arg in args[1:] or []:
            try:
                curArgs += [arg.lower()]
            except:
                continue

        curKwargs = {}
        for kwarg in kwargs or []:
            try:
                if kwarg.find(cmd + ".") == 0:
                    cleanKey = kwarg.rpartition(".")[2]
                    curKwargs[cleanKey] = kwargs[kwarg].lower()
                elif not "." in kwarg:
                    curKwargs[kwarg] = kwargs[kwarg]
            except:
                continue

        return curArgs, curKwargs

    @property
    def function_mapper(self):
        return {
            "help": CMD_Help,
            "future": CMD_ComingEpisodes,
            "episode": CMD_Episode,
            "episode.search": CMD_EpisodeSearch,
            "episode.setstatus": CMD_EpisodeSetStatus,
            "episode.subtitlesearch": CMD_SubtitleSearch,
            "exceptions": CMD_Exceptions,
            "history": CMD_History,
            "history.clear": CMD_HistoryClear,
            "history.trim": CMD_HistoryTrim,
            "failed": CMD_Failed,
            "backlog": CMD_Backlog,
            "logs": CMD_Logs,
            "sb": CMD_SiCKRAGE,
            "postprocess": CMD_PostProcess,
            "sb.addrootdir": CMD_SiCKRAGEAddRootDir,
            "sb.checkversion": CMD_SiCKRAGECheckVersion,
            "sb.checkscheduler": CMD_SiCKRAGECheckScheduler,
            "sb.deleterootdir": CMD_SiCKRAGEDeleteRootDir,
            "sb.getdefaults": CMD_SiCKRAGEGetDefaults,
            "sb.getmessages": CMD_SiCKRAGEGetMessages,
            "sb.getrootdirs": CMD_SiCKRAGEGetRootDirs,
            "sb.pausebacklog": CMD_SiCKRAGEPauseBacklog,
            "sb.ping": CMD_SiCKRAGEPing,
            "sb.restart": CMD_SiCKRAGERestart,
            "sb.searchindexers": CMD_SiCKRAGESearchIndexers,
            "sb.searchtvdb": CMD_SiCKRAGESearchTVDB,
            "sb.searchtvrage": CMD_SiCKRAGESearchTVRAGE,
            "sb.setdefaults": CMD_SiCKRAGESetDefaults,
            "sb.update": CMD_SiCKRAGEUpdate,
            "sb.shutdown": CMD_SiCKRAGEShutdown,
            "show": CMD_Show,
            "show.addexisting": CMD_ShowAddExisting,
            "show.addnew": CMD_ShowAddNew,
            "show.cache": CMD_ShowCache,
            "show.delete": CMD_ShowDelete,
            "show.getquality": CMD_ShowGetQuality,
            "show.getposter": CMD_ShowGetPoster,
            "show.getbanner": CMD_ShowGetBanner,
            "show.getnetworklogo": CMD_ShowGetNetworkLogo,
            "show.getfanart": CMD_ShowGetFanArt,
            "show.pause": CMD_ShowPause,
            "show.refresh": CMD_ShowRefresh,
            "show.seasonlist": CMD_ShowSeasonList,
            "show.seasons": CMD_ShowSeasons,
            "show.setquality": CMD_ShowSetQuality,
            "show.stats": CMD_ShowStats,
            "show.update": CMD_ShowUpdate,
            "shows": CMD_Shows,
            "shows.stats": CMD_ShowsStats
        }


class ApiCall(ApiHandler):
    _help = {"desc": "This command is not documented. Please report this to the developers."}
    _requiredParams = {}
    _optionalParams = {}
    _missing = []

    def __init__(self, application, request, *args, **kwargs):
        super(ApiCall, self).__init__(application, request, *args, **kwargs)

        try:
            if self._missing:
                self.run = self.return_missing
        except AttributeError:
            pass

        # help
        if 'help' in kwargs:
            self.run = self.return_help

    def run(self):
        # override with real output function in subclass
        return {}

    def return_help(self):
        for paramDict, paramType in [(self._requiredParams, "requiredParameters"),
                                     (self._optionalParams, "optionalParameters")]:

            if paramType in self._help:
                for paramName in paramDict:
                    if not paramName in self._help[paramType]:
                        self._help.setdefault(paramType, {})[paramName] = {}
                    if paramDict[paramName][b"allowedValues"]:
                        self._help.setdefault(paramType, {})[paramName][b"allowedValues"] = paramDict[paramName][
                            b"allowedValues"]
                    else:
                        self._help.setdefault(paramType, {})[paramName][b"allowedValues"] = "see desc"
                    self._help.setdefault(paramType, {})[paramName][b"defaultValue"] = paramDict[paramName][
                        b"defaultValue"]
                    self._help.setdefault(paramType, {})[paramName][b"type"] = paramDict[paramName][b"type"]

            elif paramDict:
                for paramName in paramDict:
                    self._help.setdefault(paramType, {})[paramName] = paramDict[paramName]
            else:
                self._help[paramType] = {}
        msg = "No description available"
        if "desc" in self._help:
            msg = self._help[b"desc"]
        return _responds(RESULT_SUCCESS, self._help, msg)

    def return_missing(self):
        if len(self._missing) == 1:
            msg = "The required parameter: '" + self._missing[0] + "' was not set"
        else:
            msg = "The required parameters: '" + "','".join(self._missing) + "' where not set"
        return _responds(RESULT_ERROR, msg=msg)

    def check_params(self, key, default, required, arg_type, allowedValues, *args, **kwargs):

        """ function to check passed params for the shorthand wrapper
            and to detect missing/required params
        """

        # auto-select indexer
        if key in indexer_ids:
            if "tvdbid" in kwargs:
                key = "tvdbid"

            self.indexer = indexer_ids.index(key)

        missing = True
        orgDefault = default

        if arg_type == "bool":
            allowedValues = [0, 1]

        if args:
            default = args[0]
            args = args[1:]
            missing = False

        if kwargs.get(key):
            default = kwargs.get(key)
            missing = False

        if required:
            if self._missing:
                self._requiredParams.update(key)
            else:
                self._requiredParams = {key: {"allowedValues": allowedValues,
                                              "defaultValue": orgDefault,
                                              "type": arg_type}}

            if missing and key not in self._missing:
                self._missing.append(key)
        else:
            self._optionalParams[key] = {"allowedValues": allowedValues,
                                         "defaultValue": orgDefault,
                                         "type": arg_type}

        if default:
            default = self._check_param_type(default, key, arg_type)
            self._check_param_value(default, key, allowedValues)

        return default, args

    def _check_param_type(self, value, name, arg_type):
        """ checks if value can be converted / parsed to arg_type
            will raise an error on failure
            or will convert it to arg_type and return new converted value
            can check for:
            - int: will be converted into int
            - bool: will be converted to False / True
            - list: will always return a list
            - string: will do nothing for now
            - ignore: will ignore it, just like "string"
        """
        error = False
        if arg_type == "int":
            if _is_int(value):
                value = int(value)
            else:
                error = True
        elif arg_type == "bool":
            if value in ("0", "1"):
                value = bool(int(value))
            elif value in ("true", "True", "TRUE"):
                value = True
            elif value in ("false", "False", "FALSE"):
                value = False
            elif value not in (True, False):
                error = True
        elif arg_type == "list":
            value = value.split("|")
        elif arg_type == "string":
            pass
        elif arg_type == "ignore":
            pass
        else:
            sickrage.srLogger.error('API :: Invalid param type: "%s" can not be checked. Ignoring it.' % str(arg_type))

        if error:
            # this is a real ApiError !!
            raise ApiError('param "%s" with given value "%s" could not be parsed into "%s"'
                           % (str(name), str(value), str(arg_type)))

        return value

    def _check_param_value(self, value, name, allowedValues):
        """ will check if value (or all values in it ) are in allowed values
            will raise an exception if value is "out of range"
            if bool(allowedValue) == False a check is not performed and all values are excepted
        """
        if allowedValues:
            error = False
            if isinstance(value, list):
                for item in value:
                    if not item in allowedValues:
                        error = True
            else:
                if not value in allowedValues:
                    error = True

            if error:
                # this is kinda a ApiError but raising an error is the only way of quitting here
                raise ApiError("param: '" + str(name) + "' with given value: '" + str(
                        value) + "' is out of allowed range '" + str(allowedValues) + "'")


class TVDBShorthandWrapper(ApiCall):
    _help = {"desc": "This is an internal function wrapper. Call the help command directly for more information."}

    def __init__(self, sid, application, request, *args, **kwargs):
        self.origArgs = args
        self.kwargs = kwargs
        self.sid = sid

        self.s, args = self.check_params("s", None, False, "ignore", [], *args, **kwargs)
        self.e, args = self.check_params("e", None, False, "ignore", [], *args, **kwargs)
        self.args = args

        super(TVDBShorthandWrapper, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ internal function wrapper """
        args = (self.sid,) + self.origArgs
        if self.e:
            return CMD_Episode(*args, **self.kwargs).run()
        elif self.s:
            return CMD_ShowSeasons(*args, **self.kwargs).run()
        else:
            return CMD_Show(*args, **self.kwargs).run()


# ###############################
#       helper functions        #
# ###############################

def _is_int(data):
    try:
        int(data)
    except (TypeError, ValueError, OverflowError):
        return False
    else:
        return True


def _rename_element(dict_obj, oldKey, newKey):
    try:
        dict_obj[newKey] = dict_obj[oldKey]
        del dict_obj[oldKey]
    except (ValueError, TypeError, NameError):
        pass
    return dict_obj


def _responds(result_type, data=None, msg=""):
    """
    result is a string of given "type" (success/failure/timeout/error)
    message is a human readable string, can be empty
    data is either a dict or a array, can be a empty dict or empty array
    """
    if data is None:
        data = {}
    return {"result": result_type_map[result_type],
            "message": msg,
            "data": data}


def _get_status_Strings(s):
    return statusStrings[s]


def _ordinal_to_dateTimeForm(ordinal):
    # workaround for episodes with no airdate
    if int(ordinal) != 1:
        date = datetime.now().date().fromordinal(ordinal)
    else:
        return ""
    return date.strftime(dateTimeFormat)


def _ordinal_to_dateForm(ordinal):
    if int(ordinal) != 1:
        date = datetime.now().date().fromordinal(ordinal)
    else:
        return ""
    return date.strftime(dateFormat)


def _historyDate_to_dateTimeForm(timeString):
    date = datetime.strptime(timeString, History.date_format)
    return date.strftime(dateTimeFormat)


def _mapQuality(showObj):
    quality_map = _getQualityMap()

    anyQualities = []
    bestQualities = []

    iqualityID, aqualityID = Quality.splitQuality(int(showObj))
    if iqualityID:
        for quality in iqualityID:
            anyQualities.append(quality_map[quality])
    if aqualityID:
        for quality in aqualityID:
            bestQualities.append(quality_map[quality])
    return anyQualities, bestQualities


def _getQualityMap():
    return {Quality.SDTV: 'sdtv',
            Quality.SDDVD: 'sddvd',
            Quality.HDTV: 'hdtv',
            Quality.RAWHDTV: 'rawhdtv',
            Quality.FULLHDTV: 'fullhdtv',
            Quality.HDWEBDL: 'hdwebdl',
            Quality.FULLHDWEBDL: 'fullhdwebdl',
            Quality.HDBLURAY: 'hdbluray',
            Quality.FULLHDBLURAY: 'fullhdbluray',
            Quality.UNKNOWN: 'unknown'}


def _getRootDirs():
    if sickrage.srConfig.ROOT_DIRS == "":
        return {}

    rootDir = {}
    root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')
    default_index = int(sickrage.srConfig.ROOT_DIRS.split('|')[0])

    rootDir[b"default_index"] = int(sickrage.srConfig.ROOT_DIRS.split('|')[0])
    # remove default_index value from list (this fixes the offset)
    root_dirs.pop(0)

    if len(root_dirs) < default_index:
        return {}

    # clean up the list - replace %xx escapes by their single-character equivalent
    root_dirs = [urllib.unquote_plus(x) for x in root_dirs]

    default_dir = root_dirs[default_index]

    dir_list = []
    for root_dir in root_dirs:
        valid = 1
        try:
            os.listdir(root_dir)
        except Exception:
            valid = 0
        default = 0
        if root_dir is default_dir:
            default = 1

        curDir = {}
        curDir[b'valid'] = valid
        curDir[b'location'] = root_dir
        curDir[b'default'] = default
        dir_list.append(curDir)

    return dir_list


class ApiError(Exception):
    """
    Generic API error
    """


class IntParseError(Exception):
    """
    A value could not be parsed into an int, but should be parsable to an int
    """


# -------------------------------------------------------------------------------------#


class CMD_Help(ApiCall):
    _help = {
        "desc": "Get help about a given command",
        "optionalParameters": {
            "subject": {"desc": "The name of the command to get the help of"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.subject, args = self.check_params("subject", "help", False, "string", self.function_mapper.keys(), args,
                                               kwargs)
        super(CMD_Help, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get help about a given command """
        if self.subject in self.function_mapper:
            out = _responds(RESULT_SUCCESS,
                            self.function_mapper.get(self.subject)(self.application, self.request, **{"help": 1}).run())
        else:
            out = _responds(RESULT_FAILURE, msg="No such cmd")
        return out


class CMD_ComingEpisodes(ApiCall):
    _help = {
        "desc": "Get the coming episodes",
        "optionalParameters": {
            "sort": {"desc": "Change the sort order"},
            "type": {"desc": "One or more categories of coming episodes, separated by |"},
            "paused": {
                "desc": "0 to exclude paused shows, 1 to include them, or omitted to use SiCKRAGE default value"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.sort, args = self.check_params("sort", "date", False, "string", ComingEpisodes.sorts.keys(), *args,
                                            **kwargs)
        self.type, args = self.check_params("type", '|'.join(ComingEpisodes.categories), False, "list",
                                            ComingEpisodes.categories, *args, **kwargs)
        self.paused, args = self.check_params("paused", bool(sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED), False, "bool", [],
                                              *args, **kwargs)
        # super, missing, help
        super(CMD_ComingEpisodes, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the coming episodes """
        grouped_coming_episodes = ComingEpisodes.get_coming_episodes(self.type, self.sort, True, self.paused)
        data = {section: [] for section in grouped_coming_episodes.keys()}

        for section, coming_episodes in grouped_coming_episodes.iteritems():
            for coming_episode in coming_episodes:
                data[section].append({
                    'airdate': coming_episode[b'airdate'],
                    'airs': coming_episode[b'airs'],
                    'ep_name': coming_episode[b'name'],
                    'ep_plot': coming_episode[b'description'],
                    'episode': coming_episode[b'episode'],
                    'indexerid': coming_episode[b'indexer_id'],
                    'network': coming_episode[b'network'],
                    'paused': coming_episode[b'paused'],
                    'quality': coming_episode[b'quality'],
                    'season': coming_episode[b'season'],
                    'show_name': coming_episode[b'show_name'],
                    'show_status': coming_episode[b'status'],
                    'tvdbid': coming_episode[b'tvdbid'],
                    'weekday': coming_episode[b'weekday']
                })

        return _responds(RESULT_SUCCESS, data)


class CMD_Episode(ApiCall):
    _help = {
        "desc": "Get detailed information about an episode",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "full_path": {
                "desc": "Return the full absolute show location (if valid, and True), or the relative show location"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)
        # optional
        self.fullPath, args = self.check_params("full_path", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_Episode, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get detailed information about an episode """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        sqlResults = main_db.MainDB(row_type="dict").select(
                "SELECT name, description, airdate, status, location, file_size, release_name, subtitles FROM tv_episodes WHERE showid = ? AND episode = ? AND season = ?",
                [self.indexerid, self.e, self.s])
        if not len(sqlResults) == 1:
            raise ApiError("Episode not found")
        episode = sqlResults[0]
        # handle path options
        # absolute vs relative vs broken
        showPath = None
        try:
            showPath = showObj.location
        except ShowDirectoryNotFoundException:
            pass

        if bool(self.fullPath) == True and showPath:
            pass
        elif bool(self.fullPath) == False and showPath:
            # using the length because lstrip removes to much
            showPathLength = len(showPath) + 1  # the / or \ yeah not that nice i know
            episode[b"location"] = episode[b"location"][showPathLength:]
        elif not showPath:  # show dir is broken ... episode path will be empty
            episode[b"location"] = ""

        # convert stuff to human form
        if tryInt(episode[b'airdate'], 1) > 693595:  # 1900
            episode[b'airdate'] = srdatetime.srDateTime.srfdate(srdatetime.srDateTime.convert_to_setting(
                    tz_updater.parse_date_time(int(episode[b'airdate']), showObj.airs, showObj.network)),
                    d_preset=dateFormat)
        else:
            episode[b'airdate'] = 'Never'

        status, quality = Quality.splitCompositeStatus(int(episode[b"status"]))
        episode[b"status"] = _get_status_Strings(status)
        episode[b"quality"] = quality.get_quality_string(quality)
        episode[b"file_size_human"] = pretty_filesize(episode[b"file_size"])

        return _responds(RESULT_SUCCESS, episode)


class CMD_EpisodeSearch(ApiCall):
    _help = {
        "desc": "Search for an episode. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_EpisodeSearch, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Search for an episode """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        epObj = showObj.getEpisode(int(self.s), int(self.e))
        if isinstance(epObj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # make a queue item for it and put it on the queue
        ep_queue_item = sickrage.srCore.SEARCHQUEUE.add_item(ManualSearchQueueItem(showObj, epObj))  # @UndefinedVariable

        # wait until the queue item tells us whether it worked or not
        while ep_queue_item.success is None:  # @UndefinedVariable
            time.sleep(1)

        # return the correct json value
        if ep_queue_item.success:
            status, quality = Quality.splitCompositeStatus(epObj.status)  # @UnusedVariable
            # TODO: split quality and status?
            return _responds(RESULT_SUCCESS, {"quality": quality.get_quality_string(quality)},
                             "Snatched (" + quality.get_quality_string(quality) + ")")

        return _responds(RESULT_FAILURE, msg='Unable to find episode')


class CMD_EpisodeSetStatus(ApiCall):
    _help = {
        "desc": "Set the status of an episode or a season (when no episode is provided)",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "status": {"desc": "The status of the episode or season"}
        },
        "optionalParameters": {
            "episode": {"desc": "The episode number"},
            "force": {"desc": "True to replace existing downloaded episode or season, False otherwise"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.status, args = self.check_params("status", None, True, "string",
                                              ["wanted", "skipped", "ignored", "failed"], *args, **kwargs)
        # optional
        self.e, args = self.check_params("episode", None, False, "int", [], *args, **kwargs)
        self.force, args = self.check_params("force", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_EpisodeSetStatus, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Set the status of an episode or a season (when no episode is provided) """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # convert the string status to a int
        for status in statusStrings.statusStrings:
            if str(statusStrings[status]).lower() == str(self.status).lower():
                self.status = status
                break
        else:  # if we dont break out of the for loop we got here.
            # the allowed values has at least one item that could not be matched against the internal status strings
            raise ApiError("The status string could not be matched to a status. Report to Devs!")

        ep_list = []
        if self.e:
            epObj = showObj.getEpisode(self.s, self.e)
            if epObj is None:
                return _responds(RESULT_FAILURE, msg="Episode not found")
            ep_list = [epObj]
        else:
            # get all episode numbers frome self,season
            ep_list = showObj.getAllEpisodes(season=self.s)

        def _epResult(result_code, ep, msg=""):
            return {'season': ep.season, 'episode': ep.episode, 'status': _get_status_Strings(ep.status),
                    'result': result_type_map[result_code], 'message': msg}

        ep_results = []
        failure = False
        start_backlog = False
        segments = {}

        sql_l = []
        for epObj in ep_list:
            with epObj.lock:
                if self.status == WANTED:
                    # figure out what episodes are wanted so we can backlog them
                    if epObj.season in segments:
                        segments[epObj.season].append(epObj)
                    else:
                        segments[epObj.season] = [epObj]

                # don't let them mess up UNAIRED episodes
                if epObj.status == UNAIRED:
                    if self.e is not None:  # setting the status of a unaired is only considert a failure if we directly wanted this episode, but is ignored on a season request
                        ep_results.append(
                                _epResult(RESULT_FAILURE, epObj, "Refusing to change status because it is UNAIRED"))
                        failure = True
                    continue

                if self.status == FAILED and not sickrage.srConfig.USE_FAILED_DOWNLOADS:
                    ep_results.append(_epResult(RESULT_FAILURE, epObj,
                                                "Refusing to change status to FAILED because failed download handling is disabled"))
                    failure = True
                    continue

                # allow the user to force setting the status for an already downloaded episode
                if epObj.status in Quality.DOWNLOADED + Quality.ARCHIVED and not self.force:
                    ep_results.append(_epResult(RESULT_FAILURE, epObj,
                                                "Refusing to change status because it is already marked as DOWNLOADED"))
                    failure = True
                    continue

                epObj.status = self.status
                sql_q = epObj.saveToDB(False)
                if sql_q:
                    sql_l.append(sql_q)
                    del sql_q  # cleanup

                if self.status == WANTED:
                    start_backlog = True

                ep_results.append(_epResult(RESULT_SUCCESS, epObj))

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

        extra_msg = ""
        if start_backlog:
            for season, segment in segments.iteritems():
                sickrage.srCore.SEARCHQUEUE.add_item(BacklogQueueItem(showObj, segment))  # @UndefinedVariable
                sickrage.srLogger.info("API :: Starting backlog for " + showObj.name + " season " + str(
                        season) + " because some episodes were set to WANTED")

            extra_msg = " Backlog started"

        if failure:
            return _responds(RESULT_FAILURE, ep_results, 'Failed to set all or some status. Check data.' + extra_msg)
        else:
            return _responds(RESULT_SUCCESS, msg='All status set successfully.' + extra_msg)


class CMD_SubtitleSearch(ApiCall):
    _help = {
        "desc": "Search for an episode subtitles. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_SubtitleSearch, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Search for an episode subtitles """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        epObj = showObj.getEpisode(int(self.s), int(self.e))
        if isinstance(epObj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # try do download subtitles for that episode
        previous_subtitles = epObj.subtitles

        try:
            subtitles = epObj.downloadSubtitles()
        except Exception:
            return _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        # return the correct json value
        newSubtitles = frozenset(epObj.subtitles).difference(previous_subtitles)
        if newSubtitles:
            newLangs = [subtitle_searcher.fromietf(newSub) for newSub in newSubtitles]
            status = 'New subtitles downloaded: %s' % ', '.join([newLang.name for newLang in newLangs])
            response = _responds(RESULT_SUCCESS, msg='New subtitles found')
        else:
            status = 'No subtitles downloaded'
            response = _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        notifications.message('Subtitles Search', status)

        return response


class CMD_Exceptions(ApiCall):
    _help = {
        "desc": "Get the scene exceptions for all or a given show",
        "optionalParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.indexerid, args = self.check_params("indexerid", None, False, "int", [], *args, **kwargs)

        # super, missing, help
        super(CMD_Exceptions, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the scene exceptions for all or a given show """

        if self.indexerid is None:
            sqlResults = cache_db.CacheDB(row_type='dict').select(
                    "SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions")
            scene_exceptions = {}
            for row in sqlResults:
                indexerid = row[b"indexerid"]
                if not indexerid in scene_exceptions:
                    scene_exceptions[indexerid] = []
                scene_exceptions[indexerid].append(row[b"show_name"])

        else:
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
            if not showObj:
                return _responds(RESULT_FAILURE, msg="Show not found")

            sqlResults = cache_db.CacheDB(row_type='dict').select(
                    "SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions WHERE indexer_id = ?",
                    [self.indexerid])
            scene_exceptions = []
            for row in sqlResults:
                scene_exceptions.append(row[b"show_name"])

        return _responds(RESULT_SUCCESS, scene_exceptions)


class CMD_History(ApiCall):
    _help = {
        "desc": "Get the downloaded and/or snatched history",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
            "type": {"desc": "Only get some entries. No value will returns every type"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.limit, args = self.check_params("limit", 100, False, "int", [], *args, **kwargs)
        self.type, args = self.check_params("type", None, False, "string", ["downloaded", "snatched"], *args, **kwargs)
        self.type = self.type.lower() if isinstance(self.type, str) else ''

        # super, missing, help
        super(CMD_History, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the downloaded and/or snatched history """
        data = History().get(self.limit, self.type)
        results = []

        for row in data:
            status, quality = Quality.splitCompositeStatus(int(row[b"action"]))
            status = _get_status_Strings(status)

            if self.type and not status.lower() == self.type:
                continue

            row[b"status"] = status
            row[b"quality"] = get_quality_string(quality)
            row[b"date"] = _historyDate_to_dateTimeForm(str(row[b"date"]))

            del row[b"action"]

            _rename_element(row, "show_id", "indexerid")
            row[b"resource_path"] = os.path.dirname(row[b"resource"])
            row[b"resource"] = os.path.basename(row[b"resource"])

            # Add tvdbid for backward compatibility
            row[b'tvdbid'] = row[b'indexerid']
            results.append(row)

        return _responds(RESULT_SUCCESS, results)


class CMD_HistoryClear(ApiCall):
    _help = {"desc": "Clear the entire history"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_HistoryClear, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Clear the entire history """
        History().clear()

        return _responds(RESULT_SUCCESS, msg="History cleared")


class CMD_HistoryTrim(ApiCall):
    _help = {"desc": "Trim history entries older than 30 days"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_HistoryTrim, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Trim history entries older than 30 days """
        History().trim()

        return _responds(RESULT_SUCCESS, msg='Removed history entries older than 30 days')


class CMD_Failed(ApiCall):
    _help = {
        "desc": "Get the failed downloads",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.limit, args = self.check_params("limit", 100, False, "int", [], *args, **kwargs)
        # super, missing, help
        super(CMD_Failed, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the failed downloads """

        ulimit = min(int(self.limit), 100)
        if ulimit == 0:
            sqlResults = failed_db.FailedDB(row_type='dict').select("SELECT * FROM failed")
        else:
            sqlResults = failed_db.FailedDB(row_type='dict').select("SELECT * FROM failed LIMIT ?", [ulimit])

        return _responds(RESULT_SUCCESS, sqlResults)


class CMD_Backlog(ApiCall):
    _help = {"desc": "Get the backlogged episodes"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_Backlog, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the backlogged episodes """

        shows = []

        for curShow in sickrage.srCore.SHOWLIST:

            showEps = []

            sqlResults = main_db.MainDB(row_type='dict').select(
                    "SELECT tv_episodes.*, tv_shows.paused FROM tv_episodes INNER JOIN tv_shows ON tv_episodes.showid = tv_shows.indexer_id WHERE showid = ? AND paused = 0 ORDER BY season DESC, episode DESC",
                    [curShow.indexerid])

            for curResult in sqlResults:

                curEpCat = curShow.getOverview(int(curResult[b"status"] or -1))
                if curEpCat and curEpCat in (Overview.WANTED, Overview.QUAL):
                    showEps.append(curResult)

            if showEps:
                shows.append({
                    "indexerid": curShow.indexerid,
                    "show_name": curShow.name,
                    "status": curShow.status,
                    "episodes": showEps
                })

        return _responds(RESULT_SUCCESS, shows)


class CMD_Logs(ApiCall):
    _help = {
        "desc": "Get the logs",
        "optionalParameters": {
            "min_level": {
                "desc":
                    "The minimum level classification of log entries to return. "
                    "Each level inherits its above levels: debug < info < warning < error"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.min_level, args = self.check_params("min_level", "error", False, "string",
                                                 ["error", "warning", "info", "debug"], *args, **kwargs)
        # super, missing, help
        super(CMD_Logs, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the logs """
        # 10 = Debug / 20 = Info / 30 = Warning / 40 = Error
        minLevel = sickrage.srLogger.logLevels[str(self.min_level).upper()]

        data = []
        if os.path.isfile(sickrage.srConfig.LOG_FILE):
            with io.open(sickrage.srConfig.LOG_FILE, 'r', encoding='utf-8') as f:
                data = f.readlines()

        regex = r"^(\d\d\d\d)\-(\d\d)\-(\d\d)\s*(\d\d)\:(\d\d):(\d\d)\s*([A-Z]+)\s*(.+?)\s*\:\:\s*(.*)$"

        finalData = []

        numLines = 0
        lastLine = False
        numToShow = min(50, len(data))

        for x in reversed(data):

            match = re.match(regex, x)

            if match:
                level = match.group(7)
                if level not in sickrage.srLogger.logLevels:
                    lastLine = False
                    continue

                if sickrage.srLogger.logLevels[level] >= minLevel:
                    lastLine = True
                    finalData.append(x.rstrip("\n"))
                else:
                    lastLine = False
                    continue

            elif lastLine:
                finalData.append("AA" + x)

            numLines += 1

            if numLines >= numToShow:
                break

        return _responds(RESULT_SUCCESS, finalData)


class CMD_PostProcess(ApiCall):
    _help = {
        "desc": "Manually post-process the files in the download folder",
        "optionalParameters": {
            "path": {"desc": "The path to the folder to post-process"},
            "force_replace": {"desc": "Force already post-processed files to be post-processed again"},
            "return_data": {"desc": "Returns the result of the post-process"},
            "process_method": {"desc": "How should valid post-processed files be handled"},
            "is_priority": {"desc": "Replace the file even if it exists in a higher quality"},
            "failed": {"desc": "Mark download as failed"},
            "type": {"desc": "The type of post-process being requested"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.path, args = self.check_params("path", None, False, "string", [], *args, **kwargs)
        self.force_replace, args = self.check_params("force_replace", False, False, "bool", [], *args, **kwargs)
        self.return_data, args = self.check_params("return_data", False, False, "bool", [], *args, **kwargs)
        self.process_method, args = self.check_params("process_method", False, False, "string",
                                                      ["copy", "symlink", "hardlink", "move"], *args, **kwargs)
        self.is_priority, args = self.check_params("is_priority", False, False, "bool", [], *args, **kwargs)
        self.failed, args = self.check_params("failed", False, False, "bool", [], *args, **kwargs)
        self.type, args = self.check_params("type", "auto", None, "string", ["auto", "manual"], *args, **kwargs)
        # super, missing, help
        super(CMD_PostProcess, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Manually post-process the files in the download folder """
        if not self.path and not sickrage.srConfig.TV_DOWNLOAD_DIR:
            return _responds(RESULT_FAILURE, msg="You need to provide a path or set TV Download Dir")

        if not self.path:
            self.path = sickrage.srConfig.TV_DOWNLOAD_DIR

        if not self.type:
            self.type = 'manual'

        data = processDir(self.path, process_method=self.process_method, force=self.force_replace,
                          is_priority=self.is_priority, failed=self.failed, proc_type=self.type)

        if not self.return_data:
            data = ""

        return _responds(RESULT_SUCCESS, data=data, msg="Started postprocess for %s" % self.path)


class CMD_SiCKRAGE(ApiCall):
    _help = {"desc": "Get miscellaneous information about SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGE, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ dGet miscellaneous information about SiCKRAGE """
        data = {"sr_version": sickrage.srCore.VERSION, "api_version": self.version,
                "api_commands": sorted(self.function_mapper.keys())}
        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEAddRootDir(ApiCall):
    _help = {
        "desc": "Add a new root (parent) directory to SiCKRAGE",
        "requiredParameters": {
            "location": {"desc": "The full path to the new root (parent) directory"},
        },
        "optionalParameters": {
            "default": {"desc": "Make this new location the default root (parent) directory"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)
        # optional
        self.default, args = self.check_params("default", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_SiCKRAGEAddRootDir, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Add a new root (parent) directory to SiCKRAGE """

        self.location = urllib.unquote_plus(self.location)
        location_matched = 0
        index = 0

        # dissallow adding/setting an invalid dir
        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="Location is invalid")

        root_dirs = []

        if sickrage.srConfig.ROOT_DIRS == "":
            self.default = 1
        else:
            root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')
            index = int(sickrage.srConfig.ROOT_DIRS.split('|')[0])
            root_dirs.pop(0)
            # clean up the list - replace %xx escapes by their single-character equivalent
            root_dirs = [urllib.unquote_plus(x) for x in root_dirs]
            for x in root_dirs:
                if x == self.location:
                    location_matched = 1
                    if self.default == 1:
                        index = root_dirs.index(self.location)
                    break

        if location_matched == 0:
            if self.default == 1:
                root_dirs.insert(0, self.location)
            else:
                root_dirs.append(self.location)

        root_dirs_new = [urllib.unquote_plus(x) for x in root_dirs]
        root_dirs_new.insert(0, index)
        root_dirs_new = '|'.join(unicode(x) for x in root_dirs_new)

        sickrage.srConfig.ROOT_DIRS = root_dirs_new
        return _responds(RESULT_SUCCESS, _getRootDirs(), msg="Root directories updated")


class CMD_SiCKRAGECheckVersion(ApiCall):
    _help = {"desc": "Check if a new version of SiCKRAGE is available"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGECheckVersion, self).__init__(application, request, *args, **kwargs)

    def run(self):
        return _responds(RESULT_SUCCESS, {
            "current_version": {
                "version": sickrage.srCore.VERSIONUPDATER.updater.version,
            },
            "latest_version": {
                "version": sickrage.srCore.VERSIONUPDATER.updater.get_newest_version,
            },
            "needs_update": sickrage.srCore.VERSIONUPDATER.check_for_new_version(),
        })

class CMD_SiCKRAGECheckScheduler(ApiCall):
    _help = {"desc": "Get information about the scheduler"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGECheckScheduler, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get information about the scheduler """
        sqlResults = main_db.MainDB(row_type='dict').select("SELECT last_backlog FROM info")

        backlogPaused = sickrage.srCore.SEARCHQUEUE.is_backlog_paused()  # @UndefinedVariable
        backlogRunning = sickrage.srCore.SEARCHQUEUE.is_backlog_in_progress()  # @UndefinedVariable
        nextBacklog = sickrage.srCore.BACKLOGSEARCHER.nextRun().strftime(dateFormat).decode(sickrage.srCore.SYS_ENCODING)

        data = {"backlog_is_paused": int(backlogPaused), "backlog_is_running": int(backlogRunning),
                "last_backlog": _ordinal_to_dateForm(sqlResults[0][b"last_backlog"]),
                "next_backlog": nextBacklog}
        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEDeleteRootDir(ApiCall):
    _help = {"desc": "'Delete a root (parent) directory from SiCKRAGE", "requiredParameters": {
        "location": {"desc": "The full path to the root (parent) directory to remove"},
    }}

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEDeleteRootDir, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Delete a root (parent) directory from SiCKRAGE """
        if sickrage.srConfig.ROOT_DIRS == "":
            return _responds(RESULT_FAILURE, _getRootDirs(), msg="No root directories detected")

        newIndex = 0
        root_dirs_new = []
        root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')
        index = int(root_dirs[0])
        root_dirs.pop(0)
        # clean up the list - replace %xx escapes by their single-character equivalent
        root_dirs = [urllib.unquote_plus(x) for x in root_dirs]
        old_root_dir = root_dirs[index]
        for curRootDir in root_dirs:
            if not curRootDir == self.location:
                root_dirs_new.append(curRootDir)
            else:
                newIndex = 0

        for curIndex, curNewRootDir in enumerate(root_dirs_new):
            if curNewRootDir is old_root_dir:
                newIndex = curIndex
                break

        root_dirs_new = [urllib.unquote_plus(x) for x in root_dirs_new]
        if len(root_dirs_new) > 0:
            root_dirs_new.insert(0, newIndex)
        root_dirs_new = "|".join(unicode(x) for x in root_dirs_new)

        sickrage.srConfig.ROOT_DIRS = root_dirs_new
        # what if the root dir was not found?
        return _responds(RESULT_SUCCESS, _getRootDirs(), msg="Root directory deleted")


class CMD_SiCKRAGEGetDefaults(ApiCall):
    _help = {"desc": "Get SiCKRAGE's user default configuration value"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEGetDefaults, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get SiCKRAGE's user default configuration value """

        anyQualities, bestQualities = _mapQuality(sickrage.srConfig.QUALITY_DEFAULT)

        data = {"status": statusStrings[sickrage.srConfig.STATUS_DEFAULT].lower(),
                "flatten_folders": int(sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT), "initial": anyQualities,
                "archive": bestQualities, "future_show_paused": int(sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED)}
        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEGetMessages(ApiCall):
    _help = {"desc": "Get all messages"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEGetMessages, self).__init__(application, request, *args, **kwargs)

    def run(self):
        messages = []
        for cur_notification in notifications.get_notifications(self.request.remote_ip):
            messages.append({"title": cur_notification.title,
                             "message": cur_notification.message,
                             "type": cur_notification.type})
        return _responds(RESULT_SUCCESS, messages)


class CMD_SiCKRAGEGetRootDirs(ApiCall):
    _help = {"desc": "Get all root (parent) directories"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEGetRootDirs, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get all root (parent) directories """

        return _responds(RESULT_SUCCESS, _getRootDirs())


class CMD_SiCKRAGEPauseBacklog(ApiCall):
    _help = {
        "desc": "Pause or unpause the backlog search",
        "optionalParameters": {
            "pause ": {"desc": "True to pause the backlog search, False to unpause it"}
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.pause, args = self.check_params("pause", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_SiCKRAGEPauseBacklog, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Pause or unpause the backlog search """
        if self.pause:
            sickrage.srCore.SEARCHQUEUE.pause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog paused")
        else:
            sickrage.srCore.SEARCHQUEUE.unpause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog unpaused")


class CMD_SiCKRAGEPing(ApiCall):
    _help = {"desc": "Ping SiCKRAGE to check if it is running"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEPing, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Ping SiCKRAGE to check if it is running """
        if sickrage.srConfig.STARTED:
            return _responds(RESULT_SUCCESS, {"pid": sickrage.srCore.PID}, "Pong")
        else:
            return _responds(RESULT_SUCCESS, msg="Pong")


class CMD_SiCKRAGERestart(ApiCall):
    _help = {"desc": "Restart SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGERestart, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Restart SiCKRAGE """

        if sickrage.srCore.WEBSERVER:
            sickrage.srCore.WEBSERVER.server_restart()
            return _responds(RESULT_SUCCESS, msg="SiCKRAGE is restarting...")
        return _responds(RESULT_FAILURE, msg='SiCKRAGE can not be restarted')


class CMD_SiCKRAGESearchIndexers(ApiCall):
    _help = {
        "desc": "Search for a show with a given name on all the indexers, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "indexerid": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        self.valid_languages = sickrage.srCore.INDEXER_API().config[b'langabbv_to_id']
        # required
        # optional
        self.name, args = self.check_params("name", None, False, "string", [], *args, **kwargs)
        self.lang, args = self.check_params("lang", sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE, False, "string",
                                            self.valid_languages.keys(), *args, **kwargs)
        self.indexerid, args = self.check_params("indexerid", None, False, "int", [], *args, **kwargs)

        # super, missing, help
        super(CMD_SiCKRAGESearchIndexers, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Search for a show with a given name on all the indexers, in a specific language """

        results = []
        lang_id = self.valid_languages[self.lang]

        if self.name and not self.indexerid:  # only name was given
            for _indexer in sickrage.srCore.INDEXER_API().indexers if self.indexer == 0 else [int(self.indexer)]:
                lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(_indexer).api_params.copy()

                if self.lang and not self.lang == sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE:
                    lINDEXER_API_PARMS[b'language'] = self.lang

                lINDEXER_API_PARMS[b'actors'] = False
                lINDEXER_API_PARMS[b'custom_ui'] = AllShowsListUI

                t = sickrage.srCore.INDEXER_API(_indexer).indexer(**lINDEXER_API_PARMS)

                try:
                    apiData = t[str(self.name).encode()]
                except (indexer_shownotfound, indexer_showincomplete, indexer_error):
                    sickrage.srLogger.warning("API :: Unable to find show with id " + str(self.indexerid))
                    continue

                for curSeries in apiData:
                    results.append({indexer_ids[_indexer]: int(curSeries[b'id']),
                                    "name": curSeries[b'seriesname'],
                                    "first_aired": curSeries[b'firstaired'],
                                    "indexer": int(_indexer)})

            return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})

        elif self.indexerid:
            for _indexer in sickrage.srCore.INDEXER_API().indexers if self.indexer == 0 else [int(self.indexer)]:
                lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(_indexer).api_params.copy()

                if self.lang and not self.lang == sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE:
                    lINDEXER_API_PARMS[b'language'] = self.lang

                lINDEXER_API_PARMS[b'actors'] = False

                t = sickrage.srCore.INDEXER_API(_indexer).indexer(**lINDEXER_API_PARMS)

                try:
                    myShow = t[int(self.indexerid)]
                except (indexer_shownotfound, indexer_showincomplete, indexer_error):
                    sickrage.srLogger.warning("API :: Unable to find show with id " + str(self.indexerid))
                    return _responds(RESULT_SUCCESS, {"results": [], "langid": lang_id})

                if not myShow.data[b'seriesname']:
                    sickrage.srLogger.debug(
                            "API :: Found show with indexerid: " + str(
                                    self.indexerid) + ", however it contained no show name")
                    return _responds(RESULT_FAILURE, msg="Show contains no name, invalid result")

                # found show
                results = [{indexer_ids[_indexer]: int(myShow.data[b'id']),
                            "name": unicode(myShow.data[b'seriesname']),
                            "first_aired": myShow.data[b'firstaired'],
                            "indexer": int(_indexer)}]
                break

            return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})
        else:
            return _responds(RESULT_FAILURE, msg="Either a unique id or name is required!")


class CMD_SiCKRAGESearchTVDB(CMD_SiCKRAGESearchIndexers):
    _help = {
        "desc": "Search for a show with a given name on The TVDB, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGESearchTVDB, self).__init__(application, request, *args, **kwargs)
        self.indexerid, args = self.check_params("tvdbid", None, False, "int", [], *args, **kwargs)


class CMD_SiCKRAGESearchTVRAGE(CMD_SiCKRAGESearchIndexers):
    """
    Deprecated, TVRage is no more.
    """

    _help = {
        "desc":
            "Search for a show with a given name on TVRage, in a specific language. "
            "This command should not longer be used, as TVRage was shut down.",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # Leave this one as APICall so it doesnt try and search anything
        # pylint: disable=W0233,W0231
        super(CMD_SiCKRAGESearchTVRAGE, self).__init__(application, request, *args, **kwargs)

    def run(self):
        return _responds(RESULT_FAILURE, msg="TVRage is disabled, invalid result")


class CMD_SiCKRAGESetDefaults(ApiCall):
    _help = {
        "desc": "Set SiCKRAGE's user default configuration value",
        "optionalParameters": {
            "initial": {"desc": "The initial quality of a show"},
            "archive": {"desc": "The archive quality of a show"},
            "future_show_paused": {"desc": "True to list paused shows in the coming episode, False otherwise"},
            "flatten_folders": {"desc": "Flatten sub-folders within the show directory"},
            "status": {"desc": "Status of missing episodes"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.initial, args = self.check_params("initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"], *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"], *args, **kwargs)
        self.future_show_paused, args = self.check_params("future_show_paused", None, False, "bool", [], *args,
                                                          **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders", None, False, "bool", [], *args, **kwargs)
        self.status, args = self.check_params("status", None, False, "string", ["wanted", "skipped", "ignored"], args,
                                              kwargs)
        # super, missing, help
        super(CMD_SiCKRAGESetDefaults, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Set SiCKRAGE's user default configuration value """

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        iqualityID = []
        aqualityID = []

        if self.initial:
            for quality in self.initial:
                iqualityID.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                aqualityID.append(quality_map[quality])

        if iqualityID or aqualityID:
            sickrage.srConfig.QUALITY_DEFAULT = Quality.combineQualities(iqualityID, aqualityID)

        if self.status:
            # convert the string status to a int
            for status in statusStrings.statusStrings:
                if statusStrings[status].lower() == str(self.status).lower():
                    self.status = status
                    break
            # this should be obsolete bcause of the above
            if not self.status in statusStrings.statusStrings:
                raise ApiError("Invalid Status")
            # only allow the status options we want
            if int(self.status) not in (3, 5, 6, 7):
                raise ApiError("Status Prohibited")
            sickrage.srConfig.STATUS_DEFAULT = self.status

        if self.flatten_folders is not None:
            sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT = int(self.flatten_folders)

        if self.future_show_paused is not None:
            sickrage.srConfig.COMING_EPS_DISPLAY_PAUSED = int(self.future_show_paused)

        return _responds(RESULT_SUCCESS, msg="Saved defaults")


class CMD_SiCKRAGEShutdown(ApiCall):
    _help = {"desc": "Shutdown SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEShutdown, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Shutdown SiCKRAGE """
        if sickrage.srCore.WEBSERVER:
            sickrage.srCore.WEBSERVER.server_shutdown()
            return _responds(RESULT_SUCCESS, msg="SiCKRAGE is shutting down...")
        return _responds(RESULT_FAILURE, msg='SiCKRAGE can not be shut down')


class CMD_SiCKRAGEUpdate(ApiCall):
    _help = {"desc": "Update SiCKRAGE to the latest version available"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_SiCKRAGEUpdate, self).__init__(application, request, *args, **kwargs)

    def run(self):
        if sickrage.srCore.VERSIONUPDATER.check_for_new_version():
            if sickrage.srCore.VERSIONUPDATER.run_backup_if_safe():
                sickrage.srCore.VERSIONUPDATER.update()

                return _responds(RESULT_SUCCESS, msg="SiCKRAGE is updating ...")

            return _responds(RESULT_FAILURE, msg="SiCKRAGE could not backup config ...")

        return _responds(RESULT_FAILURE, msg="SiCKRAGE is already up to date")


class CMD_Show(ApiCall):
    _help = {
        "desc": "Get detailed information about a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_Show, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get detailed information about a show """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        showDict = {
            "season_list": CMD_ShowSeasonList(self.application, self.request, **{"indexerid": self.indexerid}).run()[
                "data"],
            "cache": CMD_ShowCache(self.application, self.request, **{"indexerid": self.indexerid}).run()["data"]
        }

        genreList = []
        if showObj.genre:
            genreListTmp = showObj.genre.split("|")
            for genre in genreListTmp:
                if genre:
                    genreList.append(genre)

        showDict[b"genre"] = genreList
        showDict[b"quality"] = get_quality_string(showObj.quality)

        anyQualities, bestQualities = _mapQuality(showObj.quality)
        showDict[b"quality_details"] = {"initial": anyQualities, "archive": bestQualities}

        try:
            showDict[b"location"] = showObj.location
        except ShowDirectoryNotFoundException:
            showDict[b"location"] = ""

        showDict[b"language"] = showObj.lang
        showDict[b"show_name"] = showObj.name
        showDict[b"paused"] = (0, 1)[showObj.paused]
        showDict[b"subtitles"] = (0, 1)[showObj.subtitles]
        showDict[b"air_by_date"] = (0, 1)[showObj.air_by_date]
        showDict[b"flatten_folders"] = (0, 1)[showObj.flatten_folders]
        showDict[b"sports"] = (0, 1)[showObj.sports]
        showDict[b"anime"] = (0, 1)[showObj.anime]
        showDict[b"airs"] = str(showObj.airs).replace('am', ' AM').replace('pm', ' PM').replace('  ', ' ')
        showDict[b"dvdorder"] = (0, 1)[showObj.dvdorder]

        if showObj.rls_require_words:
            showDict[b"rls_require_words"] = showObj.rls_require_words.split(", ")
        else:
            showDict[b"rls_require_words"] = []

        if showObj.rls_ignore_words:
            showDict[b"rls_ignore_words"] = showObj.rls_ignore_words.split(", ")
        else:
            showDict[b"rls_ignore_words"] = []

        showDict[b"scene"] = (0, 1)[showObj.scene]
        showDict[b"archive_firstmatch"] = (0, 1)[showObj.archive_firstmatch]

        showDict[b"indexerid"] = showObj.indexerid
        showDict[b"tvdbid"] = showObj.mapIndexers()[1]
        showDict[b"imdbid"] = showObj.imdbid

        showDict[b"network"] = showObj.network
        if not showDict[b"network"]:
            showDict[b"network"] = ""
        showDict[b"status"] = showObj.status

        if tryInt(showObj.nextaired, 1) > 693595:
            dtEpisodeAirs = srdatetime.srDateTime.convert_to_setting(
                    tz_updater.parse_date_time(showObj.nextaired, showDict[b'airs'], showDict[b'network']))
            showDict[b'airs'] = srdatetime.srDateTime.srftime(dtEpisodeAirs, t_preset=timeFormat).lstrip('0').replace(
                    ' 0', ' ')
            showDict[b'next_ep_airdate'] = srdatetime.srDateTime.srfdate(dtEpisodeAirs, d_preset=dateFormat)
        else:
            showDict[b'next_ep_airdate'] = ''

        return _responds(RESULT_SUCCESS, showDict)


class CMD_ShowAddExisting(ApiCall):
    _help = {
        "desc": "Add an existing show in SiCKRAGE",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "location": {"desc": "Full path to the existing shows's folder"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "", [], *args, **kwargs)
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)
        # optional
        self.initial, args = self.check_params("initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"], *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"], *args, **kwargs)
        self.archive_firstmatch, args = self.check_params("archive_firstmatch", None, False, "int", [], *args, **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders", bool(
            sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT),
                                                       False, "bool", [], *args, **kwargs)
        self.subtitles, args = self.check_params("subtitles", int(sickrage.srConfig.USE_SUBTITLES), False, "int", [], args,
                                                 kwargs)
        # super, missing, help
        super(CMD_ShowAddExisting, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Add an existing show in SiCKRAGE """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if showObj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in the database")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg='Not a valid location')

        indexerName = None
        indexerResult = CMD_SiCKRAGESearchIndexers([], {indexer_ids[self.indexer]: self.indexerid}).run()

        if indexerResult[b'result'] == result_type_map[RESULT_SUCCESS]:
            if not indexerResult[b'data'][b'results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexerResult[b'data'][b'results']) == 1 and 'name' in indexerResult[b'data'][b'results'][0]:
                indexerName = indexerResult[b'data'][b'results'][0][b'name']

        if not indexerName:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer so we can pass it along when adding show to SR
        indexer = indexerResult[b'data'][b'results'][0][b'indexer']

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a failsafe
        newQuality = int(sickrage.srConfig.QUALITY_DEFAULT)
        iqualityID = []
        aqualityID = []

        if self.initial:
            for quality in self.initial:
                iqualityID.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                aqualityID.append(quality_map[quality])

        if iqualityID or aqualityID:
            newQuality = Quality.combineQualities(iqualityID, aqualityID)

        sickrage.srCore.SHOWQUEUE.addShow(
                int(indexer), int(self.indexerid), self.location, default_status=sickrage.srConfig.STATUS_DEFAULT,
                quality=newQuality, flatten_folders=int(self.flatten_folders), subtitles=self.subtitles,
                default_status_after=sickrage.srConfig.STATUS_DEFAULT_AFTER, archive=self.archive_firstmatch
        )

        return _responds(RESULT_SUCCESS, {"name": indexerName}, indexerName + " has been queued to be added")


class CMD_ShowAddNew(ApiCall):
    _help = {
        "desc": "Add a new show to SiCKRAGE",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "location": {"desc": "The path to the folder where the show should be created"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "status": {"desc": "The status of missing episodes"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
            "anime": {"desc": "True to mark the show as an anime, False otherwise"},
            "scene": {"desc": "True if episodes search should be made by scene numbering, False otherwise"},
            "future_status": {"desc": "The status of future episodes"},
            "archive_firstmatch": {
                "desc": "True if episodes should be archived when first match is downloaded, False otherwise"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        self.valid_languages = sickrage.srCore.INDEXER_API().config[b'langabbv_to_id']
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        self.location, args = self.check_params("location", None, False, "string", [], *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"], *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"], *args, **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders", bool(
            sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT),
                                                       False, "bool", [], *args, **kwargs)
        self.status, args = self.check_params("status", None, False, "string", ["wanted", "skipped", "ignored"], args,
                                              kwargs)
        self.lang, args = self.check_params("lang", sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE, False, "string",
                                            self.valid_languages.keys(), *args, **kwargs)
        self.subtitles, args = self.check_params("subtitles", bool(sickrage.srConfig.USE_SUBTITLES), False, "bool", [], args,
                                                 kwargs)
        self.anime, args = self.check_params("anime", bool(sickrage.srConfig.ANIME_DEFAULT), False, "bool", [], *args, **kwargs)
        self.scene, args = self.check_params("scene", bool(sickrage.srConfig.SCENE_DEFAULT), False, "bool", [], *args, **kwargs)
        self.future_status, args = self.check_params("future_status", None, False, "string",
                                                     ["wanted", "skipped", "ignored"], *args, **kwargs)
        self.archive_firstmatch, args = self.check_params("archive_firstmatch", bool(sickrage.srConfig.ARCHIVE_DEFAULT), False,
                                                          "bool", [], *args, **kwargs)

        # super, missing, help
        super(CMD_ShowAddNew, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Add a new show to SiCKRAGE """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if showObj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in database")

        if not self.location:
            if sickrage.srConfig.ROOT_DIRS != "":
                root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')
                root_dirs.pop(0)
                default_index = int(sickrage.srConfig.ROOT_DIRS.split('|')[0])
                self.location = root_dirs[default_index]
            else:
                return _responds(RESULT_FAILURE, msg="Root directory is not set, please provide a location")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="'" + self.location + "' is not a valid location")

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a failsafe
        newQuality = int(sickrage.srConfig.QUALITY_DEFAULT)
        iqualityID = []
        aqualityID = []

        if self.initial:
            for quality in self.initial:
                iqualityID.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                aqualityID.append(quality_map[quality])

        if iqualityID or aqualityID:
            newQuality = Quality.combineQualities(iqualityID, aqualityID)

        # use default status as a failsafe
        newStatus = sickrage.srConfig.STATUS_DEFAULT
        if self.status:
            # convert the string status to a int
            for status in statusStrings.statusStrings:
                if statusStrings[status].lower() == str(self.status).lower():
                    self.status = status
                    break

            if self.status not in statusStrings.statusStrings:
                raise ApiError("Invalid Status")

            # only allow the status options we want
            if int(self.status) not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            newStatus = self.status

        # use default status as a failsafe
        default_ep_status_after = sickrage.srConfig.STATUS_DEFAULT_AFTER
        if self.future_status:
            # convert the string status to a int
            for status in statusStrings.statusStrings:
                if statusStrings[status].lower() == str(self.future_status).lower():
                    self.future_status = status
                    break

            if self.future_status not in statusStrings.statusStrings:
                raise ApiError("Invalid Status")

            # only allow the status options we want
            if int(self.future_status) not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            default_ep_status_after = self.future_status

        indexerName = None
        indexerResult = CMD_SiCKRAGESearchIndexers([], {indexer_ids[self.indexer]: self.indexerid}).run()

        if indexerResult[b'result'] == result_type_map[RESULT_SUCCESS]:
            if not indexerResult[b'data'][b'results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexerResult[b'data'][b'results']) == 1 and 'name' in indexerResult[b'data'][b'results'][0]:
                indexerName = indexerResult[b'data'][b'results'][0][b'name']

        if not indexerName:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer for found show so we can pass it along
        indexer = indexerResult[b'data'][b'results'][0][b'indexer']

        # moved the logic check to the end in an attempt to eliminate empty directory being created from previous errors
        showPath = os.path.join(self.location, sanitizeFileName(indexerName))

        # don't create show dir if config says not to
        if sickrage.srConfig.ADD_SHOWS_WO_DIR:
            sickrage.srLogger.info("Skipping initial creation of " + showPath + " due to config.ini setting")
        else:
            dir_exists = makeDir(showPath)
            if not dir_exists:
                sickrage.srLogger.error("API :: Unable to create the folder " + showPath + ", can't add the show")
                return _responds(RESULT_FAILURE, {"path": showPath},
                                 "Unable to create the folder " + showPath + ", can't add the show")
            else:
                chmodAsParent(showPath)

        sickrage.srCore.SHOWQUEUE.addShow(
                int(indexer), int(self.indexerid), showPath, default_status=newStatus, quality=newQuality,
                flatten_folders=int(self.flatten_folders), lang=self.lang, subtitles=self.subtitles, anime=self.anime,
                scene=self.scene, default_status_after=default_ep_status_after, archive=self.archive_firstmatch
        )

        return _responds(RESULT_SUCCESS, {"name": indexerName}, indexerName + " has been queued to be added")


class CMD_ShowCache(ApiCall):
    _help = {
        "desc": "Check SiCKRAGE's cache to see if the images (poster, banner, fanart) for a show are valid",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowCache, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Check SiCKRAGE's cache to see if the images (poster, banner, fanart) for a show are valid """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # TODO: catch if cache dir is missing/invalid.. so it doesn't break show/show.cache
        # return {"poster": 0, "banner": 0}

        cache_obj = image_cache.ImageCache()

        has_poster = 0
        has_banner = 0

        if os.path.isfile(cache_obj.poster_path(showObj.indexerid)):
            has_poster = 1
        if os.path.isfile(cache_obj.banner_path(showObj.indexerid)):
            has_banner = 1

        return _responds(RESULT_SUCCESS, {"poster": has_poster, "banner": has_banner})


class CMD_ShowDelete(ApiCall):
    _help = {
        "desc": "Delete a show in SiCKRAGE",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "removefiles": {
                "desc": "True to delete the files associated with the show, False otherwise. This can not be undone!"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        self.removefiles, args = self.check_params("removefiles", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_ShowDelete, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Delete a show in SiCKRAGE """
        error, show = TVShow.delete(self.indexerid, self.removefiles)

        if error is not None:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='%s has been queued to be deleted' % show.name)


class CMD_ShowGetQuality(ApiCall):
    _help = {
        "desc": "Get the quality setting of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowGetQuality, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the quality setting of a show """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        anyQualities, bestQualities = _mapQuality(showObj.quality)

        return _responds(RESULT_SUCCESS, {"initial": anyQualities, "archive": bestQualities})


class CMD_ShowGetPoster(ApiCall):
    _help = {
        "desc": "Get the poster of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowGetPoster, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the poster a show """
        return {
            'outputType': 'image',
            'image': Poster(self.indexerid),
        }


class CMD_ShowGetBanner(ApiCall):
    _help = {
        "desc": "Get the banner of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowGetBanner, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the banner of a show """
        return {
            'outputType': 'image',
            'image': Banner(self.indexerid),
        }


class CMD_ShowGetNetworkLogo(ApiCall):
    _help = {
        "desc": "Get the network logo of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowGetNetworkLogo, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """
        :return: Get the network logo of a show
        """
        return {
            'outputType': 'image',
            'image': Network(self.indexerid),
        }


class CMD_ShowGetFanArt(ApiCall):
    _help = {
        "desc": "Get the fan art of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowGetFanArt, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the fan art of a show """
        return {
            'outputType': 'image',
            'image': FanArt(self.indexerid),
        }


class CMD_ShowPause(ApiCall):
    _help = {
        "desc": "Pause or unpause a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "pause": {"desc": "True to pause the show, False otherwise"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        self.pause, args = self.check_params("pause", False, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_ShowPause, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Pause or unpause a show """
        error, show = TVShow.pause(self.indexerid, self.pause)

        if error is not None:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='%s has been %s' % (show.name, ('resumed', 'paused')[show.paused]))


class CMD_ShowRefresh(ApiCall):
    _help = {
        "desc": "Refresh a show in SiCKRAGE",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowRefresh, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Refresh a show in SiCKRAGE """
        error, show = TVShow.refresh(self.indexerid)

        if error is not None:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='%s has queued to be refreshed' % show.name)


class CMD_ShowSeasonList(ApiCall):
    _help = {
        "desc": "Get the list of seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "sort": {"desc": "Return the seasons in ascending or descending order"}
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        self.sort, args = self.check_params("sort", "desc", False, "string", ["asc", "desc"], *args, **kwargs)
        # super, missing, help
        super(CMD_ShowSeasonList, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the list of seasons of a show """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        if self.sort == "asc":
            sqlResults = main_db.MainDB(row_type='dict').select(
                    "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season ASC",
                    [self.indexerid])
        else:
            sqlResults = main_db.MainDB(row_type='dict').select(
                    "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season DESC",
                    [self.indexerid])
        seasonList = []  # a list with all season numbers
        for row in sqlResults:
            seasonList.append(int(row[b"season"]))

        return _responds(RESULT_SUCCESS, seasonList)


class CMD_ShowSeasons(ApiCall):
    _help = {
        "desc": "Get the list of episodes for one or all seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "season": {"desc": "The season number"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        self.season, args = self.check_params("season", None, False, "int", [], *args, **kwargs)
        # super, missing, help
        super(CMD_ShowSeasons, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the list of episodes for one or all seasons of a show """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        if self.season is None:
            sqlResults = main_db.MainDB(row_type='dict').select(
                    "SELECT name, episode, airdate, status, release_name, season, location, file_size, subtitles FROM tv_episodes WHERE showid = ?",
                    [self.indexerid])
            seasons = {}
            for row in sqlResults:
                status, quality = Quality.splitCompositeStatus(int(row[b"status"]))
                row[b"status"] = _get_status_Strings(status)
                row[b"quality"] = get_quality_string(quality)
                if tryInt(row[b'airdate'], 1) > 693595:  # 1900
                    dtEpisodeAirs = srdatetime.srDateTime.convert_to_setting(
                            tz_updater.parse_date_time(row[b'airdate'], showObj.airs, showObj.network))
                    row[b'airdate'] = srdatetime.srDateTime.srfdate(dtEpisodeAirs, d_preset=dateFormat)
                else:
                    row[b'airdate'] = 'Never'
                curSeason = int(row[b"season"])
                curEpisode = int(row[b"episode"])
                del row[b"season"]
                del row[b"episode"]
                if not curSeason in seasons:
                    seasons[curSeason] = {}
                seasons[curSeason][curEpisode] = row

        else:
            sqlResults = main_db.MainDB(row_type='dict').select(
                    "SELECT name, episode, airdate, status, location, file_size, release_name, subtitles FROM tv_episodes WHERE showid = ? AND season = ?",
                    [self.indexerid, self.season])
            if len(sqlResults) is 0:
                return _responds(RESULT_FAILURE, msg="Season not found")
            seasons = {}
            for row in sqlResults:
                curEpisode = int(row[b"episode"])
                del row[b"episode"]
                status, quality = Quality.splitCompositeStatus(int(row[b"status"]))
                row[b"status"] = _get_status_Strings(status)
                row[b"quality"] = get_quality_string(quality)
                if tryInt(row[b'airdate'], 1) > 693595:  # 1900
                    dtEpisodeAirs = srdatetime.srDateTime.convert_to_setting(
                            tz_updater.parse_date_time(row[b'airdate'], showObj.airs, showObj.network))
                    row[b'airdate'] = srdatetime.srDateTime.srfdate(dtEpisodeAirs, d_preset=dateFormat)
                else:
                    row[b'airdate'] = 'Never'
                if not curEpisode in seasons:
                    seasons[curEpisode] = {}
                seasons[curEpisode] = row

        return _responds(RESULT_SUCCESS, seasons)


class CMD_ShowSetQuality(ApiCall):
    _help = {
        "desc": "Set the quality setting of a show. If no quality is provided, the default user setting is used.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # this for whatever reason removes hdbluray not sdtv... which is just wrong. reverting to previous code.. plus we didnt use the new code everywhere.
        # self.archive, args = self.check_params("archive", None, False, "list", _getQualityMap().values()[1:], *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"], *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl",
                                                "hdbluray", "fullhdbluray"], *args, **kwargs)
        # super, missing, help
        super(CMD_ShowSetQuality, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Set the quality setting of a show. If no quality is provided, the default user setting is used. """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a failsafe
        newQuality = int(sickrage.srConfig.QUALITY_DEFAULT)
        iqualityID = []
        aqualityID = []

        if self.initial:
            for quality in self.initial:
                iqualityID.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                aqualityID.append(quality_map[quality])

        if iqualityID or aqualityID:
            newQuality = Quality.combineQualities(iqualityID, aqualityID)
        showObj.quality = newQuality

        return _responds(RESULT_SUCCESS,
                         msg=showObj.name + " quality has been changed to " + get_quality_string(showObj.quality))


class CMD_ShowStats(ApiCall):
    _help = {
        "desc": "Get episode statistics for a given show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowStats, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get episode statistics for a given show """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # show stats
        episode_status_counts_total = {}
        episode_status_counts_total[b"total"] = 0
        for status in statusStrings.statusStrings.keys():
            if status in [UNKNOWN, DOWNLOADED, SNATCHED, SNATCHED_PROPER, ARCHIVED]:
                continue
            episode_status_counts_total[status] = 0

        # add all the downloaded qualities
        episode_qualities_counts_download = {}
        episode_qualities_counts_download[b"total"] = 0
        for statusCode in Quality.DOWNLOADED + Quality.ARCHIVED:
            status, quality = Quality.splitCompositeStatus(statusCode)
            if quality in [Quality.NONE]:
                continue
            episode_qualities_counts_download[statusCode] = 0

        # add all snatched qualities
        episode_qualities_counts_snatch = {}
        episode_qualities_counts_snatch[b"total"] = 0
        for statusCode in Quality.SNATCHED + Quality.SNATCHED_PROPER:
            status, quality = Quality.splitCompositeStatus(statusCode)
            if quality in [Quality.NONE]:
                continue
            episode_qualities_counts_snatch[statusCode] = 0

        sqlResults = main_db.MainDB(row_type='dict').select(
                "SELECT status, season FROM tv_episodes WHERE season != 0 AND showid = ?", [self.indexerid])
        # the main loop that goes through all episodes
        for row in sqlResults:
            status, quality = Quality.splitCompositeStatus(int(row[b"status"]))

            episode_status_counts_total[b"total"] += 1

            if status in Quality.DOWNLOADED + Quality.ARCHIVED:
                episode_qualities_counts_download[b"total"] += 1
                episode_qualities_counts_download[int(row[b"status"])] += 1
            elif status in Quality.SNATCHED + Quality.SNATCHED_PROPER:
                episode_qualities_counts_snatch[b"total"] += 1
                episode_qualities_counts_snatch[int(row[b"status"])] += 1
            elif status == 0:  # we dont count NONE = 0 = N/A
                pass
            else:
                episode_status_counts_total[status] += 1

        # the outgoing container
        episodes_stats = {}
        episodes_stats[b"downloaded"] = {}
        # turning codes into strings
        for statusCode in episode_qualities_counts_download:
            if statusCode == "total":
                episodes_stats[b"downloaded"][b"total"] = episode_qualities_counts_download[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            statusString = Quality.qualityStrings[quality].lower().replace(" ", "_").replace("(", "").replace(
                    ")", "")
            episodes_stats[b"downloaded"][statusString] = episode_qualities_counts_download[statusCode]

        episodes_stats[b"snatched"] = {}
        # truning codes into strings
        # and combining proper and normal
        for statusCode in episode_qualities_counts_snatch:
            if statusCode == "total":
                episodes_stats[b"snatched"][b"total"] = episode_qualities_counts_snatch[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            statusString = Quality.qualityStrings[quality].lower().replace(" ", "_").replace("(", "").replace(
                    ")", "")
            if Quality.qualityStrings[quality] in episodes_stats[b"snatched"]:
                episodes_stats[b"snatched"][statusString] += episode_qualities_counts_snatch[statusCode]
            else:
                episodes_stats[b"snatched"][statusString] = episode_qualities_counts_snatch[statusCode]

        # episodes_stats[b"total"] = {}
        for statusCode in episode_status_counts_total:
            if statusCode == "total":
                episodes_stats[b"total"] = episode_status_counts_total[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            statusString = statusStrings.statusStrings[statusCode].lower().replace(" ", "_").replace("(",
                                                                                                     "").replace(
                    ")", "")
            episodes_stats[statusString] = episode_status_counts_total[statusCode]

        return _responds(RESULT_SUCCESS, episodes_stats)


class CMD_ShowUpdate(ApiCall):
    _help = {
        "desc": "Update a show in SiCKRAGE",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        self.indexerid, args = self.check_params("indexerid", None, True, "int", [], *args, **kwargs)
        # optional
        # super, missing, help
        super(CMD_ShowUpdate, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Update a show in SiCKRAGE """
        showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(self.indexerid))
        if not showObj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            sickrage.srCore.SHOWQUEUE.updateShow(showObj, True)  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg=str(showObj.name) + " has queued to be updated")
        except CantUpdateShowException as e:
            sickrage.srLogger.debug("API::Unable to update show: {0}".format(str(e)))
            return _responds(RESULT_FAILURE, msg="Unable to update " + str(showObj.name))


class CMD_Shows(ApiCall):
    _help = {
        "desc": "Get all shows in SiCKRAGE",
        "optionalParameters": {
            "sort": {"desc": "The sorting strategy to apply to the list of shows"},
            "paused": {"desc": "True to include paused shows, False otherwise"},
        },
    }

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        self.sort, args = self.check_params("sort", "id", False, "string", ["id", "name"], *args, **kwargs)
        self.paused, args = self.check_params("paused", None, False, "bool", [], *args, **kwargs)
        # super, missing, help
        super(CMD_Shows, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get all shows in SiCKRAGE """
        shows = {}
        for curShow in sickrage.srCore.SHOWLIST:

            if self.paused is not None and bool(self.paused) != bool(curShow.paused):
                continue

            indexerShow = curShow.mapIndexers()

            showDict = {
                "paused": (0, 1)[curShow.paused],
                "quality": get_quality_string(curShow.quality),
                "language": curShow.lang,
                "air_by_date": (0, 1)[curShow.air_by_date],
                "sports": (0, 1)[curShow.sports],
                "anime": (0, 1)[curShow.anime],
                "indexerid": curShow.indexerid,
                "tvdbid": indexerShow[1],
                "network": curShow.network,
                "show_name": curShow.name,
                "status": curShow.status,
                "subtitles": (0, 1)[curShow.subtitles],
            }

            if tryInt(curShow.nextaired, 1) > 693595:  # 1900
                dtEpisodeAirs = srdatetime.srDateTime.convert_to_setting(
                        tz_updater.parse_date_time(curShow.nextaired, curShow.airs, showDict[b'network']))
                showDict[b'next_ep_airdate'] = srdatetime.srDateTime.srfdate(dtEpisodeAirs, d_preset=dateFormat)
            else:
                showDict[b'next_ep_airdate'] = ''

            showDict[b"cache"] = \
                CMD_ShowCache(self.application, self.request, **{"indexerid": curShow.indexerid}).run()[b"data"]
            if not showDict[b"network"]:
                showDict[b"network"] = ""
            if self.sort == "name":
                shows[curShow.name] = showDict
            else:
                shows[curShow.indexerid] = showDict

        return _responds(RESULT_SUCCESS, shows)


class CMD_ShowsStats(ApiCall):
    _help = {"desc": "Get the global shows and episodes statistics"}

    def __init__(self, application, request, *args, **kwargs):
        # required
        # optional
        # super, missing, help
        super(CMD_ShowsStats, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the global shows and episodes statistics """
        stats = TVShow.overall_stats()

        return _responds(RESULT_SUCCESS, {
            'ep_downloaded': stats[b'episodes'][b'downloaded'],
            'ep_snatched': stats[b'episodes'][b'snatched'],
            'ep_total': stats[b'episodes'][b'total'],
            'shows_active': stats[b'shows'][b'active'],
            'shows_total': stats[b'shows'][b'total'],
        })
