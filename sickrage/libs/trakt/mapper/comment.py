from __future__ import absolute_import, division, print_function

from trakt.mapper.core.base import Mapper


class CommentMapper(Mapper):
    @classmethod
    def comment(cls, client, item, **kwargs):
        if 'comment' in item:
            i_comment = item['comment']
        else:
            i_comment = item

        # Retrieve item keys
        pk, keys = cls.get_ids('comment', i_comment)

        if pk is None:
            return None

        # Create object
        comment = cls.construct(client, 'comment', i_comment, keys, **kwargs)

        # Update with root info
        if 'comment' in item:
            comment._update(item)

        return comment
