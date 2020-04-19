<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

____

#  (2020-04-19)



---

## Bug Fixes

- Fixed path to requirements for startup install of missing modules
  ([09556122](https://gitlab-ci-token:JnvLmknny6KXsWGX7kLx@git.sickrage.ca/SiCKRAGE/sickrage/commit/09556122f82ebce44adcfbd4b2e6b1e83ed40b67))


## Refactor

- Refactored requirements install cmd to include `--no-cache-dir` flag when ModuleNotFound exception is thrown
  ([96e2baa0](https://gitlab-ci-token:JnvLmknny6KXsWGX7kLx@git.sickrage.ca/SiCKRAGE/sickrage/commit/96e2baa026f1db19d761e2b1de8bdd1e7c7cfb04))
- Refactored application startup to install requirements via pip if ModuleNotFound exception is thrown.
  ([3bddcc22](https://gitlab-ci-token:JnvLmknny6KXsWGX7kLx@git.sickrage.ca/SiCKRAGE/sickrage/commit/3bddcc22384ec23e3b22e4711af73a85c2adf440))



---
<sub><sup>*Generated with [git-changelog](https://github.com/rafinskipg/git-changelog). If you have any problems or suggestions, create an issue.* :) **Thanks** </sub></sup>