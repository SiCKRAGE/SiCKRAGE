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



import datetime
import re
from base64 import b64decode
from binascii import unhexlify
from collections import OrderedDict
from decimal import Decimal
from functools import partial

import requests
from dateutil.parser import parse as parse_date
from lxml import etree
from requests.compat import urljoin, urlparse

from .const import HTTP_TIMEOUT
from .marshal import marshal_value
from .soap import SOAP
from .util import _getLogger


class UPNPError(Exception):
    """
    Exception class for UPnP errors.
    """
    pass


class InvalidActionException(UPNPError):
    """
    Action doesn't exist.
    """
    pass


class ValidationError(UPNPError):
    """
    Given value didn't validate with the given data type.
    """
    def __init__(self, reasons):
        super(ValidationError, self).__init__()
        self.reasons = reasons


class UnexpectedResponse(UPNPError):
    """
    Got a response we didn't expect.
    """
    pass


class CallActionMixin(object):
    def __call__(self, action_name, **kwargs):
        """
        Convenience method for quickly finding and calling an Action on a
        Service. Must have implemented a `find_action(action_name)` method.
        """
        action = self.find_action(action_name)
        if action is not None:
            return action(**kwargs)
        raise InvalidActionException('Action with name %r does not exist.' % action_name)


class Device(CallActionMixin):
    """
    UPNP Device represention.
    This class represents an UPnP device. `location` is an URL to a control XML
    file, per UPnP standard section 2.3 ('Device Description'). This MUST match
    the URL as given in the 'Location' header when using discovery (SSDP).
    `device_name` is a name for the device, which may be obtained using the
    SSDP class or may be made up by the caller.

    Raises urllib2.HTTPError when the location is invalid

    Example:

    >>> device = Device('http://192.168.1.254:80/upnp/IGD.xml')
    >>> for service in device.services:
    ...     print service.service_id
    ...
    urn:upnp-org:serviceId:layer3f
    urn:upnp-org:serviceId:wancic
    urn:upnp-org:serviceId:wandsllc:pvc_Internet
    urn:upnp-org:serviceId:wanipc:Internet
    """
    def __init__(
            self, location, device_name=None, ignore_urlbase=False,
            http_auth=None, http_headers=None):
        """
        Create a new Device instance. `location` is an URL to an XML file
        describing the server's services.
        """
        self.location = location
        self.device_name = location if device_name is None else device_name
        self.services = []
        self.service_map = {}
        self._log = _getLogger('Device')

        self.http_auth = http_auth
        self.http_headers = http_headers

        resp = requests.get(
          location,
          timeout=HTTP_TIMEOUT,
          auth=self.http_auth,
          headers=self.http_headers
        )
        resp.raise_for_status()

        root = etree.fromstring(resp.content)
        findtext = partial(root.findtext, namespaces=root.nsmap)

        self.device_type = findtext('device/deviceType')
        self.friendly_name = findtext('device/friendlyName')
        self.manufacturer = findtext('device/manufacturer')
        self.manufacturer_url = findtext('device/manufacturerURL')
        self.model_description = findtext('device/modelDescription')
        self.model_name = findtext('device/modelName')
        self.model_number = findtext('device/modelNumber')
        self.serial_number = findtext('device/serialNumber')
        self.udn = findtext('device/UDN')

        self._url_base = findtext('URLBase')
        if self._url_base is None or ignore_urlbase:
            # If no URL Base is given, the UPnP specification says: "the base
            # URL is the URL from which the device description was retrieved"
            self._url_base = self.location
        self._root_xml = root
        self._findtext = findtext
        self._find = partial(root.find, namespaces=root.nsmap)
        self._findall = partial(root.findall, namespaces=root.nsmap)
        self._read_services()

    def __repr__(self):
        return "<Device '%s'>" % (self.friendly_name)

    def __getattr__(self, name):
        """
        Allow Services to be returned as members of the Device.
        """
        try:
            return self.service_map[name]
        except KeyError:
            raise AttributeError('No attribute or service found with name %r.' % name)

    def __getitem__(self, key):
        """
        Allow Services to be returned as dictionary keys of the Device.
        """
        return self.service_map[key]

    def __dir__(self):
        """
        Add Service names to `dir(device)` output for use with tab-completion in repl.
        """
        return super(Device, self).__dir__() + list(self.service_map.keys())

    @property
    def actions(self):
        actions = []
        for service in self.services:
            actions.extend(service.actions)
        return actions

    def _read_services(self):
        """
        Read the control XML file and populate self.services with a list of
        services in the form of Service class instances.
        """
        # The double slash in the XPath is deliberate, as services can be
        # listed in two places (Section 2.3 of uPNP device architecture v1.1)
        for node in self._findall('device//serviceList/service'):
            findtext = partial(node.findtext, namespaces=self._root_xml.nsmap)
            svc = Service(
                self,
                self._url_base,
                findtext('serviceType'),
                findtext('serviceId'),
                findtext('controlURL'),
                findtext('SCPDURL'),
                findtext('eventSubURL')
            )
            self._log.debug(
                '%s: Service %r at %r', self.device_name, svc.service_type, svc.scpd_url)
            self.services.append(svc)
            self.service_map[svc.name] = svc

    def find_action(self, action_name):
        """Find an action by name.
        Convenience method that searches through all the services offered by
        the Server for an action and returns an Action instance. If the action
        is not found, returns None. If multiple actions with the same name are
        found it returns the first one.
        """
        for service in self.services:
            action = service.find_action(action_name)
            if action is not None:
                return action


