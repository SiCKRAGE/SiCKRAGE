from __future__ import absolute_import, unicode_literals


class Person(object):

    def __init__(self, data):
        # primary attributes that should be set in all cases

        self.name = self._extract_name(data)
        self.imdb_id = self._extract_imdb_id(data)

        # secondary attribs, will only get data when called via get_title_by_id

        # token and label are the persons categorisation
        # e.g token: writers label: Series writing credits
        self.token = data.get('token')
        self.label = data.get('label')
        # attr is a note about this persons work
        # e.g. (1990 - 1992 20 episodes)
        self.attr = data.get('attr')
        # other primary information about their part
        self.roles = (
            data.get('char').split('/') if data.get('char') else []
        )
        self.job = data.get('job')

    @staticmethod
    def _extract_name(data):
        # Person object can given response of get_title_by_id
        # or get_person_by_id call.
        # This function covers the slight data structure differences
        # to extract the name
        name = data.get('name')
        if isinstance(name, dict):
            return name.get('name')
        return name

    @staticmethod
    def _extract_imdb_id(data):
        name = data.get('name')
        if isinstance(name, dict):
            return name.get('nconst')
        return data.get('nconst')

    def __repr__(self):
        return '<Person: {0} ({1})>'.format(repr(self.name),
                                            repr(self.imdb_id))

    def __unicode__(self):
        return '<Person: {0} ({1})>'.format(self.name.encode('utf-8'),
                                            self.imdb_id)


class Title(object):

    def __init__(self, data):
        self.data = data

        self.imdb_id = self.data.get('tconst')
        self.title = self.data.get('title')
        self.type = self.data.get('type')
        self.year = self._extract_year()
        self.tagline = self.data.get('tagline')
        self.plots = self.data.get('plots')
        self.plot_outline = self.data.get('plot', {}).get('outline')
        self.rating = self.data.get('rating')
        self.genres = self.data.get('genres')
        self.votes = self.data.get('num_votes')
        self.runtime = self.data.get('runtime', {}).get('time')
        self.poster_url = self.data.get('image', {}).get('url')
        self.cover_url = self._extract_cover_url()
        self.release_date = self.data.get('release_date', {}).get('normal')
        self.certification = self.data.get('certificate', {}).get(
            'certificate')
        self.trailer_image_urls = self._extract_trailer_image_urls()
        self.directors_summary = self._extract_directors_summary()
        self.creators = self._extract_creators()
        self.cast_summary = self._extract_cast_summary()
        self.writers_summary = self._extract_writers_summary()
        self.credits = self._extract_credits()
        self.trailers = self._extract_trailers()

    def _extract_directors_summary(self):
        return [Person(p) for p in self.data.get('directors_summary', [])]

    def _extract_creators(self):
        return [Person(p) for p in self.data.get('creators', [])]

    def _extract_trailers(self):
        def build_dict(val):
            return {'url': val['url'], 'format': val['format']}

        trailers = self.data.get('trailer', {}).get('encodings', {}).values()
        return [build_dict(trailer) for trailer in trailers]

    def _extract_writers_summary(self):
        return [Person(p) for p in self.data.get('writers_summary', [])]

    def _extract_cast_summary(self):
        return [Person(p) for p in self.data.get('cast_summary', [])]

    def _extract_credits(self):
        credits = []

        if not self.data.get('credits'):
            return []

        for credit_group in self.data['credits']:
            """
            Possible tokens: directors, cast, writers, producers and others
            """
            for person in credit_group['list']:
                person_extra = {
                    'token': credit_group.get('token'),
                    'label': credit_group.get('label'),
                    'job': person.get('job'),
                    'attr': person.get('attr')
                }
                person_data = person.copy()
                person_data.update(person_extra)
                if 'name' in person_data.keys():
                    # some 'special' credits such as script rewrites
                    # have different formatting.
                    # we skip those here, losing some data due to this check
                    credits.append(Person(person_data))
        return credits

    def _extract_year(self):
        year = self.data.get('year')
        # if there's no year the API returns ????...
        if not year or year == '????':
            return None
        return int(year)

    def _extract_cover_url(self):
        if self.poster_url:
            return '{0}_SX214_.jpg'.format(self.poster_url.replace('.jpg', ''))

    def _extract_trailer_image_urls(self):
        slates = self.data.get('trailer', {}).get('slates', [])
        return [s['url'] for s in slates]

    def __repr__(self):
        return '<Title: {0} - {1}>'.format(repr(self.title),
                                           repr(self.imdb_id))

    def __unicode__(self):
        return '<Title: {0} - {1}>'.format(self.title, self.imdb_id)


class Image(object):

    def __init__(self, data):
        self.caption = data.get('caption')
        self.url = data.get('image', {}).get('url')
        self.width = data.get('image', {}).get('width')
        self.height = data.get('image', {}).get('height')

    def __repr__(self):
        return '<Image: {0}>'.format(repr(self.caption))

    def __unicode__(self):
        return '<Image: {0}>'.format(self.caption.encode('utf-8'))


class Review(object):

    def __init__(self, data):
        self.username = data.get('user_name')
        self.text = data.get('text')
        self.date = data.get('date')
        self.rating = data.get('user_rating')
        self.summary = data.get('summary')
        self.status = data.get('status')
        self.user_location = data.get('user_location')
        self.user_score = data.get('user_score')
        self.user_score_count = data.get('user_score_count')

    def __repr__(self):
        return '<Review: {0}>'.format(repr(self.text[:20]))

    def __unicode__(self):
        return '<Review: {0}>'.format(self.text[:20].encode('utf-8'))
