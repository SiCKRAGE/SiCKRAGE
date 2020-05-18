<img width="300px" src="https://sickrage.ca/img/logo-stacked.png" />

# 

##Mon May 18 2020 03:53:20 GMT+0000 (Coordinated Universal Time)


## Bug Fixes
  - Fixed typo that was preventing scene exception lookups
  ([5104e138](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/5104e1382c4e6bf59c9786786ba4b7345ff8fd5b))
  - Fixed issue with repeating debug message for whitelisted helper function
  ([484919d7](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/484919d7efe8288fa7f7f891761a93f05d19dca6))
  - Fixed issue with unregistering app_id when app_id is not set
  ([7a4d36b0](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/7a4d36b0f29850711b88ff72befa5d36cb720294))
  - Fixed issue with enabling sickrage api when auth token exists
  ([5a828937](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/5a828937d7bcbeb98ef42fabd4926bcce008e78a))
  - Fixed `Unsupported header value None` when attempting to link sickrage account to sickrage api
  ([4e9d3435](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/4e9d3435d14257151bce3287b4f25641a0d6a848))
  - Fixed issue with app_id being set to None due to SR API failing to return a proper app_id
  ([01f958bd](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/01f958bd79d82e703806dd990746c25d9ccdfcbd))
  - Fixed issue #SICKRAGE-APP-4Y9 - AttributeError for sickrage.core.helpers in is_ip_whitelisted
  ([5542818f](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/5542818fda25777e0ad41b1c5dcdd5ca9e6acf96))
  - Fixed issue with adding shows off IMDb
  ([617e12d1](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/617e12d17c17ab0287043277d808185fab3dcb91))
  - Fixed issue with linking/unlinking sickrage account to sickrage api
  ([f62ed722](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/f62ed7227db3bf5673e4856e0280a8b93154aaf1))
  - Fixed issue with improper quoted url strings when using TheTVDB API
  ([c7640dc1](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/c7640dc1cdf396010f4c5c988a5b25c4104e2c2d))
  - Fixed issue #486 - scene_default reference removed from add existing shows code, added search_format_default to be passed when adding existing shows
  ([9b9e717e](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/9b9e717ec4d45a62bfdb9a16cf781ac204a10b71))
  - Fixed issue with passing web root to Docker
  ([57444d96](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/57444d96d9ae32b58fad872f2cb7dc6e0e72ad1c))
  - Fixed #484 - Mass Update Error caused by incorrectly handling show search formats as a checkbox value when it should be a integer
  ([54b25045](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/54b25045e0231c300c3881fcc5f8053ca300af63))




## Refactor
  - Refactored ip whitelist helper and subnet checking
  ([741587fb](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/741587fb1c4bd7087afdf9c5ad76486e738e6aac))
  - Refactored ip whitelist helper
  ([b29f00bc](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/b29f00bcff0c3323f83af3affc9d492a02da16bf))
  - Refactored ip whitelist helper
  ([1a871175](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/1a8711755744893e4b7c61afe8c2c53f7a2c19ae))
  - Refactored check to see if sickrage account is linked to sickrage api
  ([458b9f80](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/458b9f8019829aa4d7fad9b8d3d05891a27b126f))
  - Refactored sickrage account <> sickrage api handler to logout existing auth tokens before creating new ones
  ([939eeb16](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/939eeb16f620bf11e7eaa879ee17112300459afc))
  - Refactored health check for sickrage auth server to GET method
  ([bdcf70b9](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/bdcf70b99705b4af9dc9ce6964d4aba99f18d126))
  - Refactored polling health of sickrage auth server to use HEAD method instead of GET method
  ([b2803862](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/b2803862f0ce2c36e165bd944cd52834b3a742ab))
  - Refactored popup window only for when enabling sickrage api and not when disabling it
  ([90ea9457](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/90ea9457e7444706d5958a52f8fdcb0afd1cccfc))
  - Refactored link/unlink sickrage account to sickrage api button to hide/show based on sickrage api enable/disable toggle
  ([5cc3a689](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/5cc3a68987096468deadfeb9912171812b963c40))
  - Refactored SiCKRAGE API status code 204 to return `True` if response is OK Refactored SiCKRAGE account to unlink from SiCKRAGE API only if response returned after attempting to unregister app ID is good
  ([279d4957](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/279d4957548fc25546ed2940d62166cb2716945e))
  - Refactored web username and password to be required to save settings when enabling local auth
  ([2275ec6e](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/2275ec6e49af3442952eaab08725ded67e446f76))
  - Refactored SiCKRAGE authorization client interface Feature added to allow opt-out of SSO auth logins Feature added to allow opt-out of SiCKRAGE API services Feature added to allow local auth logins Feature added to allow whitelisting of IP addresses or subnets to bypass auth logins Fixed issue with passing host as startup params Fixed issue with `check_setting_bool` always returning default values
  ([8ba400d9](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/8ba400d9b24d20545d503d633ed57f03cdff9ba6))
  - Refactored SiCKRAGE authorization client interface Feature added to allow opt-out of SSO auth logins Feature added to allow opt-out of SiCKRAGE API services Feature added to allow local auth logins Feature added to allow whitelisting of IP addresses or subnets to bypass auth logins Fixed issue with passing host as startup params Fixed issue with `check_setting_bool` always returning default values
  ([0d488348](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/0d488348d2164b0a415a9fd3f6c061ace7902585))
  - Refactored how TheTVDB api handles exceptions and how those are passed on and handled inside SR core
  ([9fb3962b](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/9fb3962bcd3a4cf01e713689d49128500c06f861))




## Branchs merged
  - Merge branch 'feature-local-auth' into develop
  ([62798f41](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/62798f418d253006eb674d3f23fde1c88805610d))
  - Merge branch 'develop' into refactor-thetvdb-api
  ([49aa5e8b](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/49aa5e8b1ecdc99a881ca4b8339533d39c6f942c))
  - Merge branch 'develop' into refactor-thetvdb-api
  ([ddeccf1e](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/ddeccf1e66980ca9546505d50ec0c3440706242e))
  - Merge branch 'develop' into refactor-thetvdb-api
  ([02fbdcd0](https://gitlab-ci-token:ktU9c-5KABSQXYLsVDzF@git.sickrage.ca/SiCKRAGE/sickrage/commit/02fbdcd061339968625eb7b505e1aaafde97c044))




