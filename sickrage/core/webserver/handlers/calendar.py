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

import datetime

from dateutil.tz import gettz
from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import try_int
from sickrage.core.tv.show.helpers import get_show_list
from sickrage.core.webserver.handlers.base import BaseHandler


class CalendarHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if sickrage.app.config.general.calendar_unprotected:
            return self.calendar()
        else:
            return self.calendar_auth()

    @authenticated
    def calendar_auth(self):
        return self.calendar()

    def calendar(self):
        """ Provides a subscribeable URL for iCal subscriptions
        """

        utc = gettz('GMT')

        sickrage.app.log.info("Receiving iCal request from %s" % self.request.remote_ip)

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SiCKRAGE\r\n'
        ical += 'X-WR-CALDESC:SiCKRAGE\r\n'
        ical += 'PRODID://SiCKRAGE Upcoming Episodes//\r\n'

        # Limit dates
        past_date = datetime.date.today() + datetime.timedelta(weeks=-52)
        future_date = datetime.date.today() + datetime.timedelta(weeks=52)

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        for show in get_show_list():
            if show.status.lower() not in ['continuing', 'returning series'] or show.paused:
                continue

            for episode in show.episodes:
                if not past_date <= episode.airdate < future_date:
                    continue

                air_date_time = sickrage.app.tz_updater.parse_date_time(episode.airdate, show.airs,
                                                                        show.network).astimezone(utc)
                air_date_time_end = air_date_time + datetime.timedelta(minutes=try_int(show.runtime, 60))

                # Create event for episode
                ical += 'BEGIN:VEVENT\r\n'
                ical += 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime("%H%M%S") + 'Z\r\n'
                ical += 'DTEND:' + air_date_time_end.strftime("%Y%m%d") + 'T' + air_date_time_end.strftime(
                    "%H%M%S") + 'Z\r\n'
                if sickrage.app.config.general.calendar_icons:
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-ICON:https://www.sickrage.ca/favicon.ico\r\n'
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n'
                ical += 'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(show.name, episode.season, episode.episode, episode.name)
                ical += 'UID:SiCKRAGE-' + str(datetime.date.today().isoformat()) + '-' + \
                        show.name.replace(" ", "-") + '-E' + str(episode.episode) + \
                        'S' + str(episode.season) + '\r\n'
                if episode.description:
                    ical += 'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show.airs or '(Unknown airs)'),
                        (show.network or 'Unknown network'),
                        episode.description.splitlines()[0])
                else:
                    ical += 'DESCRIPTION:' + (show.airs or '(Unknown airs)') + ' on ' + (
                            show.network or 'Unknown network') + '\r\n'

                ical += 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical
