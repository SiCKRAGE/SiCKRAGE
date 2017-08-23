from __future__ import absolute_import, division, print_function

from datetime import datetime

import requests
from trakt.core.helpers import popitems
from trakt.interfaces.base import Interface, authenticated
from trakt.mapper.summary import SummaryMapper


class Base(Interface):
    def new(self, media, **kwargs):
        if media != 'shows':
            raise ValueError("Media '%s' does not support the `new()` method" % (media,))

        return self.get(media, 'new', **kwargs)

    def premieres(self, media, **kwargs):
        if media != 'shows':
            raise ValueError("Media '%s' does not support the `premieres()` method" % (media,))

        return self.get(media, 'premieres', **kwargs)

    def get(self, source, media, collection=None, start_date=None, days=None, query=None, years=None, genres=None,
            languages=None, countries=None, runtimes=None, ratings=None, certifications=None, networks=None,
            status=None, **kwargs):
        """Retrieve calendar items.

        The `all` calendar displays info for all shows airing during the specified period. The `my` calendar displays
        episodes for all shows that have been watched, collected, or watchlisted.

        :param source: Calendar source (`all` or `my`)
        :type source: str

        :param media: Media type (`dvd`, `movies` or `shows`)
        :type media: str

        :param collection: Collection type (`new`, `premieres`)
        :type collection: str or None

        :param start_date: Start date (defaults to today)
        :type start_date: datetime or None

        :param days: Number of days to display (defaults to `7`)
        :type days: int or None

        :param query: Search title or description.
        :type query: str or None

        :param years: Year or range of years (e.g. `2014`, or `2014-2016`)
        :type years: int or str or tuple or None

        :param genres: Genre slugs (e.g. `action`)
        :type genres: str or list of str or None

        :param languages: Language codes (e.g. `en`)
        :type languages: str or list of str or None

        :param countries: Country codes (e.g. `us`)
        :type countries: str or list of str or None

        :param runtimes: Runtime range in minutes (e.g. `30-90`)
        :type runtimes: str or tuple or None

        :param ratings: Rating range between `0` and `100` (e.g. `75-100`)
        :type ratings: str or tuple or None

        :param certifications: US Content Certification (e.g. `pg-13`, `tv-pg`)
        :type certifications: str or list of str or None

        :param networks: (TV) Network name (e.g. `HBO`)
        :type networks: str or list of str or None

        :param status: (TV) Show status (e.g. `returning series`, `in production`, ended`)
        :type status: str or list of str or None

        :return: Items
        :rtype: list of trakt.objects.video.Video
        """
        if source not in ['all', 'my']:
            raise ValueError('Unknown collection type: %s' % (source,))

        if media not in ['dvd', 'movies', 'shows']:
            raise ValueError('Unknown media type: %s' % (media,))

        # Default `start_date` to today when only `days` is provided
        if start_date is None and days:
            start_date = datetime.utcnow()

        # Request calendar collection
        response = self.http.get(
            '/calendars/%s/%s%s' % (
                source, media,
                ('/' + collection) if collection else ''
            ),
            params=[
                start_date.strftime('%Y-%m-%d') if start_date else None,
                days
            ],
            query={
                'query': query,
                'years': years,
                'genres': genres,

                'languages': languages,
                'countries': countries,
                'runtimes': runtimes,

                'ratings': ratings,
                'certifications': certifications,

                # TV
                'networks': networks,
                'status': status
            },
            **popitems(kwargs, [
                'authenticated',
                'validate_token'
            ])
        )

        # Parse response
        items = self.get_data(response, **kwargs)

        if isinstance(items, requests.Response):
            return items

        # Map items
        if media == 'shows':
            return SummaryMapper.episodes(
                self.client, items,
                parse_show=True
            )

        return SummaryMapper.movies(self.client, items)


class AllCalendarsInterface(Base):
    path = 'calendars/all/*'

    def get(self, media, collection=None, start_date=None, days=None, **kwargs):
        return super(AllCalendarsInterface, self).get(
            'all', media, collection,
            start_date=start_date,
            days=days,
            **kwargs
        )


class MyCalendarsInterface(Base):
    path = 'calendars/my/*'

    @authenticated
    def get(self, media, collection=None, start_date=None, days=None, **kwargs):
        return super(MyCalendarsInterface, self).get(
            'my', media, collection,
            start_date=start_date,
            days=days,
            **kwargs
        )
