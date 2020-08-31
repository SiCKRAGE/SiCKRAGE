<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

# 

##Mon Aug 31 2020 02:07:49 GMT+0000 (Coordinated Universal Time)


## Bug Fixes
  - Fixed issue with scene_season being non-integer Fixed issue #SICKRAGE-APP-5TZ - NoResultFound exception not handled in get_indexer_absolute_numbering function, not returns -1 when exception is thrown Fixed issue #SICKRAGE-APP-5YH - FakeUserAgentError exception not handled when attempting to get a random user agent string for core web sessions, now returns default SR user agent string if exception is thrown Fixed issue #SICKRAGE-APP-5XV - NoneType possibly returned when getting season/episode numbering from episode object due to improper comparison Fixed issue #SICKRAGE-APP-5XE - AttributeError occurrence when trying to split show scene exceptions data by delimiter if previously never set Fixed issue #SICKRAGE-APP-5ZS - TypeError thrown due to episode status being set as a string instead of a integer
  ([eb54e81c](https://gitlab-ci-token:ssLQGoUsHgnafmq5y_tX@git.sickrage.ca/SiCKRAGE/sickrage/commit/eb54e81cd1b2c3c3a715ec9d20ee4d07e50892c7))




