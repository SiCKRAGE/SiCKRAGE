import lib.adba
from sickbeard import helpers, logger, db
import sickbeard
from time import time

class AnidbConnection(db.DBConnection):
    def __init__(self):
        db.DBConnection.__init__(self, "anidb.db")

class AnidbNotifications():
    def __init__(self):
        self.providerDB = None

    def _getdb(self):
        # init provider database if not done already
        if not self.providerDB:
            self.providerDB = AnidbConnection()
        return self.providerDB

    def add_notification_sub(self, aid):
        sickbeard.ADBA_CONNECTION.notifyadd(aid=aid, type=0, priority=1)

    def del_notification_sub(self, aid):
        sickbeard.ADBA_CONNECTION.notifydel(aid=aid, type=0, priority=1)

    def list_notification_sub(self, aid):
        sickbeard.ADBA_CONNECTION.notification(aid=aid, type=0, priority=1)

    def count_notification(self):
        result = sickbeard.ADBA_CONNECTION.notify()
        return result.datalines[0]['notifies']

    def list_notifications(self):
        result = sickbeard.ADBA_CONNECTION.notifylist()
        notifylist = []
        for notification in result.datalines:
            if notification['type'] == "N":
                notifylist.append(notification['nid'])
        return notifylist

    def get_notification(self, nid):
        result = sickbeard.ADBA_CONNECTION.notifyget(id=nid, type="N")
        fids=str(result.datalines[0]['fid'])
        return fids.split(",")

    def del_notification(self, nid):
        sickbeard.ADBA_CONNECTION.notifyack(id=nid, type="N")

    def get_group(self, gid=None, gname=None):
        if gid:
            myDB = self._getdb()
            sqlResult = myDB.select("SELECT gname, gshortname FROM group_response WHERE gid = ?", [gid])
            if len(sqlResult) == 1:
                return {'gname': sqlResult[0]['gname'],'gshortname': sqlResult[0]['gshortname']}
        if gname:
            sqlResult = myDB.select("SELECT gname, gshortname FROM group_response WHERE gname = ? or gshortname = ?", [gname,gname])
            if len(sqlResult) == 1:
                return sqlResult[0]['gid']

    def update_group(self, gid=None, gname=None):
        response = sickbeard.ADBA_CONNECTION.group(gid, gname)
        group = response.datalines[0]
        myDB = self._getdb()
        myDB.upsert("group_response",
                    {'time': int(time()), 'gname': group['name'],'gshortname': group['shortname']}, {'gid': group['gid']}
        )

    def run(self, force=False):
        if helpers.set_up_anidb_connection():
            if int(self.count_notification()) > 0:
                nids = self.list_notifications()
                for nid in nids:
                    fids = self.get_notification(nid)
                    for fid in fids:
                        file = lib.adba.Episode(sickbeard.ADBA_CONNECTION, fid=fid,
                                         paramsF=['aid', 'gid', 'eid', 'video_resolution', 'size', 'crc32', 'source', 'state',
                                                  'ed2k'], paramsA=['epno'],load=True)
                        myDB = self._getdb()
                        myDB.upsert("file_response",
                        {'time': int(time()), 'aid': file.aid, 'gid': file.gid, 'eid':file.eid, 'file_size': file.size,
                            'video_resolution': file.video_resolution, 'crc32': file.crc32, 'source': file.source,
                            'state': file.state, 'ed2k': file.ed2k, 'epno': file.epno}, {'fid': file.fid}
                        )
                    # mark the notification as read
                    self.del_notification(nid)