class Service(CallActionMixin):
    """
    Service Control Point Definition. This class reads an SCPD XML file and
    parses the actions and state variables. It can then be used to call
    actions.
    """
    def __init__(self, device, url_base, service_type, service_id,
                 control_url, scpd_url, event_sub_url):
        self.device = device
        self._url_base = url_base
        self.service_type = service_type
        self.service_id = service_id
        self._control_url = control_url
        self.scpd_url = scpd_url
        self._event_sub_url = event_sub_url

        self.actions = []
        self.action_map = {}
        self.statevars = {}
        self._log = _getLogger('Service')

        self._log.debug('%s url_base: %s', self.service_id, self._url_base)
        self._log.debug('%s SCPDURL: %s', self.service_id, self.scpd_url)
        self._log.debug('%s controlURL: %s', self.service_id, self._control_url)
        self._log.debug('%s eventSubURL: %s', self.service_id, self._event_sub_url)

        url = urljoin(self._url_base, self.scpd_url)
        self._log.debug('Reading %s', url)
        resp = requests.get(
          url,
          timeout=HTTP_TIMEOUT,
          auth=self.device.http_auth,
          headers=self.device.http_headers
        )
        resp.raise_for_status()
        self.scpd_xml = etree.fromstring(resp.content)
        self._find = partial(self.scpd_xml.find, namespaces=self.scpd_xml.nsmap)
        self._findtext = partial(self.scpd_xml.findtext, namespaces=self.scpd_xml.nsmap)
        self._findall = partial(self.scpd_xml.findall, namespaces=self.scpd_xml.nsmap)

        self._read_state_vars()
        self._read_actions()

    def __repr__(self):
        return "<Service service_id='%s'>" % (self.service_id)

    def __getattr__(self, name):
        """
        Allow Actions to be returned as members of the Service.
        """
        try:
            return self.action_map[name]
        except KeyError:
            raise AttributeError('No attribute or action found with name %r.' % name)

    def __getitem__(self, key):
        """
        Allow Actions to be returned as dictionary keys of the Service.
        """
        return self.action_map[key]

    def __dir__(self):
        """
        Add Action names to `dir(service)` output for use with tab-completion in repl.
        """
        return super(Service, self).__dir__() + [a.name for a in self.actions]

    @property
    def name(self):
        try:
            return self.service_id[self.service_id.rindex(":")+1:]
        except ValueError:
            return self.service_id

    def _read_state_vars(self):
        for statevar_node in self._findall('serviceStateTable/stateVariable'):
            findtext = partial(statevar_node.findtext, namespaces=statevar_node.nsmap)
            findall = partial(statevar_node.findall, namespaces=statevar_node.nsmap)
            name = findtext('name')
            datatype = findtext('dataType')
            send_events = statevar_node.attrib.get('sendEvents', 'yes').lower() == 'yes'
            allowed_values = set([e.text for e in findall('allowedValueList/allowedValue')])
            self.statevars[name] = dict(
                name=name,
                datatype=datatype,
                allowed_values=allowed_values,
                send_events=send_events
            )

    def _read_actions(self):
        action_url = urljoin(self._url_base, self._control_url)

        for action_node in self._findall('actionList/action'):
            name = action_node.findtext('name', namespaces=action_node.nsmap)
            argsdef_in = []
            argsdef_out = []
            for arg_node in action_node.findall(
                    'argumentList/argument', namespaces=action_node.nsmap):
                findtext = partial(arg_node.findtext, namespaces=arg_node.nsmap)
                arg_name = findtext('name')
                arg_statevar = self.statevars[findtext('relatedStateVariable')]
                if findtext('direction').lower() == 'in':
                    argsdef_in.append((arg_name, arg_statevar))
                else:
                    argsdef_out.append((arg_name, arg_statevar))
            action = Action(self, action_url, self.service_type, name, argsdef_in, argsdef_out)
            self.action_map[name] = action
            self.actions.append(action)

    @staticmethod
    def validate_subscription_response(resp):
        lc_headers = {k.lower(): v for k, v in resp.headers.items()}
        try:
            sid = lc_headers['sid']
        except KeyError:
            raise UnexpectedResponse('Event subscription call returned without a "SID" header')
        try:
            timeout_str = lc_headers['timeout'].lower()
        except KeyError:
            raise UnexpectedResponse('Event subscription call returned without a "Timeout" header')
        if not timeout_str.startswith('second-'):
            raise UnexpectedResponse(
                'Event subscription call returned an invalid timeout value: %r' % timeout_str)
        timeout_str = timeout_str[len('Second-'):]
        try:
            timeout = None if timeout_str == 'infinite' else int(timeout_str)
        except ValueError:
            raise UnexpectedResponse(
                'Event subscription call returned a timeout value which wasn\'t "infinite" or an in'
                'teger')
        return sid, timeout

    @staticmethod
    def validate_subscription_renewal_response(resp):
        lc_headers = {k.lower(): v for k, v in resp.headers.items()}
        try:
            timeout_str = lc_headers['timeout'].lower()
        except KeyError:
            raise UnexpectedResponse('Event subscription call returned without a "Timeout" header')
        if not timeout_str.startswith('second-'):
            raise UnexpectedResponse(
                'Event subscription call returned an invalid timeout value: %r' % timeout_str)
        timeout_str = timeout_str[len('Second-'):]
        try:
            timeout = None if timeout_str == 'infinite' else int(timeout_str)
        except ValueError:
            raise UnexpectedResponse(
                'Event subscription call returned a timeout value which wasn\'t "infinite" or an in'
                'teger')
        return timeout

    def find_action(self, action_name):
        try:
            return self.action_map[action_name]
        except KeyError:
            pass

    def subscribe(self, callback_url, timeout=None):
        """
        Set up a subscription to the events offered by this service.
        """
        url = urljoin(self._url_base, self._event_sub_url)
        headers = dict(
            HOST=urlparse(url).netloc,
            CALLBACK='<%s>' % callback_url,
            NT='upnp:event'
        )
        if timeout is not None:
            headers['TIMEOUT'] = 'Second-%s' % timeout
        resp = requests.request('SUBSCRIBE', url, headers=headers, auth=self.device.http_auth)
        resp.raise_for_status()
        return Service.validate_subscription_response(resp)

    def renew_subscription(self, sid, timeout=None):
        """
        Renews a previously configured subscription.
        """
        url = urljoin(self._url_base, self._event_sub_url)
        headers = dict(
            HOST=urlparse(url).netloc,
            SID=sid
        )
        if timeout is not None:
            headers['TIMEOUT'] = 'Second-%s' % timeout
        resp = requests.request('SUBSCRIBE', url, headers=headers, auth=self.device.http_auth)
        resp.raise_for_status()
        return Service.validate_subscription_renewal_response(resp)

    def cancel_subscription(self, sid):
        """
        Unsubscribes from a previously configured subscription.
        """
        url = urljoin(self._url_base, self._event_sub_url)
        headers = dict(
            HOST=urlparse(url).netloc,
            SID=sid
        )
        resp = requests.request('UNSUBSCRIBE', url, headers=headers, auth=self.device.http_auth)
        resp.raise_for_status()


