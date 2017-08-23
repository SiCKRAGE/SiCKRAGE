from __future__ import absolute_import, division, print_function

from threading import Lock


class KeyLock(object):
    def __init__(self, lock=Lock):
        self._lock = lock

        self._create_lock = Lock()
        self._locks = {}

    def __getitem__(self, key):
        # Return lock if it's available
        if key in self._locks:
            return self._locks[key]

        # Create new lock for `key` (synchronized)
        with self._create_lock:
            if key not in self._locks:
                self._locks[key] = self._lock()

            return self._locks[key]
