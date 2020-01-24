import threading

import sickrage


class RSSCacheUpdater(object):
    def __init__(self):
        self.name = "RSSCACHE-UPDATER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        if self.amActive or not sickrage.app.config.enable_rss_cache and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        for providerID, providerObj in sickrage.app.search_providers.sort().items():
            if providerObj.is_enabled:
                sickrage.app.log.debug("Updating RSS cache for provider: [{}]".format(providerObj.name))
                threading.currentThread().setName(self.name + "::[" + providerObj.name + "]")
                providerObj.cache.update(force)
                threading.currentThread().setName(self.name)
                sickrage.app.log.debug("Updated RSS cache for provider: [{}]".format(providerObj.name))

        self.amActive = False
