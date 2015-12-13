#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

# Dynamic patch system
# function naming scheme: targetmodule_targetfunction

import os
import sys
import stat
import shutil
import inspect


def shutil_copyfile(src, dst):
    """Copy data from src to dst"""
    if shutil._samefile(src, dst):
        raise shutil.Error("`%s` and `%s` are the same file" % (src, dst))
    elif not os.path.exists(src) or os.path.isdir(src):
        return

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                try:
                    raise shutil.SpecialFileError("`%s` is a named pipe" % fn)
                except NameError:
                    raise shutil.Error("`%s` is a named pipe" % fn)

    try:
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            for x in iter(lambda: fin.read(128 * 1024), ""):
                fout.write(x)
    except Exception:
        raise


# auto_apply patches
for name, patch in inspect.getmembers(sys.modules[__name__], inspect.isfunction):
    try:
        mod, func = name.split("_", 1)
        if not hasattr(sys.modules, mod):
            sys.modules[mod] = __import__(mod)
        sys.modules[mod].__dict__[func] = patch
    except:
        continue
