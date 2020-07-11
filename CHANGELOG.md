<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

# 

##Sat Jul 11 2020 18:06:33 GMT+0000 (Coordinated Universal Time)


## Bug Fixes
  - Fixed issue with displaying a show when no imdb info is available
  ([c8a763bf](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/c8a763bfa2b6f0e2431ccdec488d95a2709ee52d))
  - Fixed multi-thread issue with quicksearch
  ([148e0671](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/148e0671a11a7b422155bbfa924d939eb25779ca))
  - Fixed multi-thread issue with quicksearch
  ([a34c39d3](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/a34c39d3eff469e3b29ed0a868c368f305ca523d))
  - Fixed error message from hachoir package on import
  ([b8c55a64](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/b8c55a645136b2cd295d770364ccb637a313598c))
  - Fixed error handling for when a queued task fails
  ([9a9019cd](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/9a9019cd50e8a76a5553e76b5b9a867dcceb3141))
  - Fixed issue with post-processing
  ([8758c4a4](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/8758c4a4cb150c2b53255f4956bfd8e52caef3fb))
  - Fixed shutdown sequence
  ([016f7e88](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/016f7e883558f3e259aa3f0e8ba45f9e932e03a0))
  - Fixed passing of args to thread when creating thread for queue class task
  ([5ff5b1e9](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/5ff5b1e91686fac3c3b5402ad2b1bd4af62710af))
  - Fixed missing start of thread for queue class
  ([4350619c](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/4350619c6e64a56a8a6596cf910791b8215b6af5))




## Refactor
  - Refactored queue system and how it handles tasks
  ([4c39a2d4](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/4c39a2d4baa6cf2577e9c1387f87ee182d9661b0))
  - Refactored queue system shutdown method
  ([fe042f9b](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/fe042f9b11272ddfb39879b0a59de59503bed3d8))
  - Refactored queue system to process one queue item at a time
  ([2a47a795](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/2a47a795a371afb3b120b20fcfa74645086b1cc3))
  - Refactored queue system to use while loop instead of apscheduler
  ([31733525](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/31733525322481ef3dd04adae0566e1e0cb6511b))
  - Refactored queue system to use BackgroundScheduler instead of TornadoScheduler
  ([e1f23941](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/e1f2394179df337bd3d341df5c988581825c5707))
  - Refactored web server to run on a separate thread instead of the main thread Refactored queue system to use built-in queue classes instead of Tornado's queue classes
  ([502207ad](https://gitlab-ci-token:xCv1bVfgdaxaqrYgzM3v@git.sickrage.ca/SiCKRAGE/sickrage/commit/502207ad80a332f7a98aef894c91c40b924239d6))




