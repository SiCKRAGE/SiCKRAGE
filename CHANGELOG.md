<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

# 

##Thu Apr 23 2020 15:51:04 GMT+0000 (Coordinated Universal Time)


## Bug Fixes
  - Fixed status code comparison logic in SR API client class for handling of http error codes between 500 and 600
  ([2cf0ebdd](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/2cf0ebdd940123eba8db75548e7f0b5d99777d51))




## Features
  - Feature added to view logs in realtime from log view
  ([0865b232](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/0865b2326717524730f3c9ebec145684c019f7b0))




## Refactor
  - Refactored fifo list to collections deque in search queue class Refactored how logs view uses max lines Refactored queue class to fire events using threads instead of ioloop Refactored how scheduler jobs are forced to execute on request
  ([c2378437](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/c2378437376729f0d96accc9ee80d4ec0e659827))
  - Refactored gitlab ci/cd to push only annotated tags with commits
  ([c5737a55](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/c5737a557dab2aadc6843194fefef4d28a397008))
  - Refactored how web session class performs retries on connection errors
  ([c1352ac6](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/c1352ac639de15067e482e141ea07fef367c398f))




## Chore
  - Chore - Upgraded javascript modules for building core web functions
  ([98699252](https://gitlab-ci-token:HAUQB1LVuM6v4dybH-sF@git.sickrage.ca/SiCKRAGE/sickrage/commit/9869925269cf8f09830f89dd4b99e21e02dc40e5))




