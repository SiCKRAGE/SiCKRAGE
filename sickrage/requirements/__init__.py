#!/usr/bin/env python2
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

import os
import sys

import urllib3.contrib


def install_pip(path, user=False):
    print("Downloading pip ...")
    import urllib2

    url = "https://bootstrap.pypa.io/get-pip.py"
    file_name = os.path.join(path, url.split('/')[-1])
    u = urllib2.urlopen(url)
    with open(file_name, 'wb') as f:
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print("Downloading: %s Bytes: %s" % (file_name, file_size))
        file_size_dl = 0
        block_sz = 8192
        while True:
            buf = u.read(block_sz)
            if not buf:
                break
            file_size_dl += len(buf)
            f.write(buf)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status += chr(8) * (len(status) + 1)
            print(status),

    print("Installing pip ...")
    import subprocess
    subprocess.call([sys.executable, file_name] + ([], ['--user'])[user])

    print("Cleaning up downloaded pip files")
    os.remove(file_name)


def install_packages(requirements, user=False):
    import pip
    from pip.commands.install import InstallCommand

    pip_install_cmd = InstallCommand()

    # list installed packages
    try:
        installed = [x.project_name.lower() for x in pip.get_installed_distributions(local_only=True, user_only=user)]
    except:
        installed = []

    try:
        # read requirements file
        with open(requirements) as f:
            packages = [x.strip() for x in f.readlines() if x.strip().lower() not in installed]

        # install requirements packages
        options = pip_install_cmd.parse_args(['-q', '-I'])[0]
        options.use_user_site = user
        for i, pkg_name in enumerate(packages, start=1):
            print(r"[%3.2f%%]::Installing %s package" % (i * 100 / len(packages), pkg_name))
            pip_install_cmd.run(options, [pkg_name])

        if len(packages) > 0:
            return True
    except KeyboardInterrupt:
        raise


def upgrade_packages(user=False):
    from pip.commands.list import ListCommand
    from pip.commands.install import InstallCommand

    packages = []

    pip_install_cmd = InstallCommand()
    pip_list_cmd = ListCommand()

    while True:
        # list packages that need upgrading
        try:
            options = pip_list_cmd.parse_args(['--no-cache-dir', '--outdated'])[0]
            options.use_user_site = user

            packages = [p.project_name for p, y, _ in pip_list_cmd.find_packages_latest_versions(options)
                        if getattr(p, 'version', 0) != getattr(y, 'public', 0)]
        except:
            packages = []

        options = pip_install_cmd.parse_args(['-q', '--upgrade'])[0]
        options.use_user_site = user

        for i, pkg_name in enumerate(packages, start=1):
            try:
                print(r"[%3.2f%%]::Upgrading %s package" % (i * 100 / len(packages), pkg_name.lower()))
                pip_install_cmd.run(options, [pkg_name])
            except IndexError:
                continue
            except KeyboardInterrupt:
                raise
        else:
            break

    if len(packages) > 0:
        return True


def install_ssl(path, user=False):
    try:
        print("Installing and Patching SiCKRAGE SSL Contexts")
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
        urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST = "MEDIUM"
    except ImportError:
        return install_packages(os.path.join(path, 'ssl.txt'), user)


def install_requirements(path, optional=False, ssl=False, user=False):
    need_restart = False

    # install ssl packages
    if ssl:
        try:
            if install_ssl(path, user=user):
                os.execl(sys.executable, sys.executable, *sys.argv)
        except:
            pass

    print("Checking for required SiCKRAGE packages, please stand by ...")
    need_restart = install_packages(os.path.join(path, 'global.txt'), user)

    if optional:
        print("Checking for optional SiCKRAGE packages, please stand by ...")
        try:
            need_restart = install_packages(os.path.join(path, 'optional.txt'), user)
        except:
            pass

    print("Checking for upgradable SiCKRAGE packages, please stand by ...")
    need_restart = upgrade_packages(user)

    # silently restart sickrage if packages where installed or upgraded
    if need_restart:
        os.execl(sys.executable, sys.executable, *sys.argv)
