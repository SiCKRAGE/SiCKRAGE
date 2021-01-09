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
import collections
import datetime
import os
import re
import threading
import time
import traceback
from urllib.parse import unquote_plus

from sqlalchemy import orm
from tornado.escape import recursive_unicode, json_encode
from tornado.web import RequestHandler

import sickrage
from sickrage.core.caches import image_cache
from sickrage.core.common import dateFormat, dateTimeFormat, Overview, timeFormat, Quality, Qualities, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import ProcessMethod, SeriesProviderID
from sickrage.core.exceptions import EpisodeNotFoundException, CantRemoveShowException, CantRefreshShowException, CantUpdateShowException
from sickrage.core.helpers import backup_app_data, srdatetime, pretty_file_size, read_file_buffered, try_int, sanitize_file_name, chmod_as_parent, flatten, \
    make_dir
from sickrage.core.media.banner import Banner
from sickrage.core.media.fanart import FanArt
from sickrage.core.media.network import Network
from sickrage.core.media.poster import Poster
from sickrage.core.queues.search import ManualSearchTask, BacklogSearchTask
from sickrage.core.tv.show.coming_episodes import ComingEpisodes, ComingEpsSortBy
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.core.tv.show.history import History
from sickrage.series_providers.helpers import map_series_providers
from sickrage.subtitles import Subtitles

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

best_quality_list = [
    "sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl", "fullhdwebdl", "hdbluray", "fullhdbluray",
    "udh4ktv", "uhd4kbluray", "udh4kwebdl", "udh8ktv", "uhd8kbluray", "udh8kwebdl"
]

any_quality_list = best_quality_list + ["unknown"]


class ApiHandler(RequestHandler):
    """ api class that returns json results """
    version = 5  # use an int since float-point is unpredictable

    def prepare(self, *args, **kwargs):
        threading.currentThread().setName("API")

        # set the output callback
        # default json
        output_callback_dict = {
            'default': self._out_as_json,
            'image': self._out_as_image,
        }

        if sickrage.app.config.general.api_v1_key == self.path_args[0]:
            access_msg = "IP:{} - ACCESS GRANTED".format(self.request.remote_ip)
            sickrage.app.log.debug(access_msg)

            # set the original call_dispatcher as the local _call_dispatcher
            _call_dispatcher = self.call_dispatcher

            # if profile was set wrap "_call_dispatcher" in the profile function
            if 'profile' in self.request.arguments:
                from profilehooks import profile

                _call_dispatcher = profile(_call_dispatcher, immediate=True)
                del self.request.arguments["profile"]

            try:
                out_dict = self.route(_call_dispatcher, **self.request.arguments)
            except Exception as e:
                sickrage.app.log.error(str(e))
                error_data = {"error_msg": e, "request arguments": recursive_unicode(self.request.arguments)}
                out_dict = _responds(RESULT_FATAL, error_data, "SiCKRAGE encountered an internal error! Please report to the Devs")
        else:
            access_msg = "IP:{} - ACCESS DENIED".format(self.request.remote_ip)
            sickrage.app.log.debug(access_msg)

            error_data = {"error_msg": access_msg, "request arguments": recursive_unicode(self.request.arguments)}
            out_dict = _responds(RESULT_DENIED, error_data, access_msg)

        output_callback = output_callback_dict['default']
        if 'outputType' in out_dict:
            output_callback = output_callback_dict[out_dict['outputType']]

        self.finish(output_callback(out_dict))

    def route(self, function, **kwargs):
        kwargs = recursive_unicode(kwargs)
        for arg, value in kwargs.items():
            if len(value) == 1:
                kwargs[arg] = value[0]

        return function(**kwargs)

    def _out_as_image(self, _dict):
        self.set_header('Content-Type', _dict['image'].type)
        return _dict['image'].content

    def _out_as_json(self, _dict):
        self.set_header("Content-Type", "application/json;charset=UTF-8")
        try:
            out = json_encode(_dict)
            callback = self.get_argument('callback', None) or self.get_argument('jsonp', None)
            if callback is not None:
                out = callback + '(' + out + ');'  # wrap with JSONP call if requested
        except Exception as e:  # if we fail to generate the output fake an error
            sickrage.app.log.debug(traceback.format_exc())
            out = '{"result": "%s", "message": "error while composing output: %s"}' % (result_type_map[RESULT_ERROR], e)
        return out

    @property
    def api_calls(self):
        """
        :return: api calls
        :rtype: Union[dict, object]
        """
        return dict((cls._cmd, cls) for cls in ApiCall.__subclasses__() if '_cmd' in cls.__dict__)

    def call_dispatcher(self, *args, **kwargs):
        """ calls the appropriate CMD class
            looks for a cmd in args and kwargs
            or calls the TVDBShorthandWrapper when the first args element is a number
            or returns an error that there is no such cmd
        """
        sickrage.app.log.debug("all params: '" + str(kwargs) + "'")

        cmds = []
        if args:
            cmds, args = args[0], args[1:]
        cmds = kwargs.pop("cmd", cmds)

        outDict = {}
        if not len(cmds):
            outDict = CMD_SiCKRAGE(self.application, self.request, *args, **kwargs).run()
        else:
            cmds = cmds.split('|')

        multiCmds = bool(len(cmds) > 1)

        for cmd in cmds:
            curArgs, curKwargs = self.filter_params(cmd, *args, **kwargs)
            cmdIndex = None
            if len(cmd.split("_")) > 1:  # was a index used for this cmd ?
                cmd, cmdIndex = cmd.split("_")  # this gives us the clear cmd and the index

            sickrage.app.log.debug(cmd + ": current params " + str(curKwargs))
            if not (multiCmds and cmd in ('show.getbanner', 'show.getfanart', 'show.getnetworklogo',
                                          'show.getposter')):  # skip these cmd while chaining
                try:
                    # backport old sb calls
                    cmd = (cmd, 'sr' + cmd[2:])[cmd[:2] == 'sb']

                    if cmd in self.api_calls:
                        # call function and get response back
                        curOutDict = self.api_calls[cmd](self.application, self.request, *curArgs, **curKwargs).run()
                    elif _is_int(cmd):
                        curOutDict = TVDBShorthandWrapper(cmd, self.application, self.request, *curArgs, **curKwargs).run()
                    else:
                        curOutDict = _responds(RESULT_ERROR, "No such cmd: '" + cmd + "'")
                except InternalApiError as e:  # Api errors that we raised, they are harmless
                    curOutDict = _responds(RESULT_ERROR, msg=str(e))
            else:  # if someone chained one of the forbiden cmds they will get an error for this one cmd
                curOutDict = _responds(RESULT_ERROR, msg="The cmd '" + cmd + "' is not supported while chaining")

            if multiCmds:
                # note: if multiple same cmds are issued but one has not an index defined it will override all others
                # or the other way around, this depends on the order of the cmds
                # this is not a bug
                if cmdIndex:  # do we need a index dict for this cmd ?
                    if cmd not in outDict:
                        outDict[cmd] = {}
                    outDict[cmd][cmdIndex] = curOutDict
                else:
                    outDict[cmd] = curOutDict
            else:
                outDict = curOutDict

        if multiCmds:
            outDict = _responds(RESULT_SUCCESS, outDict)

        return outDict

    def filter_params(self, cmd, *args, **kwargs):
        """ return only params kwargs that are for cmd
            and rename them to a clean version (remove "<cmd>_")
            args are shared across all cmds

            all args and kwarks are lowerd

            cmd are separated by "|" e.g. &cmd=shows|future
            kwargs are namespaced with "." e.g. show.series_id=101501
            if a karg has no namespace asing it anyways (global)

            full e.g.
            /api?apikey=1234&cmd=show.seasonlist_asd|show.seasonlist_2&show.seasonlist_asd.series_id=101501&show.seasonlist_2.series_id=79488&sort=asc

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


class ApiCall(ApiHandler):
    _help = {"desc": "This command is not documented. Please report this to the developers."}

    def __init__(self, application, request, *args, **kwargs):
        super(ApiCall, self).__init__(application, request)
        self._missing = []
        self._requiredParams = {}
        self._optionalParams = {}
        self.check_params(*args, **kwargs)

    def run(self):
        # override with real output function in subclass
        return {}

    def return_help(self):
        for paramDict, paramType in [(self._requiredParams, "requiredParameters"),
                                     (self._optionalParams, "optionalParameters")]:

            if paramType in self._help:
                for paramName in paramDict:
                    if paramName not in self._help[paramType]:
                        self._help[paramType][paramName] = {}
                    if paramDict[paramName]["allowedValues"]:
                        self._help[paramType][paramName]["allowedValues"] = paramDict[paramName]["allowedValues"]
                    else:
                        self._help[paramType][paramName]["allowedValues"] = "see desc"

                    self._help[paramType][paramName]["defaultValue"] = paramDict[paramName]["defaultValue"]
                    self._help[paramType][paramName]["type"] = paramDict[paramName]["type"]

            elif paramDict:
                for paramName in paramDict:
                    self._help[paramType] = {}
                    self._help[paramType][paramName] = paramDict[paramName]
            else:
                self._help[paramType] = {}

        msg = "No description available"
        if "desc" in self._help:
            msg = self._help["desc"]

        return _responds(RESULT_SUCCESS, self._help, msg)

    def return_missing(self):
        if len(self._missing) == 1:
            msg = "The required parameter: '" + self._missing[0] + "' was not set"
        else:
            msg = "The required parameters: '" + "','".join(self._missing) + "' where not set"
        return _responds(RESULT_ERROR, msg=msg)

    def check_params(self, key=None, default=None, required=None, arg_type=None, allowed_values=None, *args, **kwargs):

        """ function to check passed params for the shorthand wrapper
            and to detect missing/required params
        """

        if key:
            missing = True
            org_default = default

            if arg_type == "bool":
                allowed_values = [0, 1]

            if args:
                default = args[0]
                missing = False
                args = args[1:]
            if kwargs.get(key):
                default = kwargs.get(key)
                missing = False

            key_value = {
                "allowedValues": allowed_values,
                "defaultValue": org_default,
                "type": arg_type
            }

            if required:
                self._requiredParams[key] = key_value
                if missing and key not in self._missing:
                    self._missing.append(key)
            else:
                self._optionalParams[key] = key_value

            if default:
                default = self._check_param_type(default, key, arg_type)
                self._check_param_value(default, key, allowed_values)

        if self._missing:
            setattr(self, "run", self.return_missing)

        if 'help' in kwargs:
            setattr(self, "run", self.return_help)

        return default, args

    @staticmethod
    def _check_param_type(value, name, arg_type):
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
            sickrage.app.log.error('Invalid param type: "{}" can not be checked. Ignoring it.'.format(str(arg_type)))

        if error:
            raise InternalApiError(
                'param "{}" with given value "{}" could not be parsed into "{}"'.format(str(name), str(value),
                                                                                        str(arg_type)))

        return value

    @staticmethod
    def _check_param_value(value, name, allowed_values):
        """ will check if value (or all values in it ) are in allowed values
            will raise an exception if value is "out of range"
            if bool(allowed_value) is False a check is not performed and all values are excepted
        """
        if allowed_values:
            error = False
            if isinstance(value, list):
                for item in value:
                    if item not in allowed_values:
                        error = True
            else:
                if value not in allowed_values:
                    error = True

            if error:
                # this is kinda a InternalApiError but raising an error is the only way of quitting here
                raise InternalApiError("param: '" + str(name) + "' with given value: '" + str(
                    value) + "' is out of allowed range '" + str(allowed_values) + "'")


class TVDBShorthandWrapper(ApiCall):
    _help = {"desc": "This is an internal function wrapper. Call the help command directly for more information."}

    def __init__(self, sid, application, request, *args, **kwargs):
        super(TVDBShorthandWrapper, self).__init__(application, request, *args, **kwargs)

        self.origArgs = args
        self.kwargs = kwargs
        self.sid = sid

        self.s, args = self.check_params("s", None, False, "ignore", [], *args, **kwargs)
        self.e, args = self.check_params("e", None, False, "ignore", [], *args, **kwargs)
        self.args = args

    def run(self):
        """ internal function wrapper """
        args = (self.sid,) + self.origArgs
        if self.e:
            return CMD_Episode(self.application, self.request, *args, **self.kwargs).run()
        elif self.s:
            return CMD_ShowSeasons(self.application, self.request, *args, **self.kwargs).run()
        else:
            return CMD_Show(self.application, self.request, *args, **self.kwargs).run()


def _is_int(data):
    try:
        int(data)
    except (TypeError, ValueError, OverflowError):
        return False
    else:
        return True


def _responds(result_type, data=None, msg=""):
    """
    result is a string of given "type" (success/failure/timeout/error)
    message is a human readable string, can be empty
    data is either a dict or a array, can be a empty dict or empty array
    """

    return {"result": result_type_map[result_type], "message": msg, "data": data or {}}


def _map_quality(show_object):
    anyQualities = []
    bestQualities = []

    iqualityID, aqualityID = Quality.split_quality(int(show_object))
    for quality in iqualityID:
        anyQualities.append(_get_quality_map()[quality])
    for quality in aqualityID:
        bestQualities.append(_get_quality_map()[quality])
    return anyQualities, bestQualities


def _get_quality_map():
    return {
        Qualities.SDTV: 'sdtv',
        'sdtv': Qualities.SDTV,

        Qualities.SDDVD: 'sddvd',
        'sddvd': Qualities.SDDVD,

        Qualities.HDTV: 'hdtv',
        'hdtv': Qualities.HDTV,

        Qualities.RAWHDTV: 'rawhdtv',
        'rawhdtv': Qualities.RAWHDTV,

        Qualities.FULLHDTV: 'fullhdtv',
        'fullhdtv': Qualities.FULLHDTV,

        Qualities.HDWEBDL: 'hdwebdl',
        'hdwebdl': Qualities.HDWEBDL,

        Qualities.FULLHDWEBDL: 'fullhdwebdl',
        'fullhdwebdl': Qualities.FULLHDWEBDL,

        Qualities.HDBLURAY: 'hdbluray',
        'hdbluray': Qualities.HDBLURAY,

        Qualities.FULLHDBLURAY: 'fullhdbluray',
        'fullhdbluray': Qualities.FULLHDBLURAY,

        Qualities.UHD_4K_TV: 'uhd4ktv',
        'udh4ktv': Qualities.UHD_4K_TV,

        Qualities.UHD_4K_BLURAY: '4kbluray',
        'uhd4kbluray': Qualities.UHD_4K_BLURAY,

        Qualities.UHD_4K_WEBDL: '4kwebdl',
        'udh4kwebdl': Qualities.UHD_4K_WEBDL,

        Qualities.UHD_8K_TV: 'uhd8ktv',
        'udh8ktv': Qualities.UHD_8K_TV,

        Qualities.UHD_8K_BLURAY: 'uhd8kbluray',
        'uhd8kbluray': Qualities.UHD_8K_BLURAY,

        Qualities.UHD_8K_WEBDL: 'udh8kwebdl',
        "udh8kwebdl": Qualities.UHD_8K_WEBDL,

        Qualities.UNKNOWN: 'unknown',
        'unknown': Qualities.UNKNOWN
    }


def _get_root_dirs():
    if sickrage.app.config.general.root_dirs == "":
        return {}

    rootDir = {}
    root_dirs = sickrage.app.config.general.root_dirs.split('|')
    default_index = int(sickrage.app.config.general.root_dirs.split('|')[0])

    rootDir["default_index"] = int(sickrage.app.config.general.root_dirs.split('|')[0])
    # remove default_index value from list (this fixes the offset)
    root_dirs.pop(0)

    if len(root_dirs) < default_index:
        return {}

    # clean up the list - replace %xx escapes by their single-character equivalent
    root_dirs = [unquote_plus(x) for x in root_dirs]

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

        curDir = {'valid': valid, 'location': root_dir, 'default': default}
        dir_list.append(curDir)

    return dir_list


class InternalApiError(Exception):
    """
    Generic API error
    """


class IntParseError(Exception):
    """
    A value could not be parsed into an int, but should be parsable to an int
    """


class CMD_Help(ApiCall):
    _cmd = "help"
    _help = {
        "desc": "Get help about a given command",
        "optionalParameters": {
            "subject": {"desc": "The name of the command to get the help of"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Help, self).__init__(application, request, *args, **kwargs)
        self.subject, args = self.check_params("subject", "help", False, "string", self.api_calls.keys(), *args,
                                               **kwargs)

    def run(self):
        """ Get help about a given command """
        if self.subject in self.api_calls:
            api_func = self.api_calls.get(self.subject)
            out = api_func(self.application, self.request, **{"help": 1}).run()
        else:
            out = _responds(RESULT_FAILURE, msg="No such cmd")
        return out


class CMD_Backup(ApiCall):
    _cmd = "backup"
    _help = {
        "desc": "Backup application data files",
        "requiredParameters": {
            "backup_dir": {"desc": "Directory to store backup files"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Backup, self).__init__(application, request, *args, **kwargs)
        self.backup_dir, args = self.check_params("backup_dir", sickrage.app.data_dir, True, "string", [], *args,
                                                  **kwargs)

    def run(self):
        """ Performs application backup """
        if backup_app_data(self.backup_dir):
            response = _responds(RESULT_SUCCESS, msg='Backup successful')
        else:
            response = _responds(RESULT_FAILURE, msg='Backup failed')

        return response


class CMD_ComingEpisodes(ApiCall):
    _cmd = "future"
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
        super(CMD_ComingEpisodes, self).__init__(application, request, *args, **kwargs)
        self.sort, args = self.check_params("sort", ComingEpsSortBy.DATE, False, "string", [x.name.lower() for x in ComingEpsSortBy], *args, **kwargs)
        self.type, args = self.check_params("type", '|'.join(ComingEpisodes.categories), False, "list", ComingEpisodes.categories, *args, **kwargs)
        self.paused, args = self.check_params("paused", bool(sickrage.app.config.gui.coming_eps_display_paused), False, "bool", [], *args, **kwargs)

    def run(self):
        """ Get the coming episodes """
        grouped_coming_episodes = ComingEpisodes.get_coming_episodes(self.type, ComingEpsSortBy[self.sort.upper()], True, self.paused)
        data = dict([(section, []) for section in grouped_coming_episodes.keys()])

        for section, coming_episodes in grouped_coming_episodes.items():
            for coming_episode in coming_episodes:
                data[section].append({
                    'airdate': coming_episode['airdate'],
                    'airs': coming_episode['airs'],
                    'ep_name': coming_episode['name'],
                    'ep_plot': coming_episode['description'],
                    'episode': coming_episode['episode'],
                    'episode_id': coming_episode['episode_id'],
                    'network': coming_episode['network'],
                    'paused': coming_episode['paused'],
                    'quality': coming_episode['quality'],
                    'season': coming_episode['season'],
                    'show_name': coming_episode['show_name'],
                    'show_status': coming_episode['status'],
                    'series_id': coming_episode['series_id'],
                    'series_provider_id': coming_episode['series_provider_id'],
                    'weekday': coming_episode['weekday']
                })

        return _responds(RESULT_SUCCESS, data)


class CMD_Episode(ApiCall):
    _cmd = "episode"
    _help = {
        "desc": "Get detailed information about an episode",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
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
        super(CMD_Episode, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)
        self.fullPath, args = self.check_params("full_path", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Get detailed information about an episode """
        session = sickrage.app.main_db.session()

        show_obj = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            db_data = session.query(MainDB.TVEpisode).filter_by(series_id=self.series_id, season=self.s, episode=self.e).one()
            episode_result = db_data.as_dict()

            show_path = show_obj.location

            # handle path options
            # absolute vs relative vs broken
            if bool(self.fullPath) is True and os.path.isdir(show_path):
                pass
            elif bool(self.fullPath) is False and os.path.isdir(show_path):
                # using the length because lstrip removes to much
                show_path_length = len(show_path) + 1  # the / or \ yeah not that nice i know
                episode_result['location'] = episode_result['location'][show_path_length:]
            elif not os.path.isdir(show_path):  # show dir is broken ... episode path will be empty
                episode_result['location'] = ""

            # convert stuff to human form
            if episode_result['airdate'] > datetime.date.min:  # 1900
                episode_result['airdate'] = srdatetime.SRDateTime(srdatetime.SRDateTime(
                    sickrage.app.tz_updater.parse_date_time(episode_result['airdate'], show_obj.airs, show_obj.network),
                    convert=True).dt).srfdate(d_preset=dateFormat)
            else:
                episode_result['airdate'] = 'Never'

            status, quality = Quality.split_composite_status(int(episode_result['status']))
            episode_result['status'] = status.display_name
            episode_result['quality'] = quality.display_name
            episode_result['file_size_human'] = pretty_file_size(episode_result['file_size'])

            return _responds(RESULT_SUCCESS, episode_result)
        except orm.exc.NoResultFound:
            raise InternalApiError("Episode not found")


