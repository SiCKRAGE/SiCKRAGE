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
import base64
import datetime
import gettext
import io
import os
import re
import sys
import uuid
from itertools import cycle

import rarfile
from configobj import ConfigObj

import sickrage
from sickrage.core.helpers import encryption, move_file, extract_zipfile, make_dir
from sickrage.core.websession import WebSession


def encrypt_config(config_obj, private_key, public_key):
    config_tmp_file = config_obj.filename + '.tmp'

    # encrypt config
    with io.BytesIO() as buffer, open(config_tmp_file, 'wb') as fd:
        config_obj.write(buffer)
        buffer.seek(0)
        fd.write(encryption.encrypt_string(buffer.read(), public_key))

    try:
        decrypt_config(config_tmp_file, private_key)
        sickrage.app.log.debug("Saved encrypted config to disk")
        move_file(config_tmp_file, config_obj.filename)
        return True
    except Exception as e:
        sickrage.app.log.debug("Failed to save encrypted config to disk")
        os.remove(config_tmp_file)
        return False


def decrypt_config(config_file, private_key):
    try:
        with io.BytesIO() as buffer, open(config_file, 'rb') as fd:
            buffer.write(encryption.decrypt_string(fd.read(), private_key))
            buffer.seek(0)
            config_obj = ConfigObj(buffer, encoding='utf8')
    except (AttributeError, ValueError):
        # old encryption from python 2
        config_obj = ConfigObj(config_file, encoding='utf8')
        config_obj.walk(legacy_decrypt,
                        encryption_version=int(config_obj.get('General', {}).get('encryption_version', 0)),
                        encryption_secret=config_obj.get('General', {}).get('encryption_secret', ''),
                        raise_errors=False)

    return config_obj


def legacy_encrypt(section, key, encryption_version, encryption_secret, _decrypt=False):
    """
    :rtype: basestring
    """
    # DO NOT ENCRYPT THESE
    if key in ['config_version', 'encryption_version', 'encryption_secret']:
        return

    try:
        if encryption_version == 1:
            unique_key1 = hex(uuid.getnode() ** 2)

            if _decrypt:
                section[key] = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(base64.decodestring(section[key]), cycle(unique_key1)))
            else:
                section[key] = base64.encodestring(''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(section[key], cycle(unique_key1)))).strip()
        elif encryption_version == 2:
            if _decrypt:
                section[key] = ''.join(chr(x ^ y) for x, y in zip(base64.b64decode(section[key]), cycle(map(ord, encryption_secret))))
            else:
                section[key] = base64.b64encode(''.join(chr(x ^ y) for (x, y) in zip(map(ord, section[key]), cycle(
                    map(ord, encryption_secret)))).encode()).decode().strip()
    except Exception:
        pass


def legacy_decrypt(section, key, encryption_version, encryption_secret):
    legacy_encrypt(section, key, encryption_version=encryption_version, encryption_secret=encryption_secret, _decrypt=True)


def change_gui_lang(language):
    if language:
        # Selected language
        gt = gettext.translation('messages', sickrage.LOCALE_DIR, languages=[language], codeset='UTF-8')
        gt.install(names=["ngettext"])
    else:
        # System default language
        gettext.install('messages', sickrage.LOCALE_DIR, codeset='UTF-8', names=["ngettext"])


