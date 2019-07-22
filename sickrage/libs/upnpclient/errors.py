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



class UPnPErrorCodeDescriptions(object):
    _descriptions = {
        401: 'No action by that name at this service.',
        402: ('Could be any of the following: not enough in args, args in the wrong order, one or m'
              'ore in args are of the wrong data type.'),
        403: '(Deprecated - no not use)',
        501: 'MAY be returned if current state of service prevents invoking that action.',
        600: 'The argument value is invalid',
        601: ('An argument value is less than the minimum or more than the maximum value of the all'
              'owed value range, or is not in the allowed value list.'),
        602: 'The requested action is optional and is not implemented by the device.',
        603: ('The device does not have sufficient memory available to complete the action. This MA'
              'Y be a temporary condition; the control point MAY choose to retry the unmodified req'
              'uest again later and it MAY succeed if memory is available.'),
        604: ('The device has encountered an error condition which it cannot resolve itself and req'
              'uired human intervention such as a reset or power cycle. See the device display or d'
              'ocumentation for further guidance.'),
        605: 'A string argument is too long for the device to handle properly.'
    }

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise KeyError("'key' must be an integer")
        if 606 <= key <= 612:
            return 'These ErrorCodes are reserved for UPnP DeviceSecurity.'
        elif 613 <= key <= 699:
            return 'Common action errors. Defined by UPnP Forum Technical Committee.'
        elif 700 <= key <= 799:
            return 'Action-specific errors defined by UPnP Forum working committee.'
        elif 800 <= key <= 899:
            return 'Action-specific errors for non-standard actions. Defined by UPnP vendor.'
        return self._descriptions[key]


ERR_CODE_DESCRIPTIONS = UPnPErrorCodeDescriptions()
