<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

____

#  (2020-04-19)



---

## Bug Fixes

- Fixed #SICKRAGE-APP-46H - Refactored IMDb ID regex
  ([327b5a30](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/327b5a306cd7b4154654fb08685bc9359cc8bc59))
- Fixed #SICKRAGE-APP-46K - `list index out of range` when getting episode info from TheTVDB in another language
  ([4b9115bd](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/4b9115bdc9b5693244132d366b2f6c195f72b2da))
- Fixed #SICKRAGE-APP-46R - `can't compare datetime.datetime to datetime.date` error when trying to display show
  ([2cfc7bfc](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/2cfc7bfcc8167ee0cc292a73526f917c26042406))
- Fixed #SICKRAGE-APP-46N - `Failed parsing provider` for immortalseed provider if tooltip is not found.
  ([8287af20](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/8287af202f6c720f45c1f8c79fe0d34c05db3eea))
- Fixed `'NoneType' object has no attribute 'get'` when attempting to decrypt legacy config encryption
  ([f21457c4](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/f21457c4187947aaac2b03a1745501d5cbee2338))
- Fixed `Unknown format code 'd' for object of type 'str'`
  ([2eac3920](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/2eac39209671a37e47f83957184719cfa9ff8974))
- Fixed KeyError when trying to get torrent size attribute for Nyaa provider
  ([4619f99d](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/4619f99dc4635973f15b1860e0df1eabdc506ab4))
- Fixed URL regex for rTorrent search client
  ([7b8c2c15](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/7b8c2c15b985f66099429d003b8862f3d0fbf6fe))


## Refactor

- Refactored npx command for generating changelog
  ([877f7f57](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/877f7f57bbc3169f2217431487a67beb911a460b))
- Refactored changelog creation
  ([022e36d3](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/022e36d344ef0f0706acd7b363db1c634107a583))
- Refactored ErrorViewer and WarningViewer classes to use collections deque with a max size of 100 to prevent memory errors.
  ([ec25dfed](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/ec25dfed73b8115375529793bd590f181d7c6b05))
- Refactored TVShow class episode cache to set() from list()
  ([41298595](https://gitlab-ci-token:fWGEkgJsFmsLWRRykMqw@git.sickrage.ca/SiCKRAGE/sickrage/commit/41298595afe35078563f198ea50739ace26c79ff))



---
<sub><sup>*Generated with [git-changelog](https://github.com/rafinskipg/git-changelog). If you have any problems or suggestions, create an issue.* :) **Thanks** </sub></sup>