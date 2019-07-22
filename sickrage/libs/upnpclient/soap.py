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



import re

import requests
from lxml import etree

from .util import _getLogger

SOAP_TIMEOUT = 30
NS_SOAP_ENV = 'http://schemas.xmlsoap.org/soap/envelope/'
NS_UPNP_ERR = 'urn:schemas-upnp-org:control-1-0'
ENCODING_STYLE = 'http://schemas.xmlsoap.org/soap/encoding/'
ENCODING = 'utf-8'


class SOAPError(Exception):
    pass


class SOAPProtocolError(Exception):
    pass


class SOAP(object):
    """SOAP (Simple Object Access Protocol) implementation
    This class defines a simple SOAP client.
    """
    def __init__(self, url, service_type):
        self.url = url
        self.service_type = service_type
        # FIXME: Use urlparse for this:
        self._host = self.url.split('//', 1)[1].split('/', 1)[0]  # Get hostname portion of url
        self._log = _getLogger('SOAP')

    def _extract_upnperror(self, err_xml):
        """
        Extract the error code and error description from an error returned by the device.
        """
        nsmap = {'s': list(err_xml.nsmap.values())[0]}
        fault_str = err_xml.findtext(
            's:Body/s:Fault/faultstring', namespaces=nsmap)
        try:
            err = err_xml.xpath(
                's:Body/s:Fault/detail/*[name()="%s"]' % fault_str, namespaces=nsmap)[0]
        except IndexError:
            msg = 'Tag with name of %r was not found in the error response.' % fault_str
            self._log.debug(
                msg + '\n' + etree.tostring(err_xml, pretty_print=True).decode('utf8'))
            raise SOAPProtocolError(msg)

        err_code = err.findtext('errorCode', namespaces=err.nsmap)
        err_desc = err.findtext('errorDescription', namespaces=err.nsmap)

        if err_code is None or err_desc is None:
            msg = 'Tags errorCode or errorDescription were not found in the error response.'
            self._log.debug(
                msg + '\n' + etree.tostring(err_xml, pretty_print=True).decode('utf8'))
            raise SOAPProtocolError(msg)
        return int(err_code), err_desc

    @staticmethod
    def _remove_extraneous_xml_declarations(xml_str):
        """
        Sometimes devices return XML with more than one XML declaration in, such as when returning
        their own XML config files. This removes the extra ones and preserves the first one.
        """
        xml_declaration = ''
        if xml_str.startswith('<?xml'):
            xml_declaration, xml_str = xml_str.split('?>', maxsplit=1)
            xml_declaration += '?>'
        xml_str = re.sub(r'<\?xml.*?\?>', '', xml_str, flags=re.I)
        return xml_declaration + xml_str

    def call(self, action_name, arg_in=None, http_auth=None, http_headers=None):
        """
        Construct the XML and make the call to the device. Parse the response values into a dict.
        """
        if arg_in is None:
            arg_in = {}

        soap_env = '{%s}' % NS_SOAP_ENV
        m = '{%s}' % self.service_type

        root = etree.Element(soap_env+'Envelope', nsmap={'SOAP-ENV': NS_SOAP_ENV})
        root.attrib[soap_env+'encodingStyle'] = ENCODING_STYLE
        body = etree.SubElement(root, soap_env+'Body')
        action = etree.SubElement(body, m+action_name, nsmap={'m': self.service_type})
        for key, value in arg_in.items():
            etree.SubElement(action, key).text = str(value)
        body = etree.tostring(root, encoding=ENCODING, xml_declaration=True)
        headers = {
            'SOAPAction': '"%s#%s"' % (self.service_type, action_name),
            'Host': self._host,
            'Content-Type': 'text/xml',
            'Content-Length': str(len(body)),
        }
        headers.update(http_headers or {})

        try:
            resp = requests.post(
                self.url,
                body,
                headers=headers,
                timeout=SOAP_TIMEOUT,
                auth=http_auth
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            # If the body of the error response contains XML then it should be a UPnP error,
            # otherwise reraise the HTTPError.
            try:
                err_xml = etree.fromstring(exc.response.content)
            except etree.XMLSyntaxError:
                raise exc
            raise SOAPError(*self._extract_upnperror(err_xml))

        xml_str = resp.content.strip()
        try:
            xml = etree.fromstring(xml_str)
        except etree.XMLSyntaxError:
            # Try removing any extra XML declarations in case there are more than one.
            # This sometimes happens when a device sends its own XML config files.
            xml = etree.fromstring(self._remove_extraneous_xml_declarations(xml_str))
        except ValueError:
            # This can occur when requests returns a `str` (unicode) but there's also an XML
            # declaration, which lxml doesn't like.
            xml = etree.fromstring(xml_str.encode('utf8'))

        response = xml.find(".//{%s}%sResponse" % (self.service_type, action_name))
        if response is None:
            msg = ('Returned XML did not include an element which matches namespace %r and tag name'
                   ' \'%sResponse\'.' % (self.service_type, action_name))
            self._log.debug(msg + '\n' + etree.tostring(xml, pretty_print=True).decode('utf8'))
            raise SOAPProtocolError(msg)

        # Sometimes devices return XML strings as their argument values without escaping them with
        # CDATA. This checks to see if the argument has been parsed as XML and un-parses it if so.
        ret = {}
        for arg in response.getchildren():
            children = arg.getchildren()
            if children:
                ret[arg.tag] = b"\n".join(etree.tostring(x) for x in children)
            else:
                ret[arg.tag] = arg.text

        return ret
