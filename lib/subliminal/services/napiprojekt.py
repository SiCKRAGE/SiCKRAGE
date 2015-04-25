# -*- coding: utf-8 -*-
# Copyright 2011-2012 Antoine Bertin <diaoulael@gmail.com>
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
from . import ServiceBase
from ..language import language_set, Language
from ..subtitles import get_subtitle_path, ResultSubtitle
from ..videos import Episode, Movie, UnknownVideo
from ..exceptions import DownloadFailedError, ServiceError
import logging
import os
import sys
import tempfile
import codecs
import subprocess

logger = logging.getLogger("subliminal")

class NapiProjekt(ServiceBase):

    napi_lang_map = { 'pl': ('PL'), 'pol': ('PL'), 'en': ('ENG'), 'eng': ('ENG') }
    languages     = language_set(['en', 'pl'])
    require_video = True
    api_based     = True
    videos        = [Movie, Episode, UnknownVideo]
    server_url    = 'http://napiprojekt.pl/unit_napisy/dl.php'
    site_url      = 'http://www.napiprojekt.pl/'
    password      = 'iBlm8NTigvru0Jr0'
    data          = {}

    def list_checked(self, video, languages):
        return self.query(video.path, video.hashes['NapiProjekt'], languages)

    def query(self, filepath, moviehash, languages):
	
	available_languages = language_set()
        #langs = filter(lambda x: x in languages, languages)
	
	for language in languages:
	    payload = {
                "l": self.napi_lang_map[self.get_code(language)],
                "f": moviehash,
                "t": self._f(moviehash),
                "v": "other",
                "kolejka": "false",
                "nick": "",
                "pass": "",
                "napios": os.name
            }

            r = self.session.get(self.server_url, params=payload)

            if r.text.startswith('NPc'):
                logger.info(u'Could not find subtitles for hash %s' % moviehash) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
                return []
            if r.status_code != 200:
                logger.error(u'Request %s returned status code %d' % (r.url, r.status_code)) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
                return []
            
            available_languages.add(language)
	    self.data[language] = r.content

		
        languages &= available_languages

        if not languages:
            logger.debug(u'Could not find subtitles for hash %s with languages %r (only %r available)' % 
                (moviehash, languages, available_languages)) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
            return []

        subtitles = []
        for language in languages:
            path = get_subtitle_path(filepath, language, self.config.multi)
            subtitle = ResultSubtitle(path, language, self.__class__.__name__.lower(), 
		'%s?action=download&hash=%s&language=%s' % (self.server_url, moviehash, language))
            subtitles.append(subtitle)

	    logger.info('NapiProjekt downloaded %s subtitles for %s' % (language, path)) \
		if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')

        return subtitles


    def download(self, subtitle):
        try:
            self.data[subtitle.language] = self._decompress(self.data[subtitle.language])

            logger.info('Writing file %s', subtitle.path) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
            fp = codecs.open(subtitle.path,'wb')
            fp.write(self.data[subtitle.language])
            fp.close()

        except Exception as e:
            if os.path.exists(subtitle.path):
                os.remove(subtitle.path)
	    logger.error('Exception while decompressing -> %s' % str(e)) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
            raise DownloadFailedError(str(e))

        return subtitle


    def _decompress(self, data):
        """
        Decompresses download data (napiprojekt uses 7Zip compression)
        """
        fp  = tempfile.NamedTemporaryFile('wb', suffix=".7z")
        tfp = fp.name
        fp.write(data)
        fp.flush()

        try:
            cmd = ['/usr/bin/7z', 'x', '-y', '-so', '-p' + self.password, tfp]
            sa = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            (so, se) = sa.communicate(data)
            retcode  = sa.returncode
            fp.close()
            logger.debug('Executing cmd %s', ' '.join(cmd)) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
            logger.debug('Decompressed subtitles') if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
	    return so

        except OSError, e:
            fp.close()
            msg = 'Skipping, subtitle decompression failed: %s' % (e)
            logger.warning(msg) if sys.platform != 'win32' else logger.debug('Log line suppressed on windows')
            raise DownloadFailedError(msg)


    def _f(self, z):
        """
        Magic number calculation
        """
        idx = [ 0xe, 0x3,  0x6, 0x8, 0x2 ]
        mul = [   2,   2,    5,   4,   3 ]
        add = [   0, 0xd, 0x10, 0xb, 0x5 ]

        b = []
        for i in xrange(len(idx)):
            a = add[i]
            m = mul[i]
            i = idx[i]

            t = a + int(z[i], 16)
            v = int(z[t:t+2], 16)
            b.append( ("%x" % (v*m))[-1] )

        return ''.join(b)

Service = NapiProjekt
