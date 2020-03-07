# import os
#
# from dogpile.cache import make_region
# from dogpile.cache.backends.file import AbstractFileLock
# from dogpile.util import ReadWriteMutex
#
#
# class MutexLock(AbstractFileLock):
#     """:class:`MutexLock` is a thread-based rw lock based on :class:`dogpile.core.ReadWriteMutex`."""
#
#     def __init__(self, filename):
#         """Constructor.
#         :param filename:
#         """
#         self.mutex = ReadWriteMutex()
#
#     def acquire_read_lock(self, wait):
#         """Default acquire_read_lock."""
#         ret = self.mutex.acquire_read_lock(wait)
#         return wait or ret
#
#     def acquire_write_lock(self, wait):
#         """Default acquire_write_lock."""
#         ret = self.mutex.acquire_write_lock(wait)
#         return wait or ret
#
#     def release_read_lock(self):
#         """Default release_read_lock."""
#         return self.mutex.release_read_lock()
#
#     def release_write_lock(self):
#         """Default release_write_lock."""
#         return self.mutex.release_write_lock()
#
#
# def configure_regions(cache_dir, replace_existing_backend=False):
#     tv_episodes_cache.configure('dogpile.cache.dbm', replace_existing_backend=replace_existing_backend,
#                                 arguments={'filename': os.path.join(cache_dir, 'tv_episodes.dbm'), 'lock_factory': MutexLock})
#
#
# tv_episodes_cache = make_region()
