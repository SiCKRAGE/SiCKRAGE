import functools
import threading

import sickrage


class RSSCacheUpdater(object):
    def __init__(self):
        super(RSSCacheUpdater, self).__init__()
        self.name = "RSSCACHE-UPDATER"
        self.lock = threading.Lock()
        self.amActive = False

    def task(self, force=False):
        if self.amActive or not sickrage.app.config.enable_rss_cache and not force:
            return

        self.amActive = True

        for providerID, providerObj in sickrage.app.search_providers.sort().items():
            if providerObj.is_enabled:
                threading.currentThread().setName('{}::{}'.format(self.name, providerObj.name.upper()))
                providerObj.cache.update(force)

        self.amActive = False