def change_unrar_tool(unrar_tool):
    # Check for failed unrar attempt, and remove it
    # Must be done before unrar is ever called or the self-extractor opens and locks startup
    bad_unrar = os.path.join(sickrage.app.data_dir, 'unrar.exe')
    if os.path.exists(bad_unrar) and os.path.getsize(bad_unrar) == 447440:
        try:
            os.remove(bad_unrar)
        except OSError as e:
            sickrage.app.log.warning("Unable to delete bad unrar.exe file {}: {}. You should delete it manually".format(bad_unrar, e.strerror))

    for check in [unrar_tool, 'unrar']:
        try:
            rarfile.custom_check([check], True)
            sickrage.app.unrar_tool = rarfile.UNRAR_TOOL = check
            return True
        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
            continue

    if sys.platform == 'win32':
        # Look for WinRAR installations
        winrar_path = 'WinRAR\\UnRAR.exe'

        # Make a set of unique paths to check from existing environment variables
        check_locations = {
            os.path.join(location, winrar_path) for location in (
                os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles(x86)"),
                os.environ.get("ProgramFiles"), re.sub(r'\s?\(x86\)', '', os.environ["ProgramFiles"])
            ) if location
        }

        check_locations.add(os.path.join(sickrage.PROG_DIR, 'unrar\\unrar.exe'))

        for check in check_locations:
            if os.path.isfile(check):
                # Can use it?
                try:
                    rarfile.custom_check([check], True)
                    sickrage.app.unrar_tool = rarfile.UNRAR_TOOL = check
                    return True
                except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                    continue

        # Download
        sickrage.app.log.info('Trying to download unrar.exe and set the path')
        unrar_zip = os.path.join(sickrage.app.data_dir, 'unrar_win.zip')

        if WebSession().download("https://sickrage.ca/downloads/unrar_win.zip", filename=unrar_zip) and extract_zipfile(archive=unrar_zip,
                                                                                                                        targetDir=sickrage.app.data_dir):
            try:
                os.remove(unrar_zip)
            except OSError as e:
                sickrage.app.log.info("Unable to delete downloaded file {}: {}. You may delete it manually".format(unrar_zip, e.strerror))

            check = os.path.join(sickrage.app.data_dir, "unrar.exe")

            try:
                rarfile.custom_check([check], True)
                sickrage.app.unrar_tool = rarfile.UNRAR_TOOL = check
                sickrage.app.log.info('Successfully downloaded unrar.exe and set as unrar tool')
                return True
            except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                sickrage.app.log.info('Sorry, unrar was not set up correctly. Try installing WinRAR and '
                                      'make sure it is on the system PATH')
        else:
            sickrage.app.log.info('Unable to download unrar.exe')

    if sickrage.app.config.general.unpack:
        sickrage.app.log.info('Disabling UNPACK setting because no unrar is installed.')
        sickrage.app.config.general.unpack = False

def change_nzb_dir(nzb_dir):
    """
    Change NZB blackhole directory

    :param nzb_dir: New NZB Folder location
    :return: True on success, False on failure
    """
    if nzb_dir == '':
        sickrage.app.config.blackhole.nzb_dir = ''
        return True

    if os.path.normpath(sickrage.app.config.blackhole.nzb_dir) != os.path.normpath(nzb_dir):
        if make_dir(nzb_dir):
            sickrage.app.config.blackhole.nzb_dir = os.path.normpath(nzb_dir)
            sickrage.app.log.info("Changed NZB folder to " + nzb_dir)
        else:
            return False

    return True


def change_torrent_dir(torrent_dir):
    """
    Change Torrent blackhole directory

    :param torrent_dir: New torrent directory
    :return: True on success, False on failure
    """
    if torrent_dir == '':
        sickrage.app.config.blackhole.torrent_dir = ''
        return True

    if os.path.normpath(sickrage.app.config.blackhole.torrent_dir) != os.path.normpath(torrent_dir):
        if make_dir(torrent_dir):
            sickrage.app.config.blackhole.torrent_dir = os.path.normpath(torrent_dir)
            sickrage.app.log.info("Changed torrent folder to " + torrent_dir)
        else:
            return False

    return True


def change_tv_download_dir(tv_download_dir):
    """
    Change TV_DOWNLOAD directory (used by postprocessor)

    :param tv_download_dir: New tv download directory
    :return: True on success, False on failure
    """
    if tv_download_dir == '':
        sickrage.app.config.general.tv_download_dir = ''
        return True

    if os.path.normpath(sickrage.app.config.general.tv_download_dir) != os.path.normpath(tv_download_dir):
        if make_dir(tv_download_dir):
            sickrage.app.config.general.tv_download_dir = os.path.normpath(tv_download_dir)
            sickrage.app.log.info("Changed TV download folder to " + tv_download_dir)
        else:
            return False

    return True


