<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

# 

##Fri Apr 24 2020 15:34:41 GMT+0000 (Coordinated Universal Time)


## Refactor
  - Refactored provider URLs to not be pulled from API, currently the code for this needs to be reworked as its causing performance issues.
  ([73a6fd85](https://gitlab-ci-token:B19KDp47GV5LeFiHeDkP@git.sickrage.ca/SiCKRAGE/sickrage/commit/73a6fd85de971acf0173c1716de370bf74d8c4c7))
  - Refactored scheduled jobs to be async and execute on ioloop in their own thread
  ([64ecdbeb](https://gitlab-ci-token:B19KDp47GV5LeFiHeDkP@git.sickrage.ca/SiCKRAGE/sickrage/commit/64ecdbeb0e988d7a6aae6a17ad539d0a8181cae8))
  - Refactored auto-postprocessing task to be async
  ([f4958915](https://gitlab-ci-token:B19KDp47GV5LeFiHeDkP@git.sickrage.ca/SiCKRAGE/sickrage/commit/f49589158c79cb2ddbc30d7927e07d64dcb21dc4))
  - Refactored name of function in auto_postprocessor.py from run to task
  ([6ef74b10](https://gitlab-ci-token:B19KDp47GV5LeFiHeDkP@git.sickrage.ca/SiCKRAGE/sickrage/commit/6ef74b10569dd25046d57f18827e4a33671b5a80))




