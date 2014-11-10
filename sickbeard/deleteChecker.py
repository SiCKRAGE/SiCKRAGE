# Author: Frank Fenton
# URL: http://code.google.com/p/sickbeard/
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

import os
import traceback
import datetime
import sickbeard

from sickbeard import db
from sickbeard import tv
from sickbeard import logger
from sickbeard import helpers

class DeleteChecker():

    def run(self, force=False):
        logger.log(u"Begin check if files need to be deleted/trashed")

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM delete_media")

        for sqlEp in sqlResults:

            if datetime.datetime.strptime(sqlEp["action_time"], "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(minutes=sickbeard.DELETE_CHECKER_FREQUENCY) < datetime.datetime.now():

                showObj = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))
                if not showObj:
                    logger.log(u'Show not found', logger.DEBUG)
                    return
                
                epObj = showObj.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
                if isinstance(epObj, str):
                    logger.log(u'Episode not found', logger.DEBUG)
                    return

                if epObj.deleteMedia() == False:
                    logger.log(u'Removing file(s) has failed. Retry on next run', logger.ERROR)
                else:
                    sql_l = [["DELETE FROM delete_media WHERE showid=? AND season=? AND episode=?", [sqlEp["showid"], sqlEp["season"], sqlEp["episode"]]],
                             ["UPDATE tv_episodes SET delete_media=? WHERE showid=? AND season=? AND episode=?", ['', sqlEp["showid"], sqlEp["season"], sqlEp["episode"]]]]
                    myDB = db.DBConnection()
                    myDB.mass_action(sql_l)