class CMD_EpisodeSearch(ApiCall):
    _cmd = "episode.search"
    _help = {
        "desc": "Search for an episode. The response might take some time.",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_EpisodeSearch, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)

    def run(self):
        """ Search for an episode """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        try:
            epObj = show_object.get_episode(int(self.s), int(self.e))
        except EpisodeNotFoundException:
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchTask(show_object.series_id, show_object.series_provider_id, epObj.season, epObj.episode)
        sickrage.app.search_queue.put(ep_queue_item)

        # wait until the queue item tells us whether it worked or not
        while not ep_queue_item.success:
            time.sleep(1)

        # return the correct json value
        if ep_queue_item.success:
            status, quality = Quality.split_composite_status(epObj.status)
            return _responds(RESULT_SUCCESS, {"quality": quality.display_name}, "Snatched (" + quality.display_name + ")")

        return _responds(RESULT_FAILURE, msg='Unable to find episode')


class CMD_EpisodeSetStatus(ApiCall):
    _cmd = "episode.setstatus"
    _help = {
        "desc": "Set the status of an episode or a season (when no episode is provided)",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
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
        super(CMD_EpisodeSetStatus, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.status, args = self.check_params("status", None, True, "string", ["WANTED", "SKIPPED", "IGNORED", "FAILED"], *args, **kwargs)
        self.e, args = self.check_params("episode", None, False, "int", [], *args, **kwargs)
        self.force, args = self.check_params("force", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Set the status of an episode or a season (when no episode is provided) """
        show_obj = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # convert string status to EpisodeStatus
        self.status = EpisodeStatus[self.status]

        if self.e:
            try:
                ep_list = [show_obj.get_episode(self.s, self.e)]
            except EpisodeNotFoundException as e:
                return _responds(RESULT_FAILURE, msg="Episode not found")
        else:
            # get all episode numbers in specified season
            ep_list = [x for x in show_obj.episodes if x.season == self.s]

        def _epResult(result_code, ep, msg=""):
            return {'season': ep.season, 'episode': ep.episode, 'status': ep.status.display_name,
                    'result': result_type_map[result_code], 'message': msg}

        ep_results = []
        failure = False
        start_backlog = False
        wanted = []

        for epObj in ep_list:
            if self.status == EpisodeStatus.WANTED:
                # figure out what episodes are wanted so we can backlog them
                wanted += [(epObj.season, epObj.episode)]

            # don't let them mess up UNAIRED episodes
            if epObj.status == EpisodeStatus.UNAIRED:
                if self.e is not None:
                    ep_results.append(_epResult(RESULT_FAILURE, epObj, "Refusing to change status because it is UNAIRED"))
                    failure = True
                continue

            # allow the user to force setting the status for an already downloaded episode
            if epObj.status in flatten(
                    [EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]) and not self.force:
                ep_results.append(_epResult(RESULT_FAILURE, epObj, "Refusing to change status because it is already marked as DOWNLOADED"))
                failure = True
                continue

            epObj.status = self.status
            epObj.save()

            if self.status == EpisodeStatus.WANTED:
                start_backlog = True

            ep_results.append(_epResult(RESULT_SUCCESS, epObj))

        extra_msg = ""
        if start_backlog:
            for season, episode in wanted:
                sickrage.app.search_queue.put(BacklogSearchTask(show_obj.series_id, show_obj.series_provider_id, season, episode))
                sickrage.app.log.info("Starting backlog for " + show_obj.name + " season " + str(season) + " because some episodes were set to WANTED")

            extra_msg = " Backlog started"

        if failure:
            return _responds(RESULT_FAILURE, ep_results, 'Failed to set all or some status. Check data.' + extra_msg)
        else:
            return _responds(RESULT_SUCCESS, msg='All status set successfully.' + extra_msg)


class CMD_SubtitleSearch(ApiCall):
    _cmd = "episode.subtitlesearch"
    _help = {
        "desc": "Search for an episode subtitles. The response might take some time.",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SubtitleSearch, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.s, args = self.check_params("season", None, True, "int", [], *args, **kwargs)
        self.e, args = self.check_params("episode", None, True, "int", [], *args, **kwargs)

    def run(self):
        """ Search for an episode subtitles """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        try:
            epObj = show_object.get_episode(int(self.s), int(self.e))
        except EpisodeNotFoundException as e:
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # try do download subtitles for that episode
        previous_subtitles = epObj.subtitles

        try:
            epObj.download_subtitles()
        except Exception:
            return _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        # return the correct json value
        newSubtitles = frozenset(epObj.subtitles).difference(previous_subtitles)
        if newSubtitles:
            newLangs = [Subtitles().name_from_code(newSub) for newSub in newSubtitles]
            status = 'New subtitles downloaded: %s' % ', '.join([newLang for newLang in newLangs])
            response = _responds(RESULT_SUCCESS, msg='New subtitles found')
        else:
            status = 'No subtitles downloaded'
            response = _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        sickrage.app.alerts.message(_('Subtitles Search'), status)

        return response


class CMD_Exceptions(ApiCall):
    _cmd = "exceptions"
    _help = {
        "desc": "Get the scene exceptions for all or a given show",
        "optionalParameters": {
            "series_id": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Exceptions, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, False, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Get the scene exceptions for all or a given show """
        if self.series_id is None:
            scene_exceptions = {}
            for show in get_show_list():
                series_id = show.series_id
                if series_id not in scene_exceptions:
                    scene_exceptions[series_id] = []
                scene_exceptions[series_id].append(show.name)
        else:
            show = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
            if not show:
                return _responds(RESULT_FAILURE, msg="Show not found")

            scene_exceptions = show.scene_exceptions

        return _responds(RESULT_SUCCESS, scene_exceptions)


class CMD_History(ApiCall):
    _cmd = "history"
    _help = {
        "desc": "Get the downloaded and/or snatched history",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
            "type": {"desc": "Only get some entries. No value will returns every type"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_History, self).__init__(application, request, *args, **kwargs)
        self.limit, args = self.check_params("limit", 100, False, "int", [], *args, **kwargs)
        self.type, args = self.check_params("type", None, False, "string", ["downloaded", "snatched"], *args, **kwargs)
        self.type = self.type.lower() if isinstance(self.type, str) else ''

    def run(self):
        """ Get the downloaded and/or snatched history """
        data = History().get(self.limit, self.type)
        results = []

        for row in data:
            status, quality = Quality.split_composite_status(int(row["action"]))

            if self.type and not status.lower() == self.type:
                continue

            row["status"] = status.display_name
            row["quality"] = quality.display_name
            row["date"] = row["date"].strftime(dateTimeFormat)

            del row["action"]

            row["series_id"] = row.pop("series_id")
            row["resource_path"] = os.path.dirname(row["resource"])
            row["resource"] = os.path.basename(row["resource"])

            # Add tvdbid for backward compatibility
            row['tvdbid'] = row['series_id']
            results.append(row)

        return _responds(RESULT_SUCCESS, results)


class CMD_HistoryClear(ApiCall):
    _cmd = "history.clear"
    _help = {"desc": "Clear the entire history"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_HistoryClear, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Clear the entire history """
        History().clear()

        return _responds(RESULT_SUCCESS, msg="History cleared")


class CMD_HistoryTrim(ApiCall):
    _cmd = "history.trim"
    _help = {"desc": "Trim history entries older than 30 days"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_HistoryTrim, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Trim history entries older than 30 days """
        History().trim()

        return _responds(RESULT_SUCCESS, msg='Removed history entries older than 30 days')


class CMD_Failed(ApiCall):
    _cmd = "failed"
    _help = {
        "desc": "Get the failed downloads",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Failed, self).__init__(application, request, *args, **kwargs)
        self.limit, args = self.check_params("limit", 100, False, "int", [], *args, **kwargs)

    def run(self):
        """ Get the failed downloads """

        session = sickrage.app.main_db.session()

        ulimit = min(int(self.limit), 100)
        if ulimit == 0:
            dbData = session.query(MainDB.FailedSnatch).all()
        else:
            dbData = session.query(MainDB.FailedSnatch).limit(ulimit)

        return _responds(RESULT_SUCCESS, dbData)


class CMD_Backlog(ApiCall):
    _cmd = "backlog"
    _help = {"desc": "Get the backlogged episodes"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Backlog, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the backlogged episodes """

        shows = []

        for s in get_show_list():
            showEps = []

            if s.paused:
                continue

            for e in sorted(s.episodes, key=lambda x: (x.season, x.episode), reverse=True):
                cur_ep_cat = e.overview or -1
                if cur_ep_cat and cur_ep_cat in (Overview.WANTED, Overview.LOW_QUALITY):
                    showEps += [e]

            if showEps:
                shows.append({
                    "series_id": s.series_id,
                    "show_name": s.name,
                    "status": s.status,
                    "episodes": showEps
                })

        return _responds(RESULT_SUCCESS, shows)


class CMD_Logs(ApiCall):
    _cmd = "logs"
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
        super(CMD_Logs, self).__init__(application, request, *args, **kwargs)
        self.min_level, args = self.check_params("min_level", "error", False, "string",
                                                 ["error", "warning", "info", "debug"], *args, **kwargs)

    def run(self):
        """ Get the logs """
        maxLines = 50

        levelsFiltered = '|'.join(
            [x for x in sickrage.app.log.logLevels.keys() if
             sickrage.app.log.logLevels[x] >= int(
                 sickrage.app.log.logLevels[str(self.min_level).upper()])])

        logRegex = re.compile(
            r"(?P<entry>^\d+\-\d+\-\d+\s+\d+\:\d+\:\d+\s+(?:{})[\s\S]+?(?:{})[\s\S]+?$)".format(levelsFiltered, ""),
            re.S + re.M)

        data = []
        try:
            if os.path.isfile(sickrage.app.log.logFile):
                data += list(reversed(re.findall("((?:^.+?{}.+?$))".format(""),
                                                 "\n".join(next(read_file_buffered(sickrage.app.log.logFile,
                                                                                   reverse=True)).splitlines()),
                                                 re.S + re.M + re.I)))
                maxLines -= len(data)
                if len(data) == maxLines:
                    raise StopIteration
        except StopIteration:
            pass
        except Exception as e:
            pass

        return _responds(RESULT_SUCCESS, "\n".join(logRegex.findall("\n".join(data))))


class CMD_PostProcess(ApiCall):
    _cmd = "postprocess"
    _help = {
        "desc": "Manually post-process the files in the download folder",
        "optionalParameters": {
            "path": {"desc": "The path to the folder to post-process"},
            "force_replace": {"desc": "Force already post-processed files to be post-processed again"},
            "return_data": {"desc": "Returns the result of the post-process"},
            "process_method": {"desc": "How should valid post-processed files be handled"},
            "is_priority": {"desc": "Replace the file even if it exists in a higher quality"},
            "delete": {"desc": "Delete processed files and folders"},
            "failed": {"desc": "Mark download as failed"},
            "type": {"desc": "The type of post-process being requested"},
            "force_next": {"desc": "Waits for the current processing queue item to finish and returns result of this request"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_PostProcess, self).__init__(application, request, *args, **kwargs)
        self.path, args = self.check_params("path", None, False, "string", [], *args, **kwargs)
        self.force_replace, args = self.check_params("force_replace", False, False, "bool", [], *args, **kwargs)
        self.return_data, args = self.check_params("return_data", False, False, "bool", [], *args, **kwargs)
        self.process_method, args = self.check_params("process_method", ProcessMethod.COPY.name, False, "string", [x.name.lower() for x in ProcessMethod], *args, **kwargs)
        self.is_priority, args = self.check_params("is_priority", False, False, "bool", [], *args, **kwargs)
        self.delete, args = self.check_params("delete", False, False, "bool", [], *args, **kwargs)
        self.failed, args = self.check_params("failed", False, False, "bool", [], *args, **kwargs)
        self.proc_type, args = self.check_params("type", "auto", None, "string", ["auto", "manual"], *args, **kwargs)
        self.force_next, args = self.check_params("force_next", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Manually post-process the files in the download folder """
        if not self.path and not sickrage.app.config.general.tv_download_dir:
            return _responds(RESULT_FAILURE, msg="You need to provide a path or set TV Download Dir")

        if not self.path:
            self.path = sickrage.app.config.general.tv_download_dir

        if not self.proc_type:
            self.proc_type = 'manual'

        data = sickrage.app.postprocessor_queue.put(self.path, process_method=ProcessMethod[self.process_method.upper()], force=self.force_replace,
                                                    is_priority=self.is_priority, delete_on=self.delete, failed=self.failed, proc_type=self.proc_type,
                                                    force_next=self.force_next)

        if not self.return_data:
            data = ""

        return _responds(RESULT_SUCCESS, data=data, msg="Started postprocess for {}".format(self.path))


class CMD_SiCKRAGE(ApiCall):
    _cmd = "sr"
    _help = {"desc": "Get miscellaneous information about SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGE, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get miscellaneous information about SiCKRAGE """
        data = {"app_version": sickrage.version(), "api_version": self.version,
                "api_commands": sorted(self.api_calls.keys())}
        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEAddRootDir(ApiCall):
    _cmd = "sr.addrootdir"
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
        super(CMD_SiCKRAGEAddRootDir, self).__init__(application, request, *args, **kwargs)
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)
        self.default, args = self.check_params("default", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Add a new root (parent) directory to SiCKRAGE """

        self.location = unquote_plus(self.location)
        location_matched = 0
        index = 0

        # dissallow adding/setting an invalid dir
        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="Location is invalid")

        root_dirs = []

        if sickrage.app.config.general.root_dirs == "":
            self.default = 1
        else:
            root_dirs = sickrage.app.config.general.root_dirs.split('|')
            index = int(sickrage.app.config.general.root_dirs.split('|')[0])
            root_dirs.pop(0)
            # clean up the list - replace %xx escapes by their single-character equivalent
            root_dirs = [unquote_plus(x) for x in root_dirs]
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

        root_dirs_new = [unquote_plus(x) for x in root_dirs]
        root_dirs_new.insert(0, index)
        root_dirs_new = '|'.join(x for x in root_dirs_new)

        sickrage.app.config.general.root_dirs = root_dirs_new

        sickrage.app.config.save()

        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directories updated")


class CMD_SiCKRAGECheckVersion(ApiCall):
    _cmd = "sr.checkversion"
    _help = {"desc": "Check if a new version of SiCKRAGE is available"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGECheckVersion, self).__init__(application, request, *args, **kwargs)

    def run(self):
        return _responds(RESULT_SUCCESS, {
            "current_version": {
                "version": sickrage.app.version_updater.version,
            },
            "latest_version": {
                "version": sickrage.app.version_updater.updater.get_newest_version,
            },
            "needs_update": sickrage.app.version_updater.check_for_new_version(True),
        })


class CMD_SiCKRAGECheckScheduler(ApiCall):
    _cmd = "sr.checkscheduler"
    _help = {"desc": "Get information about the scheduler"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGECheckScheduler, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get information about the scheduler """

        backlog_paused = sickrage.app.search_queue.is_backlog_searcher_paused()
        backlog_running = sickrage.app.search_queue.is_backlog_in_progress()

        data = {"backlog_is_paused": int(backlog_paused),
                "backlog_is_running": int(backlog_running)}

        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEDeleteRootDir(ApiCall):
    _cmd = "sr.deleterootdir"
    _help = {"desc": "Delete a root (parent) directory from SiCKRAGE", "requiredParameters": {
        "location": {"desc": "The full path to the root (parent) directory to remove"},
    }}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEDeleteRootDir, self).__init__(application, request, *args, **kwargs)
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)

    def run(self):
        """ Delete a root (parent) directory from SiCKRAGE """
        if sickrage.app.config.general.root_dirs == "":
            return _responds(RESULT_FAILURE, _get_root_dirs(), msg="No root directories detected")

        newIndex = 0
        root_dirs_new = []
        root_dirs = sickrage.app.config.general.root_dirs.split('|')
        index = int(root_dirs[0])
        root_dirs.pop(0)
        # clean up the list - replace %xx escapes by their single-character equivalent
        root_dirs = [unquote_plus(x) for x in root_dirs]
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

        root_dirs_new = [unquote_plus(x) for x in root_dirs_new]
        if len(root_dirs_new) > 0:
            root_dirs_new.insert(0, newIndex)
        root_dirs_new = "|".join(x for x in root_dirs_new)

        sickrage.app.config.general.root_dirs = root_dirs_new
        # what if the root dir was not found?
        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directory deleted")


class CMD_SiCKRAGEGetDefaults(ApiCall):
    _cmd = "sr.getdefaults"
    _help = {"desc": "Get SiCKRAGE's user default configuration value"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEGetDefaults, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get SiCKRAGE's user default configuration value """

        any_qualities, best_qualities = _map_quality(sickrage.app.config.general.quality_default)

        data = {"status": sickrage.app.config.general.status_default.display_name.lower(),
                "flatten_folders": int(sickrage.app.config.general.flatten_folders_default), "initial": any_qualities,
                "archive": best_qualities, "future_show_paused": int(sickrage.app.config.gui.coming_eps_display_paused)}
        return _responds(RESULT_SUCCESS, data)


class CMD_SiCKRAGEGetMessages(ApiCall):
    _cmd = "sr.getmessages"
    _help = {"desc": "Get all messages"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEGetMessages, self).__init__(application, request, *args, **kwargs)

    def run(self):
        messages = []
        for cur_notification in sickrage.app.alerts.get_notifications(self.request.remote_ip):
            messages.append({"title": cur_notification.data['title'],
                             "message": cur_notification.data['body'],
                             "type": cur_notification.data['type']})
        return _responds(RESULT_SUCCESS, messages)


class CMD_SiCKRAGEGetRootDirs(ApiCall):
    _cmd = "sr.getrootdirs"
    _help = {"desc": "Get all root (parent) directories"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEGetRootDirs, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get all root (parent) directories """

        return _responds(RESULT_SUCCESS, _get_root_dirs())


class CMD_SiCKRAGEPauseDaily(ApiCall):
    _cmd = "sr.pausedaily"
    _help = {
        "desc": "Pause or unpause the daily search",
        "optionalParameters": {
            "pause": {"desc": "True to pause the daily search, False to unpause it"}
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEPauseDaily, self).__init__(application, request, *args, **kwargs)
        self.pause, args = self.check_params("pause", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Pause or unpause the daily search """
        if self.pause:
            sickrage.app.search_queue.pause_daily_searcher()
            return _responds(RESULT_SUCCESS, msg="Daily searcher paused")
        else:
            sickrage.app.search_queue.unpause_daily_searcher()
            return _responds(RESULT_SUCCESS, msg="Daily searcher unpaused")


class CMD_SiCKRAGEPauseBacklog(ApiCall):
    _cmd = "sr.pausebacklog"
    _help = {
        "desc": "Pause or unpause the backlog search",
        "optionalParameters": {
            "pause": {"desc": "True to pause the backlog search, False to unpause it"}
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEPauseBacklog, self).__init__(application, request, *args, **kwargs)
        self.pause, args = self.check_params("pause", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Pause or unpause the backlog search """
        if self.pause:
            sickrage.app.search_queue.pause_backlog_searcher()
            return _responds(RESULT_SUCCESS, msg="Backlog searcher paused")
        else:
            sickrage.app.search_queue.unpause_backlog_searcher()
            return _responds(RESULT_SUCCESS, msg="Backlog searcher unpaused")


class CMD_SiCKRAGEPing(ApiCall):
    _cmd = "sr.ping"
    _help = {"desc": "Ping SiCKRAGE to check if it is running"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEPing, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Ping SiCKRAGE to check if it is running """
        if sickrage.app.started:
            return _responds(RESULT_SUCCESS, {"pid": sickrage.app.pid}, "Pong")
        else:
            return _responds(RESULT_SUCCESS, msg="Pong")


class CMD_SiCKRAGERestart(ApiCall):
    _cmd = "sr.restart"
    _help = {"desc": "Restart SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGERestart, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Restart SiCKRAGE """
        sickrage.app.shutdown(restart=True)
        return _responds(RESULT_SUCCESS, msg="SiCKRAGE is restarting...")


class CMD_SiCKRAGESearchSeriesProvider(ApiCall):
    _cmd = "sr.searchindexers"
    _help = {
        "desc": "Search for a show with a given name on all the indexers, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "series_id": {"desc": "Unique ID of a show"},
            "series_provider_id": {"desc": "Unique ID of a series provider"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGESearchSeriesProvider, self).__init__(application, request, *args, **kwargs)
        self.name, args = self.check_params("name", None, False, "string", [], *args, **kwargs)
        self.lang, args = self.check_params("lang", sickrage.app.config.general.series_provider_default_language, False, "string", [], *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, False, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Search for a show with a given name on a specific series provider, in a specific language """

        results = []

        series_provider = sickrage.app.series_providers[self.series_provider_id.upper()]
        series_provider_language = self.lang or sickrage.app.config.general.series_provider_default_language

        if self.name and not self.series_id:  # only name was given
            resp = series_provider.search(self.name, language=series_provider_language)
            if resp:
                for curSeries in resp:
                    if not resp.get('seriesname', None):
                        continue

                    if not resp.get('firstaired', None):
                        continue

                    results.append({
                        'series_id': int(curSeries['id']),
                        "name": curSeries['seriesname'],
                        'first_aired': curSeries['firstaired']
                    })

                return _responds(RESULT_SUCCESS, {"results": results, "langid": series_provider_language})

        elif self.series_id:
            resp = series_provider.search(self.series_id, language=series_provider_language)
            if resp:
                if not resp.get('seriesname', None):
                    sickrage.app.log.debug("Found show with series_id: " + str(self.series_id) + ", however it contained no show name")
                    return _responds(RESULT_FAILURE, msg="Show contains no name, invalid result")

                if not resp.get('firstaired', None):
                    sickrage.app.log.debug("Found show with series_id: " + str(self.series_id) + ", however it contained no first air date")
                    return _responds(RESULT_FAILURE, msg="Show contains no first air date, invalid result")

                # found show
                results = [{
                    'series_id': int(resp['id']),
                    "name": resp['seriesname'],
                    'first_aired': resp['firstaired']
                }]

                return _responds(RESULT_SUCCESS, {"results": results, "langid": series_provider_language})

        return _responds(RESULT_FAILURE, msg="Either a unique id or name is required!")


class CMD_SiCKRAGESearchTVDB(CMD_SiCKRAGESearchSeriesProvider):
    _cmd = "sr.searchtvdb"
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
        self.series_id, args = self.check_params("tvdbid", None, False, "int", [], *args, **kwargs)


class CMD_SiCKRAGESearchTVRAGE(CMD_SiCKRAGESearchSeriesProvider):
    _cmd = "sr.searchtvrage"
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
        super(CMD_SiCKRAGESearchTVRAGE, self).__init__(application, request, *args, **kwargs)

    def run(self):
        return _responds(RESULT_FAILURE, msg="TVRage is disabled, invalid result")


class CMD_SiCKRAGESetDefaults(ApiCall):
    _cmd = "sr.setdefaults"
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
        super(CMD_SiCKRAGESetDefaults, self).__init__(application, request, *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list", any_quality_list, *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list", best_quality_list, *args, **kwargs)
        self.future_show_paused, args = self.check_params("future_show_paused", None, False, "bool", [], *args,
                                                          **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders", None, False, "bool", [], *args, **kwargs)
        self.status, args = self.check_params("status", None, False, "string", ["wanted", "skipped", "ignored"], *args,
                                              **kwargs)

    def run(self):
        """ Set SiCKRAGE's user default configuration value """

        iqualityID = []
        aqualityID = []

        if isinstance(self.initial, collections.Iterable):
            for quality in self.initial:
                iqualityID.append(_get_quality_map()[quality])
        if isinstance(self.archive, collections.Iterable):
            for quality in self.archive:
                aqualityID.append(_get_quality_map()[quality])

        if iqualityID or aqualityID:
            sickrage.app.config.general.quality_default = Quality.combine_qualities(iqualityID, aqualityID)

        if self.status:
            # only allow the status options we want
            if self.status not in (EpisodeStatus.WANTED, EpisodeStatus.SKIPPED, EpisodeStatus.ARCHIVED, EpisodeStatus.IGNORED):
                raise InternalApiError("Status Prohibited")

            sickrage.app.config.general.status_default = self.status

        if self.flatten_folders is not None:
            sickrage.app.config.general.flatten_folders_default = int(self.flatten_folders)

        if self.future_show_paused is not None:
            sickrage.app.config.gui.coming_eps_display_paused = int(self.future_show_paused)

        sickrage.app.config.save()

        return _responds(RESULT_SUCCESS, msg="Saved defaults")


class CMD_SiCKRAGEShutdown(ApiCall):
    _cmd = "sr.shutdown"
    _help = {"desc": "Shutdown SiCKRAGE"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEShutdown, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Shutdown SiCKRAGE """
        if sickrage.app.started:
            sickrage.app.shutdown()
            return _responds(RESULT_SUCCESS, msg="SiCKRAGE is shutting down...")
        return _responds(RESULT_FAILURE, msg='SiCKRAGE can not be shut down')


class CMD_SiCKRAGEUpdate(ApiCall):
    _cmd = "sr.update"
    _help = {"desc": "Update SiCKRAGE to the latest version available"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_SiCKRAGEUpdate, self).__init__(application, request, *args, **kwargs)

    def run(self):
        if sickrage.app.version_updater.check_for_new_version():
            if sickrage.app.version_updater.update():
                return _responds(RESULT_SUCCESS, msg="SiCKRAGE is updating ...")
            return _responds(RESULT_FAILURE, msg="SiCKRAGE could not update ...")
        return _responds(RESULT_FAILURE, msg="SiCKRAGE is already up to date")


class CMD_Show(ApiCall):
    _cmd = "show"
    _help = {
        "desc": "Get detailed information about a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Show, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Get detailed information about a show """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        showDict = {
            "season_list": (CMD_ShowSeasonList(self.application, self.request, **{"series_id": self.series_id}).run())["data"],
            "cache": (CMD_ShowCache(self.application, self.request, **{"series_id": self.series_id}).run())["data"]
        }

        genreList = []
        if show_object.genre:
            genreListTmp = show_object.genre.split("|")
            for genre in genreListTmp:
                if genre:
                    genreList.append(genre)

        showDict["genre"] = genreList
        showDict["quality"] = Qualities(show_object.quality).display_name

        anyQualities, bestQualities = _map_quality(show_object.quality)
        showDict["quality_details"] = {"initial": anyQualities, "archive": bestQualities}

        showDict["location"] = show_object.location
        showDict["language"] = show_object.lang
        showDict["show_name"] = show_object.name
        showDict["paused"] = (0, 1)[show_object.paused]
        showDict["subtitles"] = (0, 1)[show_object.subtitles]
        showDict["search_format"] = show_object.search_format
        showDict["flatten_folders"] = (0, 1)[show_object.flatten_folders]
        showDict["scene"] = (0, 1)[show_object.scene]
        showDict["anime"] = (0, 1)[show_object.anime]
        showDict["airs"] = str(show_object.airs).replace('am', ' AM').replace('pm', ' PM').replace('  ', ' ')
        showDict["dvd_order"] = (0, 1)[show_object.dvd_order]

        if show_object.rls_require_words:
            showDict["rls_require_words"] = show_object.rls_require_words.split(", ")
        else:
            showDict["rls_require_words"] = []

        if show_object.rls_ignore_words:
            showDict["rls_ignore_words"] = show_object.rls_ignore_words.split(", ")
        else:
            showDict["rls_ignore_words"] = []

        showDict["skip_downloaded"] = (0, 1)[show_object.skip_downloaded]

        showDict["series_id"] = show_object.series_id
        showDict["series_provider_id"] = show_object.series_provider.name
        showDict["tvdbid"] = map_series_providers(show_object.series_provider_id, show_object.series_id, show_object.name)[SeriesProviderID.THETVDB.name]
        showDict["imdbid"] = show_object.imdb_id

        showDict["network"] = show_object.network
        if not showDict["network"]:
            showDict["network"] = ""
        showDict["status"] = show_object.status

        if try_int(show_object.airs_next, 1) > 693595:
            dtEpisodeAirs = srdatetime.SRDateTime(
                sickrage.app.tz_updater.parse_date_time(show_object.airs_next, showDict['airs'], showDict['network']), convert=True).dt
            showDict['airs'] = srdatetime.SRDateTime(dtEpisodeAirs).srftime(t_preset=timeFormat).lstrip('0').replace(
                ' 0', ' ')
            showDict['next_ep_airdate'] = srdatetime.SRDateTime(dtEpisodeAirs).srfdate(d_preset=dateFormat)
        else:
            showDict['next_ep_airdate'] = ''

        return _responds(RESULT_SUCCESS, showDict)


class CMD_ShowAddExisting(ApiCall):
    _cmd = "show.addexisting"
    _help = {
        "desc": "Add an existing show in SiCKRAGE",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
            "series_provider_id": {"desc": "Unique ID of a series provider"},
            "location": {"desc": "Full path to the existing shows's folder"},
        },
        "optionalParameters": {
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowAddExisting, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.location, args = self.check_params("location", None, True, "string", [], *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list", any_quality_list, *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list", best_quality_list, *args, **kwargs)
        self.skip_downloaded, args = self.check_params("skip_downloaded", None, False, "int", [], *args, **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders",
                                                       bool(sickrage.app.config.general.flatten_folders_default), False,
                                                       "bool", [], *args, **kwargs)
        self.subtitles, args = self.check_params("subtitles", int(sickrage.app.config.subtitles.enable), False, "int",
                                                 [], *args, **kwargs)

    def run(self):
        """ Add an existing show in SiCKRAGE """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if show_object:
            return _responds(RESULT_FAILURE, msg="An existing series_id already exists in the database")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg='Not a valid location')

        series_provider_id = SeriesProviderID[self.series_provider_id]

        series_provider_result = CMD_SiCKRAGESearchSeriesProvider(self.application, self.request, **{
            'series_id': self.series_id,
            'series_provider_id': series_provider_id
        }).run()

        series_name = None

        if series_provider_result['result'] == result_type_map[RESULT_SUCCESS]:
            if not series_provider_result['data']['results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check series_id and try again")
            if len(series_provider_result['data']['results']) == 1 and 'name' in series_provider_result['data']['results'][0]:
                series_name = series_provider_result['data']['results'][0]['name']

        first_aired = series_provider_result['data']['results'][0]['first_aired']

        if not series_name or not first_aired:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # use default quality as a failsafe
        newQuality = int(sickrage.app.config.general.quality_default)
        iqualityID = []
        aqualityID = []

        if isinstance(self.initial, collections.Iterable):
            for quality in self.initial:
                iqualityID.append(_get_quality_map()[quality])
        if isinstance(self.archive, collections.Iterable):
            for quality in self.archive:
                aqualityID.append(_get_quality_map()[quality])

        if iqualityID or aqualityID:
            newQuality = Quality.combine_qualities(iqualityID, aqualityID)

        sickrage.app.show_queue.add_show(
            series_provider_id=series_provider_id, series_id=int(self.series_id), show_dir=self.location,
            default_status=sickrage.app.config.general.status_default, quality=newQuality, flatten_folders=int(self.flatten_folders),
            subtitles=self.subtitles, default_status_after=sickrage.app.config.general.status_default_after, skip_downloaded=self.skip_downloaded
        )

        return _responds(RESULT_SUCCESS, {"name": series_name}, series_name + " has been queued to be added")


class CMD_ShowAddNew(ApiCall):
    _cmd = "show.addnew"
    _help = {
        "desc": "Add a new show to SiCKRAGE",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
            "series_provider_id": {"desc": "Unique ID of a series provider"},
        },
        "optionalParameters": {
            "initial": {"desc": "The initial quality of the show"},
            "location": {"desc": "The path to the folder where the show should be created"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "status": {"desc": "The status of missing episodes"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
            "anime": {"desc": "True to mark the show as an anime, False otherwise"},
            "scene": {"desc": "True to use scene numbering, False otherwise"},
            "search_format": {"desc": "The search format used when searching for episodes"},
            "future_status": {"desc": "The status of future episodes"},
            "skip_downloaded": {
                "desc": "True if episodes should be archived when first match is downloaded, False otherwise"
            },
            "add_show_year": {
                "desc": "True if show year should be appended to show folder name, False otherwise"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowAddNew, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.location, args = self.check_params("location", None, False, "string", [], *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list", any_quality_list, *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list", best_quality_list, *args, **kwargs)
        self.flatten_folders, args = self.check_params("flatten_folders", bool(sickrage.app.config.general.flatten_folders_default), False, "bool", [], *args,
                                                       **kwargs)
        self.status, args = self.check_params("status", None, False, "string", ["wanted", "skipped", "ignored"], *args, **kwargs)
        self.lang, args = self.check_params("lang", sickrage.app.config.general.series_provider_default_language, False, "string", [], *args, **kwargs)
        self.subtitles, args = self.check_params("subtitles", bool(sickrage.app.config.subtitles.enable), False, "bool", [], *args, **kwargs)
        self.scene, args = self.check_params("scene", bool(sickrage.app.config.general.scene_default), False, "bool", [], *args, **kwargs)
        self.anime, args = self.check_params("anime", bool(sickrage.app.config.general.anime_default), False, "bool", [], *args, **kwargs)
        self.search_format, args = self.check_params("search_format", sickrage.app.config.general.search_format_default, False, "string", [], *args, **kwargs)
        self.future_status, args = self.check_params("future_status", None, False, "string", ["wanted", "skipped", "ignored"], *args, **kwargs)
        self.skip_downloaded, args = self.check_params("skip_downloaded", bool(sickrage.app.config.general.skip_downloaded_default), False, "bool", [], *args,
                                                       **kwargs)
        self.add_show_year, args = self.check_params("add_show_year", bool(sickrage.app.config.general.add_show_year_default), False, "bool", [], *args,
                                                     **kwargs)

    def run(self):
        """ Add a new show to SiCKRAGE """
        show_obj = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if show_obj:
            return _responds(RESULT_FAILURE, msg="An existing series_id already exists in database")

        if not self.location:
            if sickrage.app.config.general.root_dirs != "":
                root_dirs = sickrage.app.config.general.root_dirs.split('|')
                root_dirs.pop(0)
                default_index = int(sickrage.app.config.general.root_dirs.split('|')[0])
                self.location = root_dirs[default_index]
            else:
                return _responds(RESULT_FAILURE, msg="Root directory is not set, please provide a location")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="'" + self.location + "' is not a valid location")

        # use default quality as a failsafe
        new_quality = int(sickrage.app.config.general.quality_default)
        iquality_id = []
        aquality_id = []

        if isinstance(self.initial, collections.Iterable):
            for quality in self.initial:
                iquality_id.append(_get_quality_map()[quality])
        if isinstance(self.archive, collections.Iterable):
            for quality in self.archive:
                aquality_id.append(_get_quality_map()[quality])

        if iquality_id or aquality_id:
            new_quality = Quality.combine_qualities(iquality_id, aquality_id)

        # use default status as a failsafe
        new_status = sickrage.app.config.general.status_default
        if self.status:
            # only allow the status options we want
            if self.status not in (EpisodeStatus.WANTED, EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")

            new_status = self.status

        # use default status as a failsafe
        default_ep_status_after = sickrage.app.config.general.status_default_after
        if self.future_status:
            # only allow the status options we want
            if self.future_status not in (EpisodeStatus.WANTED, EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            default_ep_status_after = self.future_status

        series_provider_id = SeriesProviderID[self.series_provider_id]

        series_provider_result = CMD_SiCKRAGESearchSeriesProvider(self.application, self.request, **{
            'series_id': self.series_id,
            'series_provider_id': series_provider_id
        }).run()

        series_name = None

        if series_provider_result['result'] == result_type_map[RESULT_SUCCESS]:
            if not series_provider_result['data']['results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check series_id and try again")
            if len(series_provider_result['data']['results']) == 1 and 'name' in series_provider_result['data']['results'][0]:
                series_name = series_provider_result['data']['results'][0]['name']

        first_aired = series_provider_result['data']['results'][0]['first_aired']

        if not series_name or not first_aired:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # moved the logic check to the end in an attempt to eliminate empty directory being created from previous errors
        show_path = os.path.join(self.location, sanitize_file_name(series_name))
        if self.add_show_year and not re.match(r'.*\(\d+\)$', show_path):
            show_path = "{} ({})".format(show_path, re.search(r'\d{4}', first_aired).group(0))

        # don't create show dir if config says not to
        if sickrage.app.config.general.add_shows_wo_dir:
            sickrage.app.log.info("Skipping initial creation of " + show_path + " due to config.ini setting")
        else:
            dir_exists = make_dir(show_path)
            if not dir_exists:
                sickrage.app.log.warning("Unable to create the folder " + show_path + ", can't add the show")
                return _responds(RESULT_FAILURE, {"path": show_path}, "Unable to create the folder " + show_path + ", can't add the show")
            else:
                chmod_as_parent(show_path)

        sickrage.app.show_queue.add_show(
            series_provider_id=series_provider_id, series_id=int(self.series_id), show_dir=show_path, default_status=new_status, quality=new_quality,
            flatten_folders=int(self.flatten_folders), lang=self.lang, subtitles=self.subtitles, anime=self.anime, scene=self.scene,
            search_format=self.search_format, default_status_after=default_ep_status_after, skip_downloaded=self.skip_downloaded
        )

        return _responds(RESULT_SUCCESS, {"name": series_name}, series_name + " has been queued to be added")


class CMD_ShowCache(ApiCall):
    _cmd = "show.cache"
    _help = {
        "desc": "Check SiCKRAGE's cache to see if the images (poster, banner, fanart) for a show are valid",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowCache, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Check SiCKRAGE's cache to see if the images (poster, banner, fanart) for a show are valid """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # TODO: catch if cache dir is missing/invalid.. so it doesn't break show/show.cache
        # return {"poster": 0, "banner": 0}

        cache_obj = image_cache.ImageCache()

        has_poster = 0
        has_banner = 0

        if os.path.isfile(cache_obj.poster_path(show_object.series_id)):
            has_poster = 1
        if os.path.isfile(cache_obj.banner_path(show_object.series_id)):
            has_banner = 1

        return _responds(RESULT_SUCCESS, {"poster": has_poster, "banner": has_banner})


class CMD_ShowDelete(ApiCall):
    _cmd = "delete"
    _help = {
        "desc": "Delete a show in SiCKRAGE",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "removefiles": {
                "desc": "True to delete the files associated with the show, False otherwise. This can not be undone!"
            },
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowDelete, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.removefiles, args = self.check_params("removefiles", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Delete a show in SiCKRAGE """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            sickrage.app.show_queue.remove_show(show_object.series_id, show_object.series_provider_id, bool(self.removefiles))
        except CantRemoveShowException as exception:
            return _responds(RESULT_FAILURE, msg=str(exception))

        return _responds(RESULT_SUCCESS, msg='%s has been queued to be deleted' % show_object.name)


class CMD_ShowGetQuality(ApiCall):
    _cmd = "show.getquality"
    _help = {
        "desc": "Get the quality setting of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowGetQuality, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Get the quality setting of a show """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        anyQualities, bestQualities = _map_quality(show_object.quality)

        return _responds(RESULT_SUCCESS, {"initial": anyQualities, "archive": bestQualities})


class CMD_ShowGetPoster(ApiCall):
    _cmd = "show.getposter"
    _help = {
        "desc": "Get the poster of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowGetPoster, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args,
                                                          **kwargs)

    def run(self):
        """ Get the poster a show """
        return {
            'outputType': 'image',
            'image': Poster(self.series_id, SeriesProviderID[self.series_provider_id.upper()]),
        }


class CMD_ShowGetBanner(ApiCall):
    _cmd = "show.getbanner"
    _help = {
        "desc": "Get the banner of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowGetBanner, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Get the banner of a show """
        return {
            'outputType': 'image',
            'image': Banner(self.series_id, SeriesProviderID[self.series_provider_id.upper()]),
        }


class CMD_ShowGetNetworkLogo(ApiCall):
    _cmd = "show.getnetworklogo"
    _help = {
        "desc": "Get the network logo of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowGetNetworkLogo, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """
        :return: Get the network logo of a show
        """
        return {
            'outputType': 'image',
            'image': Network(self.series_id, SeriesProviderID[self.series_provider_id.upper()]),
        }


class CMD_ShowGetFanArt(ApiCall):
    _cmd = "show.getfanart"
    _help = {
        "desc": "Get the fan art of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowGetFanArt, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args,
                                                          **kwargs)

    def run(self):
        """ Get the fan art of a show """
        return {
            'outputType': 'image',
            'image': FanArt(self.series_id, SeriesProviderID[self.series_provider_id.upper()]),
        }


class CMD_ShowPause(ApiCall):
    _cmd = "show.pause"
    _help = {
        "desc": "Pause or unpause a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "pause": {"desc": "True to pause the show, False otherwise"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowPause, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.pause, args = self.check_params("pause", False, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Pause or unpause a show """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        if self.pause is None:
            show_object.paused = not show_object.paused
        else:
            show_object.paused = self.pause

        show_object.save()

        return _responds(RESULT_SUCCESS, msg='%s has been %s' % (show_object.name, ('resumed', 'paused')[show_object.paused]))


class CMD_ShowRefresh(ApiCall):
    _cmd = "show.refresh"
    _help = {
        "desc": "Refresh a show in SiCKRAGE",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowRefresh, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Refresh a show in SiCKRAGE """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            sickrage.app.show_queue.refresh_show(show_object.series_id, show_object.series_provider_id)
        except CantRefreshShowException as e:
            return _responds(RESULT_FAILURE, msg=str(e))

        return _responds(RESULT_SUCCESS, msg='%s has queued to be refreshed' % show_object.name)


class CMD_ShowSeasonList(ApiCall):
    _cmd = "show.seasonlist"
    _help = {
        "desc": "Get the list of seasons of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "sort": {"desc": "Return the seasons in ascending or descending order"}
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowSeasonList, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.sort, args = self.check_params("sort", "desc", False, "string", ["asc", "desc"], *args, **kwargs)

    def run(self):
        """ Get the list of seasons of a show """
        show_obj = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        season_list = set()
        for episode_object in show_obj.episodes:
            season_list.add(episode_object.season)

        return _responds(RESULT_SUCCESS, sorted(list(season_list), reverse=self.sort == 'desc'))


class CMD_ShowSeasons(ApiCall):
    _cmd = "show.seasons"
    _help = {
        "desc": "Get the list of episodes for one or all seasons of a show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "season": {"desc": "The season number"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowSeasons, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        self.season, args = self.check_params("season", None, False, "int", [], *args, **kwargs)

    def run(self):
        """ Get the list of episodes for one or all seasons of a show """

        session = sickrage.app.main_db.session()

        seasons = {}

        show_obj = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        if self.season is None:
            db_data = session.query(MainDB.TVEpisode).filter_by(series_id=self.series_id, series_provider_id=show_obj.series_provider_id)
        else:
            db_data = session.query(MainDB.TVEpisode).filter_by(series_id=self.series_id, series_provider_id=show_obj.series_provider_id, season=self.season)

        for row in db_data:
            episode_dict = row.as_dict()

            status, quality = Quality.split_composite_status(int(episode_dict['status']))
            episode_dict['status'] = status.display_name
            episode_dict['quality'] = quality.display_name

            if episode_dict['airdate'] > datetime.date.min:
                dtEpisodeAirs = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(episode_dict['airdate'], show_obj.airs, show_obj.network),
                                                      convert=True).dt
                episode_dict['airdate'] = srdatetime.SRDateTime(dtEpisodeAirs).srfdate(d_preset=dateFormat)
            else:
                episode_dict['airdate'] = 'Never'

            curSeason = int(episode_dict['season'])
            curEpisode = int(episode_dict['episode'])

            if curSeason not in seasons:
                seasons[curSeason] = {}

            seasons[curSeason][curEpisode] = episode_dict

        return _responds(RESULT_SUCCESS, seasons)


class CMD_ShowSetQuality(ApiCall):
    _cmd = "show.setquality"
    _help = {
        "desc": "Set the quality setting of a show. If no quality is provided, the default user setting is used.",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowSetQuality, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)
        # self.archive, args = self.check_params("archive", None, False, "list", _getQualityMap().values()[1:], *args, **kwargs)
        self.initial, args = self.check_params("initial", None, False, "list", any_quality_list, *args, **kwargs)
        self.archive, args = self.check_params("archive", None, False, "list", best_quality_list, *args, **kwargs)

    def run(self):
        """ Set the quality setting of a show. If no quality is provided, the default user setting is used. """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # use default quality as a failsafe
        newQuality = int(sickrage.app.config.general.quality_default)
        iqualityID = []
        aqualityID = []

        if isinstance(self.initial, collections.Iterable):
            for quality in self.initial:
                iqualityID.append(_get_quality_map()[quality])
        if isinstance(self.archive, collections.Iterable):
            for quality in self.archive:
                aqualityID.append(_get_quality_map()[quality])

        if iqualityID or aqualityID:
            newQuality = Quality.combine_qualities(iqualityID, aqualityID)

        show_object.quality = newQuality
        show_object.save()

        return _responds(RESULT_SUCCESS, msg=show_object.name + " quality has been changed to " + Qualities(show_object.quality).display_name)


class CMD_ShowStats(ApiCall):
    _cmd = "show.stats"
    _help = {
        "desc": "Get episode statistics for a given show",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowStats, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Get episode statistics for a given show """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.upper()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # show stats
        episode_status_counts_total = {"total": 0}
        for status in EpisodeStatus:
            if status in [EpisodeStatus.UNKNOWN, EpisodeStatus.DOWNLOADED, EpisodeStatus.SNATCHED, EpisodeStatus.SNATCHED_PROPER, EpisodeStatus.ARCHIVED]:
                continue

            episode_status_counts_total[status] = 0

        # add all the downloaded qualities
        episode_qualities_counts_download = {"total": 0}
        for status in flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
            __, quality = Quality.split_composite_status(status)
            if quality == Qualities.NONE:
                continue

            episode_qualities_counts_download[status] = 0

        # add all snatched qualities
        episode_qualities_counts_snatch = {"total": 0}
        for statusCode in flatten([EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER)]):
            __, quality = Quality.split_composite_status(statusCode)
            if quality == Qualities.NONE:
                continue

            episode_qualities_counts_snatch[statusCode] = 0

        # the main loop that goes through all episodes
        for episode_object in show_object.episodes:
            if episode_object.season == 0:
                continue

            status, quality = Quality.split_composite_status(episode_object.status)
            if quality == Qualities.NONE:
                continue

            episode_status_counts_total["total"] += 1

            if status in flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
                episode_qualities_counts_download["total"] += 1
                episode_qualities_counts_download[episode_object.status] += 1
            elif status in flatten([EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER)]):
                episode_qualities_counts_snatch["total"] += 1
                episode_qualities_counts_snatch[episode_object.status] += 1
            elif status == EpisodeStatus.UNKNOWN:  # we dont count UNKNOWN
                pass
            else:
                episode_status_counts_total[status] += 1

        # the outgoing container
        episodes_stats = {
            "total": 0,
            "downloaded": {},
            "snatched": {}
        }

        for statusCode in episode_qualities_counts_download:
            if statusCode == "total":
                episodes_stats["downloaded"]["total"] = episode_qualities_counts_download[statusCode]
                continue

            status, quality = Quality.split_composite_status(statusCode)
            status_string = quality.display_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            episodes_stats["downloaded"][status_string] = episode_qualities_counts_download[statusCode]

        for statusCode in episode_qualities_counts_snatch:
            if statusCode == "total":
                episodes_stats["snatched"]["total"] = episode_qualities_counts_snatch[statusCode]
                continue

            status, quality = Quality.split_composite_status(statusCode)
            status_string = quality.display_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            if quality.display_name in episodes_stats["snatched"]:
                episodes_stats["snatched"][status_string] += episode_qualities_counts_snatch[statusCode]
            else:
                episodes_stats["snatched"][status_string] = episode_qualities_counts_snatch[statusCode]

        for statusCode in episode_status_counts_total:
            if statusCode == "total":
                episodes_stats["total"] = episode_status_counts_total[statusCode]
                continue

            status_string = statusCode.display_name
            status_string = status_string.lower().replace(" ", "_").replace("(", "").replace(")", "")
            episodes_stats[status_string] = episode_status_counts_total[statusCode]

        return _responds(RESULT_SUCCESS, episodes_stats)


class CMD_ShowUpdate(ApiCall):
    _cmd = "show.update"
    _help = {
        "desc": "Update a show in SiCKRAGE",
        "requiredParameters": {
            "series_id": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowUpdate, self).__init__(application, request, *args, **kwargs)
        self.series_id, args = self.check_params("series_id", None, True, "int", [], *args, **kwargs)
        self.series_provider_id, args = self.check_params("series_provider_id", None, True, "string", [x.name.lower() for x in SeriesProviderID], *args, **kwargs)

    def run(self):
        """ Update a show in SiCKRAGE """
        show_object = find_show(int(self.series_id), SeriesProviderID[self.series_provider_id.lower()])
        if not show_object:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            sickrage.app.show_queue.update_show(show_object.series_id, show_object.series_provider_id, force=True)
            return _responds(RESULT_SUCCESS, msg=str(show_object.name) + " has queued to be updated")
        except CantUpdateShowException as e:
            sickrage.app.log.debug("API::Unable to update show: {}".format(e))
            return _responds(RESULT_FAILURE, msg="Unable to update " + str(show_object.name))


class CMD_Shows(ApiCall):
    _cmd = "shows"
    _help = {
        "desc": "Get all shows in SiCKRAGE",
        "optionalParameters": {
            "sort": {"desc": "The sorting strategy to apply to the list of shows"},
            "paused": {"desc": "True to include paused shows, False otherwise"},
        },
    }

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_Shows, self).__init__(application, request, *args, **kwargs)
        self.sort, args = self.check_params("sort", "id", False, "string", ["id", "name"], *args, **kwargs)
        self.paused, args = self.check_params("paused", None, False, "bool", [], *args, **kwargs)

    def run(self):
        """ Get all shows in SiCKRAGE """
        shows = {}
        for curShow in get_show_list():
            if self.paused is not None and bool(self.paused) != bool(curShow.paused):
                continue

            showDict = {
                "paused": (0, 1)[curShow.paused],
                "quality": Qualities(curShow.quality).display_name,
                "language": curShow.lang,
                "search_format": curShow.search_format,
                "anime": (0, 1)[curShow.anime],
                "series_id": curShow.series_id,
                "series_provider_id": curShow.series_provider.name,
                "network": curShow.network,
                "show_name": curShow.name,
                "status": curShow.status,
                "subtitles": (0, 1)[curShow.subtitles],
            }

            if try_int(curShow.airs_next, 1) > 693595:  # 1900
                dtEpisodeAirs = srdatetime.SRDateTime(
                    sickrage.app.tz_updater.parse_date_time(curShow.airs_next, curShow.airs, showDict['network']), convert=True).dt
                showDict['next_ep_airdate'] = srdatetime.SRDateTime(dtEpisodeAirs).srfdate(d_preset=dateFormat)
            else:
                showDict['next_ep_airdate'] = ''

            showDict["cache"] = (CMD_ShowCache(self.application, self.request, **{"series_id": curShow.series_id}).run())["data"]

            if not showDict["network"]:
                showDict["network"] = ""
            if self.sort == "name":
                shows[curShow.name] = showDict
            else:
                shows[curShow.series_id] = showDict

        return _responds(RESULT_SUCCESS, shows)


class CMD_ShowsStats(ApiCall):
    _cmd = "shows.stats"
    _help = {"desc": "Get the global shows and episodes statistics"}

    def __init__(self, application, request, *args, **kwargs):
        super(CMD_ShowsStats, self).__init__(application, request, *args, **kwargs)

    def run(self):
        """ Get the global shows and episodes statistics """
        overall_stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in get_show_list() if show.paused == 0 and show.status.lower() == 'continuing']),
                'total': len(get_show_list()),
            },
            'total_size': 0
        }

        for show in get_show_list():
            if sickrage.app.show_queue.is_being_added(show.series_id) or sickrage.app.show_queue.is_being_removed(show.series_id):
                continue

            overall_stats['episodes']['snatched'] += show.episodes_snatched or 0
            overall_stats['episodes']['downloaded'] += show.episodes_downloaded or 0
            overall_stats['episodes']['total'] += show.episodes_total or 0
            overall_stats['total_size'] += show.total_size or 0

        return _responds(RESULT_SUCCESS, {
            'ep_downloaded': overall_stats['episodes']['downloaded'],
            'ep_snatched': overall_stats['episodes']['snatched'],
            'ep_total': overall_stats['episodes']['total'],
            'shows_active': overall_stats['shows']['active'],
            'shows_total': overall_stats['shows']['total'],
        })
