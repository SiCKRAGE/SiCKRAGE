from __future__ import absolute_import, division, print_function

import logging
from threading import RLock

from six.moves import _thread as thread

from trakt.core.helpers import synchronized

log = logging.getLogger(__name__)


class ListCollection(object):
    def __init__(self, *lists):
        self._lists = lists or []
        self._lock = RLock()

    @synchronized(lambda self: self._lock)
    def append(self, value):
        l = self._lists[-1]

        if type(l) is not list:
            raise ValueError()

        l.append(value)

    @synchronized(lambda self: self._lock)
    def find_list(self, index):
        count = len(self)

        if index >= count:
            raise IndexError()

        if index < 0:
            index += count

        pos = 0

        for l in self.lists():
            l_len = len(l)

            if pos <= index < pos + l_len:
                return l, index - pos
            else:
                pos += l_len

        return None, None

    @synchronized(lambda self: self._lock)
    def lists(self, resolve=True):
        for l in self._lists:
            if resolve and callable(l):
                l = l()

            yield l

    @synchronized(lambda self: self._lock)
    def pop(self, index=None):
        if index is None:
            index = len(self) - 1

        list, index = self.find_list(index)

        if list is None:
            raise IndexError()

        return list.pop(index)

    @synchronized(lambda self: self._lock)
    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for x in range(len(self)):
            if self[x] != other[x]:
                return False

        return True

    @synchronized(lambda self: self._lock)
    def __contains__(self, value):
        for x in self:
            if x == value:
                return True

        return False

    def __getitem__(self, index):
        list, index = self.find_list(index)

        if list is None:
            raise IndexError()

        return list[index]

    @synchronized(lambda self: self._lock)
    def __iter__(self):
        for l in self.lists():
            # Yield items from each list
            for x in l:
                yield x

    @synchronized(lambda self: self._lock)
    def __len__(self):
        return sum([len(l) for l in self.lists()])

    def __setitem__(self, index, value):
        list, index = self.find_list(index)

        if list is None:
            raise IndexError()

        list[index] = value

    def __repr__(self):
        return '[%s]' % ', '.join(repr(x) for x in self)

    __hash__ = None


class ContextCollection(object):
    def __init__(self, base=None):
        self.base = base or []

        self._lock = RLock()
        self._threads = {}

    @synchronized(lambda self: self._lock)
    def build(self, ident):
        if ident not in self._threads:
            self._threads[ident] = ListCollection(lambda: self.base, [])

        return self._threads[ident]

    @property
    def current(self):
        ident = thread.get_ident()

        try:
            return self._threads[ident]
        except KeyError:
            return self.build(ident)

    def append(self, value):
        self.current.append(value)

    @synchronized(lambda self: self._lock)
    def clear(self):
        ident = thread.get_ident()

        if ident not in self._threads:
            return

        del self._threads[ident]

    def pop(self, index=None):
        return self.current.pop(index)

    def __getitem__(self, index):
        return self.current[index]

    def __len__(self):
        return len(self.current)