class Action(object):
    def __init__(self, service, url, service_type, name, argsdef_in=None, argsdef_out=None):
        if argsdef_in is None:
            argsdef_in = []
        if argsdef_out is None:
            argsdef_out = []
        self.service = service
        self.url = url
        self.service_type = service_type
        self.name = name
        self.argsdef_in = argsdef_in
        self.argsdef_out = argsdef_out
        self._log = _getLogger('Action')

    def __repr__(self):
        return "<Action '%s'>" % (self.name)

    def __call__(self, http_auth=None, http_headers=None, **kwargs):
        arg_reasons = {}
        call_kwargs = OrderedDict()

        # Validate arguments using the SCPD stateVariable definitions
        for name, statevar in self.argsdef_in:
            if name not in kwargs:
                raise UPNPError('Missing required param \'%s\'' % (name))
            valid, reasons = self.validate_arg(kwargs[name], statevar)
            if not valid:
                arg_reasons[name] = reasons
            # Preserve the order of call args, as listed in SCPD XML spec
            call_kwargs[name] = kwargs[name]

        if arg_reasons:
            raise ValidationError(arg_reasons)

        # Make the actual call
        self._log.debug(">> %s (%s)", self.name, call_kwargs)
        soap_client = SOAP(self.url, self.service_type)

        soap_response = soap_client.call(
          self.name,
          call_kwargs,
          http_auth or self.service.device.http_auth,
          http_headers or self.service.device.http_headers
        )
        self._log.debug("<< %s (%s): %s", self.name, call_kwargs, soap_response)

        # Marshall the response to python data types
        out = {}
        for name, statevar in self.argsdef_out:
            __, value = marshal_value(statevar['datatype'], soap_response[name])
            out[name] = value

        return out

    @staticmethod
    def validate_arg(arg, argdef):
        """
        Validate an incoming (unicode) string argument according the UPnP spec. Raises UPNPError.
        """
        datatype = argdef['datatype']
        reasons = set()
        ranges = {
            'ui1': (int, 0, 255),
            'ui2': (int, 0, 65535),
            'ui4': (int, 0, 4294967295),
            'i1': (int, -128, 127),
            'i2': (int, -32768, 32767),
            'i4': (int, -2147483648, 2147483647),
            'r4': (Decimal, Decimal('3.40282347E+38'), Decimal('1.17549435E-38'))
        }
        try:
            if datatype in set(ranges.keys()):
                v_type, v_min, v_max = ranges[datatype]
                if not v_min <= v_type(arg) <= v_max:
                    reasons.add('%r datatype must be a number in the range %s to %s' % (
                        datatype, v_min, v_max))

            elif datatype in {'r8', 'number', 'float', 'fixed.14.4'}:
                v = Decimal(arg)
                if v < 0:
                    assert Decimal('-1.79769313486232E308') <= v <= Decimal('4.94065645841247E-324')
                else:
                    assert Decimal('4.94065645841247E-324') <= v <= Decimal('1.79769313486232E308')

            elif datatype == 'char':
                v = arg.decode('utf8') if isinstance(arg, bytes) else arg
                assert len(v) == 1

            elif datatype == 'string':
                v = arg.decode("utf8") if isinstance(arg, bytes) else arg
                if argdef['allowed_values'] and v not in argdef['allowed_values']:
                    reasons.add('Value %r not in allowed values list' % arg)

            elif datatype == 'date':
                v = parse_date(arg)
                if any((v.hour, v.minute, v.second)):
                    reasons.add("'date' datatype must not contain a time")

            elif datatype in ('dateTime', 'dateTime.tz'):
                v = parse_date(arg)
                if datatype == 'dateTime' and v.tzinfo is not None:
                    reasons.add("'dateTime' datatype must not contain a timezone")

            elif datatype in ('time', 'time.tz'):
                now = datetime.datetime.utcnow()
                v = parse_date(arg, default=now)
                if v.tzinfo is not None:
                    now += v.utcoffset()
                if not all((
                        v.day == now.day,
                        v.month == now.month,
                        v.year == now.year)):
                    reasons.add('%r datatype must not contain a date' % datatype)
                if datatype == 'time' and v.tzinfo is not None:
                    reasons.add('%r datatype must not have timezone information' % datatype)

            elif datatype == 'boolean':
                valid = {'true', 'yes', '1', 'false', 'no', '0'}
                if arg.lower() not in valid:
                    reasons.add('%r datatype must be one of %s' % (datatype, ','.join(valid)))

            elif datatype == 'bin.base64':
                b64decode(arg)

            elif datatype == 'bin.hex':
                unhexlify(arg)

            elif datatype == 'uri':
                urlparse(arg)

            elif datatype == 'uuid':
                if not re.match(
                        r'^[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}$',
                        arg, re.I):
                    reasons.add('%r datatype must contain a valid UUID')

            else:
                reasons.add("%r datatype is unrecognised." % datatype)

        except ValueError as exc:
            reasons.add(str(exc))

        return not bool(len(reasons)), reasons
