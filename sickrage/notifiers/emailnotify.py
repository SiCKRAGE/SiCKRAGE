# Authors:
# Derek Battams <derek@battams.ca>
# Pedro Jose Pereira Vieito (@pvieito) <pvieito@gmail.com>
#
# URL: https://github.com/echel0n/SickRage
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
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import sickrage
from sickrage.core.databases import main_db
from sickrage.notifiers import srNotifiers


class EmailNotifier(srNotifiers):
    def __init__(self):
        self.last_err = None

    def test_notify(self, host, port, smtp_from, use_tls, user, pwd, to):
        msg = MIMEText('This is a test message from SiCKRAGE.  If you\'re reading this, the test succeeded.')
        msg['Subject'] = 'SiCKRAGE: Test Message'
        msg['From'] = smtp_from
        msg['To'] = to
        msg['Date'] = formatdate(localtime=True)
        return self._sendmail(host, port, smtp_from, use_tls, user, pwd, [to], msg, True)

    def _notify_snatch(self, ep_name, title="Snatched:"):
        """
        Send a notification that an episode was snatched

        ep_name: The name of the episode that was snatched
        title: The title of the notification (optional)
        """
        ep_name = ep_name

        if sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSNATCH:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                sickrage.srCore.srLogger.warning('Skipping email notify because there are no configured recipients')
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                            "<body style='font-family:Helvetica, Arial, sans-serif;'><h3>SiCKRAGE Notification - Snatched</h3>\n<p>Show: <b>" + re.search(
                                    "(.+?) -.+", ep_name).group(1) + "</b></p>\n<p>Episode: <b>" + re.search(
                                    ".+ - (.+?-.+) -.+", ep_name).group(
                                    1) + "</b></p>\n\n<footer style='margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;'>Powered by SiCKRAGE.</footer></body>",
                            'html'))
                except:
                    try:
                        msg = MIMEText(ep_name)
                    except:
                        msg = MIMEText("Episode Snatched")

                msg['Subject'] = 'Snatched: ' + ep_name
                msg['From'] = sickrage.srCore.srConfig.EMAIL_FROM
                msg['To'] = ','.join(to)
                msg['Date'] = formatdate(localtime=True)
                if self._sendmail(sickrage.srCore.srConfig.EMAIL_HOST, sickrage.srCore.srConfig.EMAIL_PORT, sickrage.srCore.srConfig.EMAIL_FROM,
                                  sickrage.srCore.srConfig.EMAIL_TLS,
                                  sickrage.srCore.srConfig.EMAIL_USER, sickrage.srCore.srConfig.EMAIL_PASSWORD, to, msg):
                    sickrage.srCore.srLogger.debug("Snatch notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    sickrage.srCore.srLogger.error("Snatch notification ERROR: %s" % self.last_err)

    def _notify_download(self, ep_name, title="Completed:"):
        """
        Send a notification that an episode was downloaded

        ep_name: The name of the episode that was downloaded
        title: The title of the notification (optional)
        """
        ep_name = ep_name

        if sickrage.srCore.srConfig.EMAIL_NOTIFY_ONDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                sickrage.srCore.srLogger.warning('Skipping email notify because there are no configured recipients')
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                            "<body style='font-family:Helvetica, Arial, sans-serif;'><h3>SiCKRAGE Notification - Downloaded</h3>\n<p>Show: <b>" + re.search(
                                    "(.+?) -.+", ep_name).group(1) + "</b></p>\n<p>Episode: <b>" + re.search(
                                    ".+ - (.+?-.+) -.+", ep_name).group(
                                    1) + "</b></p>\n\n<footer style='margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;'>Powered by SiCKRAGE.</footer></body>",
                            'html'))
                except:
                    try:
                        msg = MIMEText(ep_name)
                    except:
                        msg = MIMEText('Episode Downloaded')

                msg['Subject'] = 'Downloaded: ' + ep_name
                msg['From'] = sickrage.srCore.srConfig.EMAIL_FROM
                msg['To'] = ','.join(to)
                msg['Date'] = formatdate(localtime=True)
                if self._sendmail(sickrage.srCore.srConfig.EMAIL_HOST, sickrage.srCore.srConfig.EMAIL_PORT, sickrage.srCore.srConfig.EMAIL_FROM,
                                  sickrage.srCore.srConfig.EMAIL_TLS,
                                  sickrage.srCore.srConfig.EMAIL_USER, sickrage.srCore.srConfig.EMAIL_PASSWORD, to, msg):
                    sickrage.srCore.srLogger.debug("Download notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    sickrage.srCore.srLogger.error("Download notification ERROR: %s" % self.last_err)

    def _notify_subtitle_download(self, ep_name, lang, title="Downloaded subtitle:"):
        """
        Send a notification that an subtitle was downloaded

        ep_name: The name of the episode that was downloaded
        lang: Subtitle language wanted
        """
        ep_name = ep_name

        if sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                sickrage.srCore.srLogger.warning('Skipping email notify because there are no configured recipients')
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                            "<body style='font-family:Helvetica, Arial, sans-serif;'><h3>SiCKRAGE Notification - Subtitle Downloaded</h3>\n<p>Show: <b>" + re.search(
                                    "(.+?) -.+", ep_name).group(1) + "</b></p>\n<p>Episode: <b>" + re.search(
                                    ".+ - (.+?-.+) -.+", ep_name).group(
                                    1) + "</b></p>\n<p>Language: <b>" + lang + "</b></p>\n\n<footer style='margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;'>Powered by SiCKRAGE.</footer></body>",
                            'html'))
                except:
                    try:
                        msg = MIMEText(ep_name + ": " + lang)
                    except:
                        msg = MIMEText("Episode Subtitle Downloaded")

                msg['Subject'] = lang + ' Subtitle Downloaded: ' + ep_name
                msg['From'] = sickrage.srCore.srConfig.EMAIL_FROM
                msg['To'] = ','.join(to)
                if self._sendmail(sickrage.srCore.srConfig.EMAIL_HOST, sickrage.srCore.srConfig.EMAIL_PORT, sickrage.srCore.srConfig.EMAIL_FROM,
                                  sickrage.srCore.srConfig.EMAIL_TLS,
                                  sickrage.srCore.srConfig.EMAIL_USER, sickrage.srCore.srConfig.EMAIL_PASSWORD, to, msg):
                    sickrage.srCore.srLogger.debug("Download notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    sickrage.srCore.srLogger.error("Download notification ERROR: %s" % self.last_err)

    def _notify_version_update(self, new_version="??"):
        pass

    def _generate_recipients(self, show):
        addrs = []

        # Grab the global recipients
        for addr in sickrage.srCore.srConfig.EMAIL_LIST.split(','):
            if (len(addr.strip()) > 0):
                addrs.append(addr)

        # Grab the recipients for the show
        for s in show:
            for subs in main_db.MainDB().select("SELECT notify_list FROM tv_shows WHERE show_name = ?", (s,)):
                if subs['notify_list']:
                    for addr in subs['notify_list'].split(','):
                        if (len(addr.strip()) > 0):
                            addrs.append(addr)

        addrs = set(addrs)
        sickrage.srCore.srLogger.debug('Notification recipients: %s' % addrs)
        return addrs

    def _sendmail(self, host, port, smtp_from, use_tls, user, pwd, to, msg, smtpDebug=False):
        sickrage.srCore.srLogger.debug('HOST: %s; PORT: %s; FROM: %s, TLS: %s, USER: %s, PWD: %s, TO: %s' % (
            host, port, smtp_from, use_tls, user, pwd, to))
        try:
            srv = smtplib.SMTP(host, int(port))
        except Exception as e:
            sickrage.srCore.srLogger.error("Exception generated while sending e-mail: " + str(e))
            sickrage.srCore.srLogger.debug(traceback.format_exc())
            return False

        if smtpDebug:
            srv.set_debuglevel(1)
        try:
            if (bool(use_tls)) or (len(user) > 0 and len(pwd) > 0):
                srv.ehlo()
                sickrage.srCore.srLogger.debug('Sent initial EHLO command!')
            if bool(use_tls):
                srv.starttls()
                sickrage.srCore.srLogger.debug('Sent STARTTLS command!')
            if len(user) > 0 and len(pwd) > 0:
                srv.login(str(user), str(pwd))
                sickrage.srCore.srLogger.debug('Sent LOGIN command!')

            srv.sendmail(smtp_from, to, msg.as_string())
            srv.quit()
            return True
        except Exception as e:
            self.last_err = '%s' % e
            return False

    def _parseEp(self, ep_name):
        ep_name = ep_name

        sep = " - "
        titles = ep_name.split(sep)
        titles.sort(key=len, reverse=True)
        sickrage.srCore.srLogger.debug("TITLES: %s" % titles)
        return titles
