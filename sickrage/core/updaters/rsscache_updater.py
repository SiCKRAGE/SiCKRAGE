import functools
import threading

import sickrage


class RSSCacheUpdater(object):
    def __init__(self):
        super(RSSCacheUpdater, self).__init__()
        self.name = "RSSCACHE-UPDATER"
        self.lock = threading.Lock()
        self.amActive = False

    async def task(self, force=False):
        if self.amActive or not sickrage.app.config.enable_rss_cache and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        for providerID, providerObj in sickrage.app.search_providers.sort().items():
            if providerObj.is_enabled:
                await sickrage.app.io_loop.run_in_executor(None, functools.partial(self.worker, providerObj, force))

        self.amActive = False

    def worker(self, provider, force):
        threading.currentThread().setName('{}::{}'.format(self.name, provider.name.upper()))
        sickrage.app.log.debug("Updating RSS cache")
        provider.cache.update(force)
        sickrage.app.log.debug("Updated RSS cache")
