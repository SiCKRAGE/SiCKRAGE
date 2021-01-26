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
import functools
import ipaddress
import threading
import time
from urllib.parse import urlparse

import upnpclient

import sickrage
from sickrage.core.helpers import get_internal_ip


class UPNPClient(object):
    _nat_portmap_lifetime = 30 * 60

    def __init__(self, *args, **kwargs):
        self.name = "UPNP"
        self.running = False

    def task(self, force=False):
        if self.running or not sickrage.app.config.general.enable_upnp:
            return

        try:
            self.running = True

            threading.currentThread().setName(self.name)

            self.add_nat_portmap()
        finally:
            self.running = False

    def refresh_nat_portmap(self):
        """Run an infinite loop refreshing our NAT port mapping.
        On every iteration we configure the port mapping with a lifetime of 30 minutes and then
        sleep for that long as well.
        """
        while True:
            time.sleep(self._nat_portmap_lifetime)
            self.add_nat_portmap()

    def add_nat_portmap(self):
        # sickrage.app.log.debug("Adding SiCKRAGE UPNP portmap...")

        try:
            upnp_dev = self._discover_upnp_device()
            if upnp_dev is None:
                return
            self._add_nat_portmap(upnp_dev)
        except upnpclient.soap.SOAPError as e:
            if e.args == (718, 'ConflictInMappingEntry'):
                # An entry already exists with the parameters we specified. Maybe the router
                # didn't clean it up after it expired or it has been configured by other piece
                # of software, either way we should not override it.
                # https://tools.ietf.org/id/draft-ietf-pcp-upnp-igd-interworking-07.html#errors
                sickrage.app.log.debug("UPnP port mapping already configured, not overriding it")
            else:
                sickrage.app.log.debug("Failed to add UPnP portmap")
        except Exception:
            sickrage.app.log.debug("Failed to add UPnP portmap")

    def _add_nat_portmap(self, upnp_dev):
        # internal_ip = self._find_internal_ip_on_device_network(upnp_dev)
        # if internal_ip is None:
        #     sickrage.app.log.warn("Unable to detect internal IP address in order to add UPnP portmap")
        #     return

        for protocol, description in [('TCP', 'SiCKRAGE')]:
            upnp_dev.WANIPConn1.AddPortMapping(
                NewRemoteHost='',
                NewExternalPort=sickrage.app.config.general.web_external_port,
                NewProtocol=protocol,
                NewInternalPort=sickrage.app.config.general.web_port,
                NewInternalClient=sickrage.app.web_host or '0.0.0.0',
                NewEnabled='1',
                NewPortMappingDescription=description,
                NewLeaseDuration=self._nat_portmap_lifetime,
            )

        # sickrage.app.log.debug("UPnP port forwarding successfully added")

    def delete_nat_portmap(self):
        # sickrage.app.log.debug("Deleting SiCKRAGE UPNP portmap...")

        upnp_dev = self._discover_upnp_device()
        if upnp_dev is None:
            return
        self._delete_nat_portmap(upnp_dev)

    def _delete_nat_portmap(self, upnp_dev):
        for protocol, description in [('TCP', 'SiCKRAGE')]:
            upnp_dev.WANIPConn1.DeletePortMapping(
                NewRemoteHost='',
                NewExternalPort=sickrage.app.config.general.web_external_port,
                NewProtocol=protocol,
            )

        # sickrage.app.log.debug("UPnP port forwarding successfully deleted")

    def _discover_upnp_device(self):
        devices = upnpclient.discover()
        if devices:
            for device in devices:
                try:
                    device.WANIPConn1
                except AttributeError:
                    continue

                return device

    def _find_internal_ip_on_device_network(self, upnp_dev):
        lan_ip = get_internal_ip()
        parsed_url = urlparse(upnp_dev.location)
        upnp_dev_net = ipaddress.ip_network(parsed_url.hostname + '/24', strict=False)

        if ipaddress.ip_address(str(lan_ip)) in upnp_dev_net:
            return lan_ip
        return None
