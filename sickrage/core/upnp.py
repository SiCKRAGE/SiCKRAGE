import netifaces
import threading
import time
from urlparse import urlparse

import ipaddress
import upnpclient

import sickrage


class UPNPClient(threading.Thread):
    _nat_portmap_lifetime = 30 * 60

    def __init__(self):
        super(UPNPClient, self).__init__(name='UPNP')
        self.stop = threading.Event()

    def run(self):
        upnp_dev = self._discover_upnp_device()
        if upnp_dev is not None:
            self._add_nat_portmap(upnp_dev)

        self.refresh_nat_portmap()

    def shutdown(self):
        self.stop.set()
        self.delete_nat_portmap()

        try:
            self.join(1)
        except:
            pass

    def refresh_nat_portmap(self):
        """Run an infinite loop refreshing our NAT port mapping.
        On every iteration we configure the port mapping with a lifetime of 30 minutes and then
        sleep for that long as well.
        """
        while not self.stop.is_set():
            time.sleep(self._nat_portmap_lifetime)
            self.add_nat_portmap()

    def add_nat_portmap(self):
        sickrage.app.log.debug("Setting up UPNP portmap...")

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
                sickrage.app.log.exception("Failed to setup UPnP portmap")
        except Exception:
            sickrage.app.log.exception("Failed to setup UPnP portmap")

    def _add_nat_portmap(self, upnp_dev):
        internal_ip = self._find_internal_ip_on_device_network(upnp_dev)
        if internal_ip is None:
            sickrage.app.log.warn("Unable to detect internal IP address in order to setup UPnP portmap")
            return

        for protocol, description in [('TCP', 'SiCKRAGE')]:
            upnp_dev.WANIPConn1.AddPortMapping(
                NewRemoteHost='0.0.0.0',
                NewExternalPort=sickrage.app.config.web_port,
                NewProtocol=protocol,
                NewInternalPort=sickrage.app.config.web_port,
                NewInternalClient=internal_ip,
                NewEnabled='1',
                NewPortMappingDescription=description,
                NewLeaseDuration=self._nat_portmap_lifetime,
            )

        sickrage.app.log.debug("UPnP port forwarding successfully setup")

    def delete_nat_portmap(self):
        upnp_dev = self._discover_upnp_device()
        if upnp_dev is None:
            return
        self._add_nat_portmap(upnp_dev)

    def _delete_nat_portmap(self, upnp_dev):
        internal_ip = self._find_internal_ip_on_device_network(upnp_dev)
        if internal_ip is None:
            sickrage.app.log.warn("Unable to detect internal IP address in order to delete UPnP portmap")
            return

        for protocol, description in [('TCP', 'SiCKRAGE')]:
            upnp_dev.WANIPConn1.DeletePortMapping(
                NewRemoteHost='0.0.0.0',
                NewExternalPort=sickrage.app.config.web_port,
                NewProtocol=protocol,
            )

        sickrage.app.log.debug("UPnP port forwarding successfully deleted")

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
        parsed_url = urlparse(upnp_dev.location)
        upnp_dev_net = ipaddress.ip_network(parsed_url.hostname + '/24', strict=False)

        for iface in netifaces.interfaces():
            for family, addresses in netifaces.ifaddresses(iface).items():
                if family != netifaces.AF_INET:
                    continue
                for item in addresses:
                    if ipaddress.ip_address(item['addr']) in upnp_dev_net:
                        return item['addr']
        return None
