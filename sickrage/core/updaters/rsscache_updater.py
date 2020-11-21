import functools
import threading

import sickrage


class RSSCacheUpdater(object):
    def __init__(self):
        super(RSSCacheUpdater, self).__init__()
        self.name = "RSSCACHE-UPDATER"
        self.lock = threading.Lock()
        self.running = False

    def task(self, force=False):
        if self.running or not sickrage.app.config.general.enable_rss_cache and not force:
            return

        try:
            self.running = True

            for providerID, providerObj in sickrage.app.search_providers.sort().items():
                if providerObj.is_enabled:
                    threading.currentThread().setName('{}::{}'.format(self.name, providerObj.name.upper()))
                    providerObj.cache.update(force)
        finally:
            self.running = False
