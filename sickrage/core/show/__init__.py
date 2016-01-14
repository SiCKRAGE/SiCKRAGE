from datetime import date

import sickrage
from sickrage.core.common import Quality, SKIPPED, WANTED
from sickrage.core.databases import main_db
from sickrage.core.exceptions import CantRefreshShowException, \
    CantRemoveShowException, MultipleShowObjectsException
from sickrage.core.helpers import findCertainShow


class Show:
    @staticmethod
    def delete(indexer_id, remove_files=False):
        """
        Try to delete a show
        :param indexer_id: The unique id of the show to delete
        :param remove_files: ``True`` to remove the files associated with the show, ``False`` otherwise
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickrage.SHOWQUEUE.removeShow(show, bool(remove_files))
        except CantRemoveShowException as exception:
            return exception, show

        return None, show

    @staticmethod
    def overall_stats():
        shows = sickrage.showList
        today = str(date.today().toordinal())

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER
        total_status = [SKIPPED, WANTED]

        results = main_db.MainDB().select(
                'SELECT airdate, status '
                'FROM tv_episodes '
                'WHERE season > 0 '
                'AND episode > 0 '
                'AND airdate > 1'
        )

        stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in shows if show.paused == 0 and show.status == 'Continuing']),
                'total': len(shows),
            },
        }

        for result in results:
            if result[b'status'] in downloaded_status:
                stats[b'episodes'][b'downloaded'] += 1
                stats[b'episodes'][b'total'] += 1
            elif result[b'status'] in snatched_status:
                stats[b'episodes'][b'snatched'] += 1
                stats[b'episodes'][b'total'] += 1
            elif result[b'airdate'] <= today and result[b'status'] in total_status:
                stats[b'episodes'][b'total'] += 1

        return stats

    @staticmethod
    def pause(indexer_id, pause=None):
        """
        Change the pause state of a show
        :param indexer_id: The unique id of the show to update
        :param pause: ``True`` to pause the show, ``False`` to resume the show, ``None`` to toggle the pause state
        :return: A tuple containing:
         - an error message if the pause state could not be changed, ``None`` otherwise
         - the show object that was updated, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        if pause is None:
            show.paused = not show.paused
        else:
            show.paused = pause

        show.saveToDB()

        return None, show

    @staticmethod
    def refresh(indexer_id):
        """
        Try to refresh a show
        :param indexer_id: The unique id of the show to refresh
        :return: A tuple containing:
         - an error message if the show could not be refreshed, ``None`` otherwise
         - the show object that was refreshed, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickrage.SHOWQUEUE.refreshShow(show)
        except CantRefreshShowException as exception:
            return exception, show

        return None, show

    @staticmethod
    def _validate_indexer_id(indexer_id):
        """
        Check that the provided indexer_id is valid and corresponds with a known show
        :param indexer_id: The indexer id to check
        :return: A tuple containing:
         - an error message if the indexer id is not correct, ``None`` otherwise
         - the show object corresponding to ``indexer_id`` if it exists, ``None`` otherwise
        """

        if indexer_id is None:
            return 'Invalid show ID', None

        try:
            show = findCertainShow(sickrage.showList, int(indexer_id))
        except MultipleShowObjectsException:
            return 'Unable to find the specified show', None

        return None, show
