from lib.tvdb_api.tvdb_api import Tvdb
from lib.tvrage_api.tvrage_api import TVRage
from lib.anidb_api.anidb_api import AniDB

INDEXER_TVDB = 1
INDEXER_TVRAGE = 2
INDEXER_ANIDB = 3

initConfig = {}
indexerConfig = {}

initConfig['valid_languages'] = [
    "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
    "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"]

initConfig['langabbv_to_id'] = {
    'el': 20, 'en': 7, 'zh': 27,
    'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
    'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
    'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}

indexerConfig[INDEXER_TVDB] = {
    'id': INDEXER_TVDB,
    'name': 'theTVDB',
    'module': Tvdb,
    'api_params': {'apikey': '9DAF49C96CBF8DAC',
                   'language': 'en',
                   'useZip': True
    },
}

indexerConfig[INDEXER_TVRAGE] = {
    'id': INDEXER_TVRAGE,
    'name': 'TVRage',
    'module': TVRage,
    'api_params': {'apikey': 'Uhewg1Rr0o62fvZvUIZt',
                   'language': 'en'
    },
}

indexerConfig[INDEXER_ANIDB] = {
    'id': INDEXER_ANIDB,
    'name': 'AniDB',
    'module': AniDB,
    'api_params': {'apikey': '',
                   'language': 'en'
    },
    }

# TVDB Indexer Settings
indexerConfig[INDEXER_TVDB]['xem_origin'] = 'tvdb'
indexerConfig[INDEXER_TVDB]['icon'] = 'thetvdb16.png'
indexerConfig[INDEXER_TVDB]['scene_url'] = 'http://midgetspy.github.com/sb_tvdb_scene_exceptions/exceptions.txt'
indexerConfig[INDEXER_TVDB]['show_url'] = 'http://thetvdb.com/?tab=series&id='
indexerConfig[INDEXER_TVDB]['base_url'] = 'http://thetvdb.com/api/%(apikey)s/series/' % indexerConfig[INDEXER_TVDB]['api_params']

# TVRAGE Indexer Settings
indexerConfig[INDEXER_TVRAGE]['xem_origin'] = 'rage'
indexerConfig[INDEXER_TVRAGE]['icon'] = 'tvrage16.png'
indexerConfig[INDEXER_TVRAGE]['scene_url'] = 'http://raw.github.com/echel0n/sb_tvrage_scene_exceptions/master/exceptions.txt'
indexerConfig[INDEXER_TVRAGE]['show_url'] = 'http://tvrage.com/shows/id-'
indexerConfig[INDEXER_TVRAGE]['base_url'] = 'http://tvrage.com/showinfo.php?key=%(apikey)s&sid=' % indexerConfig[INDEXER_TVRAGE]['api_params']

# ANIDB Indexer Settings
indexerConfig[INDEXER_ANIDB]['xem_origin'] = 'anidb'
indexerConfig[INDEXER_ANIDB]['icon'] = 'anidb16.png'
indexerConfig[INDEXER_ANIDB]['scene_url'] = 'http://raw.github.com/Ether009/sb_anidb_scene_exceptions/master/exceptions.txt'
indexerConfig[INDEXER_ANIDB]['show_url'] = 'http://anidb.net/perl-bin/animedb.pl?show=anime&aid='
indexerConfig[INDEXER_ANIDB]['base_url'] = 'http://api.anidb.net:9001/httpapi?client=sickrage&clientver=1&protover=1&request=anime&aid='