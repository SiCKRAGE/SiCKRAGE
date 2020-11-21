SiCKRAGE
=====
Automatic Video Library Manager for TV Shows.
It watches for new episodes of your favorite shows, and when they are posted it does its magic.

#### Features
 - Kodi/XBMC library updates, poster/banner/fanart downloads, and NFO/TBN generation
 - Configurable automatic episode renaming, sorting, and other processing
 - Easily see what episodes you're missing, are airing soon, and more
 - Automatic torrent/nzb searching, downloading, and processing at the qualities you want
 - Largest list of supported torrent and nzb providers, both public and private
 - Can notify Kodi, XBMC, Growl, Trakt, Twitter, and more when new episodes are available
 - Searches TheTVDB.com and AniDB.net for shows, seasons, episodes, and metadata
 - Episode status management allows for mass failing seasons/episodes to force retrying
 - DVD Order numbering for returning the results in DVD order instead of Air-By-Date order
 - Allows you to choose which series provider to have SiCKRAGE search its show info from when importing
 - Automatic XEM Scene Numbering/Naming for seasons/episodes
 - Available for any platform, uses a simple HTTP interface
 - Specials and multi-episode torrent/nzb support
 - Automatic subtitles matching and downloading
 - Improved failed download handling
 - DupeKey/DupeScore for NZBGet 12+
 - Real SSL certificate validation
 - Supports Anime shows

#### Installation
$ pip install sickrage
$ sickrage

#### Important
Before using this with your existing database (sickrage.db or sickbeard.db) please make a backup copy of it and delete
any other database files such as cache.db and failed.db if present.

We HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own
risk.