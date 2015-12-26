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

import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import re

import sickbeard

import logging
from sickbeard import db
from sickrage.helper.encoding import ss


class EmailNotifier:
    def __init__(self):
        self.last_err = None

    def test_notify(self, host, port, smtp_from, use_tls, user, pwd, to):
        msg = MIMEText('This is a test message from SiCKRAGE.  If you\'re reading this, the test succeeded.')
        msg[b'Subject'] = 'SiCKRAGE: Test Message'
        msg[b'From'] = smtp_from
        msg[b'To'] = to
        msg[b'Date'] = formatdate(localtime=True)
        return self._sendmail(host, port, smtp_from, use_tls, user, pwd, [to], msg, True)

    def notify_snatch(self, ep_name, title="Snatched:"):
        """
        Send a notification that an episode was snatched

        ep_name: The name of the episode that was snatched
        title: The title of the notification (optional)
        """
        ep_name = ss(ep_name)

        if sickbeard.EMAIL_NOTIFY_ONSNATCH:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                logging.warning('Skipping email notify because there are no configured recipients')
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

                msg[b'Subject'] = 'Snatched: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logging.debug("Snatch notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    logging.error("Snatch notification ERROR: %s" % self.last_err)

    def notify_download(self, ep_name, title="Completed:"):
        """
        Send a notification that an episode was downloaded

        ep_name: The name of the episode that was downloaded
        title: The title of the notification (optional)
        """
        ep_name = ss(ep_name)

        if sickbeard.EMAIL_NOTIFY_ONDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                logging.warning('Skipping email notify because there are no configured recipients')
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

                msg[b'Subject'] = 'Downloaded: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logging.debug("Download notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    logging.error("Download notification ERROR: %s" % self.last_err)

    def notify_subtitle_download(self, ep_name, lang, title="Downloaded subtitle:"):
        """
        Send a notification that an subtitle was downloaded

        ep_name: The name of the episode that was downloaded
        lang: Subtitle language wanted
        """
        ep_name = ss(ep_name)

        if sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if len(to) == 0:
                logging.warning('Skipping email notify because there are no configured recipients')
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

                msg[b'Subject'] = lang + ' Subtitle Downloaded: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logging.debug("Download notification sent to [%s] for '%s'" % (to, ep_name))
                else:
                    logging.error("Download notification ERROR: %s" % self.last_err)

    def notify_git_update(self, new_version="??"):
        pass

    def _generate_recipients(self, show):
        addrs = []

        # Grab the global recipients
        for addr in sickbeard.EMAIL_LIST.split(','):
            if (len(addr.strip()) > 0):
                addrs.append(addr)

        # Grab the recipients for the show
        myDB = db.DBConnection()
        for s in show:
            for subs in myDB.select("SELECT notify_list FROM tv_shows WHERE show_name = ?", (s,)):
                if subs[b'notify_list']:
                    for addr in subs[b'notify_list'].split(','):
                        if (len(addr.strip()) > 0):
                            addrs.append(addr)

        addrs = set(addrs)
        logging.debug('Notification recipients: %s' % addrs)
        return addrs

    def _sendmail(self, host, port, smtp_from, use_tls, user, pwd, to, msg, smtpDebug=False):
        logging.debug('HOST: %s; PORT: %s; FROM: %s, TLS: %s, USER: %s, PWD: %s, TO: %s' % (
            host, port, smtp_from, use_tls, user, pwd, to))
        try:
            srv = smtplib.SMTP(host, int(port))
        except Exception as e:
            logging.error("Exception generated while sending e-mail: " + str(e))
            logging.debug(traceback.format_exc())
            return False

        if smtpDebug:
            srv.set_debuglevel(1)
        try:
            if (use_tls == '1' or use_tls == True) or (len(user) > 0 and len(pwd) > 0):
                srv.ehlo()
                logging.debug('Sent initial EHLO command!')
            if use_tls == '1' or use_tls == True:
                srv.starttls()
                logging.debug('Sent STARTTLS command!')
            if len(user) > 0 and len(pwd) > 0:
                srv.login(user, pwd)
                logging.debug('Sent LOGIN command!')
            srv.sendmail(smtp_from, to, msg.as_string())
            srv.quit()
            return True
        except Exception as e:
            self.last_err = '%s' % e
            return False

    def _parseEp(self, ep_name):
        ep_name = ss(ep_name)

        sep = " - "
        titles = ep_name.split(sep)
        titles.sort(key=len, reverse=True)
        logging.debug("TITLES: %s" % titles)
        return titles


notifier = EmailNotifier