def change_auto_postprocessor_freq(freq):
    """
    Change frequency of automatic postprocessing thread
    TODO: Make all thread frequency changers in config.py return True/False status

    :param freq: New frequency
    """
    sickrage.app.config.general.auto_postprocessor_freq = int(freq)
    if sickrage.app.config.general.auto_postprocessor_freq < sickrage.app.min_auto_postprocessor_freq:
        sickrage.app.config.general.auto_postprocessor_freq = sickrage.app.min_auto_postprocessor_freq

    sickrage.app.scheduler.reschedule_job(sickrage.app.auto_postprocessor.name, trigger='interval',
                                          minutes=sickrage.app.config.general.auto_postprocessor_freq)


def change_daily_searcher_freq(freq):
    """
    Change frequency of daily search thread

    :param freq: New frequency
    """
    sickrage.app.config.general.daily_searcher_freq = int(freq)
    if sickrage.app.config.general.daily_searcher_freq < sickrage.app.min_daily_searcher_freq:
        sickrage.app.config.general.daily_searcher_freq = sickrage.app.min_daily_searcher_freq

    sickrage.app.scheduler.reschedule_job(sickrage.app.daily_searcher.name, trigger='interval', minutes=sickrage.app.config.general.daily_searcher_freq)


def change_backlog_searcher_freq(freq):
    """
    Change frequency of backlog thread

    :param freq: New frequency
    """
    sickrage.app.config.general.backlog_searcher_freq = int(freq)
    if sickrage.app.config.general.backlog_searcher_freq < sickrage.app.min_backlog_searcher_freq:
        sickrage.app.config.general.backlog_searcher_freq = sickrage.app.min_backlog_searcher_freq

    sickrage.app.scheduler.reschedule_job(sickrage.app.backlog_searcher.name, trigger='interval', minutes=sickrage.app.config.general.backlog_searcher_freq)


def change_show_update_hour(freq):
    """
    Change frequency of show updater thread

    :param freq: New frequency
    """
    sickrage.app.config.general.show_update_hour = int(freq)
    if sickrage.app.config.general.show_update_hour < 0 or sickrage.app.config.general.show_update_hour > 23:
        sickrage.app.config.general.show_update_hour = 0

    sickrage.app.scheduler.reschedule_job(sickrage.app.show_updater.name, trigger='interval', hours=1,
                                          start_date=datetime.datetime.utcnow().replace(hour=sickrage.app.config.general.show_update_hour))


def change_subtitle_searcher_freq(freq):
    """
    Change frequency of subtitle thread

    :param freq: New frequency
    """
    sickrage.app.config.general.subtitle_searcher_freq = int(freq)
    if sickrage.app.config.general.subtitle_searcher_freq < sickrage.app.min_subtitle_searcher_freq:
        sickrage.app.config.general.subtitle_searcher_freq = sickrage.app.min_subtitle_searcher_freq

    sickrage.app.scheduler.reschedule_job(sickrage.app.subtitle_searcher.name, trigger='interval', hours=sickrage.app.config.general.subtitle_searcher_freq)


def change_failed_snatch_age(age):
    """
    Change age of failed snatches

    :param age: New age
    """
    sickrage.app.config.failed_snatches.age = int(age)
    if sickrage.app.config.failed_snatches.age < sickrage.app.min_failed_snatch_age:
        sickrage.app.config.failed_snatches.age = sickrage.app.min_failed_snatch_age


def change_version_notify(version_notify):
    """
    Change frequency of versioncheck thread

    :param version_notify: New frequency
    """
    sickrage.app.config.general.version_notify = version_notify
    if not sickrage.app.config.general.version_notify:
        sickrage.app.latest_version_string = None


def change_web_external_port(web_external_port):
    """
    Change web external port number

    :param web_external_port: New web external port number
    """
    if sickrage.app.config.general.enable_upnp:
        sickrage.app.upnp_client.delete_nat_portmap()
        sickrage.app.config.general.web_external_port = int(web_external_port)
        sickrage.app.upnp_client.add_nat_portmap()
