from __future__ import absolute_import, division, print_function

from trakt.mapper.core.base import Mapper


class ListMapper(Mapper):
    @classmethod
    def custom_list(cls, client, item, **kwargs):
        if 'list' in item:
            i_list = item['list']
        else:
            i_list = item

        # Retrieve item keys
        pk, keys = cls.get_ids('custom_list', i_list)

        if pk is None:
            return None

        # Create object
        custom_list = cls.construct(client, 'custom_list', i_list, keys, **kwargs)

        # Update with root info
        if 'list' in item:
            custom_list._update(item)

        return custom_list
