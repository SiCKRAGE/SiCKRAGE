# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################




class Immutable(object):
    _mutable = False

    def __setattr__(self, name, value):
        if self._mutable or name == '_mutable':
            super(Immutable, self).__setattr__(name, value)
        else:
            raise TypeError("Can't modify immutable instance")

    def __delattr__(self, name):
        if self._mutable:
            super(Immutable, self).__delattr__(name)
        else:
            raise TypeError("Can't modify immutable instance")

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(['{0}={1}'.format(k, repr(v)) for k, v in self])
        )

    def __iter__(self):
        l = self.__dict__.keys()
        l.sort()
        for k in l:
            if not k.startswith('_'):
                yield k, getattr(self, k)

    @staticmethod
    def mutablemethod(f):
        def func(self, *args, **kwargs):
            if isinstance(self, Immutable):
                old_mutable = self._mutable
                self._mutable = True
                res = f(self, *args, **kwargs)
                self._mutable = old_mutable
            else:
                res = f(self, *args, **kwargs)
            return res

        return func
