# Changelog

## sentry-cli 1.49.0

* Detect Heroku's `SOURCE_VERSION` environment variable (#613)
* Allow extensions with dots for sourcemap uploads (#605)
* Fix validation of `releases set-commits` options in JS (#618)
* Add an optional column for project slugs in `releases list` (#612)
* Add an optional `--wait` flag for upload-dif (#619)

**NOTE**: This release changes the default behavior of `upload-dif`. Previously,
the command waited until Sentry had fully processed uploaded files. Now, the
command terminates after a successful upload but does not wait for server-side
processing. This will speed up uploads for the common case. Specify `--wait` for
the old behavior if you want to make sure that debug files are available before
sending native events.

## sentry-cli 1.48.0

* Add support for Brotli, GZip and Deflate compression algorithms for binary download (#607)
* Fix binary download progress bar calculations (#606)

## sentry-cli 1.47.2

**Changes**:
* Always show the full version in `releases list` (#584).
* Do not warn when using the standard docker entrypoint.

**JavaScript API**:
* Pass the `silent` option to `releases` commands in JavaScript (#552).
* Allow setting commits on a release in JavaScript (#580).

**Fixed bugs**:
* Fix an error in the bash hook if the log file gets deleted (#583).
* Fix detection of Azure repositories in `releases set-commits` (#576).
* Fix detection of annotated tags in `releases set-commits` (#598).
* Fix normalization of sourcemap URL prefixes with trailing slashes (#599).
* Fix upload of source bundles created with `difutil bundle-sources` (#602).

## sentry-cli 1.47.1

* Fix potentially broken payloads in `send-event`.

## sentry-cli 1.47.0

* Trim whitespace in header values to prevent potential header injections
  through the auth token header. (#563)
* Improved Azure DevOps URL parsing. (#556)

## sentry-cli 1.46.0

* Relax the release file limit for sourcemap uploads when artifact bundles
  are supported by the serntry server (#559)

## sentry-cli 1.45.0

* Allow ports in VCS urls when associating commits (#551)
* Support PDB and PE uploads to Sentry (#553)

## sentry-cli 1.44.4

* Emit better version names for react native (#506)
* Fix a regression in sourcemap uploads for certain release names (#549)
* Ensure case insensitive git repository matching (#511)

## sentry-cli 1.44.3

* Fix a regression with URL prefixes in sourcemap uploads (#544)

## sentry-cli 1.44.2

* Even faster sourcemap uploads to sentry.io (#540, #542)

## sentry-cli 1.44.1

* Fixed a segfault in curl on empty file uploading (#535)

## sentry-cli 1.44.0

* Parallelize source map uploads (#533)

## sentry-cli 1.43.0

* Add support for File RAM Bundles (#528)
* Accept more Azure DevOps URLs (#525)

## sentry-cli 1.42.0

* Add support for Indexed RAM Bundles (#523)
* Add "silent" option to JS constructor (#512)

## sentry-cli 1.41.2

* Fix slow unzipping in debug file upload (#519)

## sentry-cli 1.41.1

* Warn before uploading more than 20.000 files to a release (#513)

## sentry-cli 1.41.0

* Recognizes GNU compressed debug files on Linux
* Also uploads Breakpad files and ELF files only containing symbol tables

## sentry-cli 1.40.0

* Automatically retry on various socket and SSL errors (#466, #490)
* Use a connection pool for the outgoing API requests.  This is likely to resolve
  some issues in curl itself that manifested itself as malloc errors on shutdown (#489)
* Upgrade internal dependencies and shrink overall binary (#488)
* Upgrade internal sentry crate

## sentry-cli 1.39.1

* Fix Proguard upload issues on Windows (#484).

## sentry-cli 1.39.0

* Release enabling an internal sentry experiment.

## sentry-cli 1.38.1

* Fix plist parsing

## sentry-cli 1.38.0

* Upgraded symbolic which offers support top R8 code shrinker.

## sentry-cli 1.37.4

* Added `SENTRY_NO_PROGRESS_BAR` environment variable to suppress progress
  bars (#467)
* Fixed an issue where dif uploads would indicate failure if no files where
  to upload.

## sentry-cli 1.37.3

* Report non zero status for server side processing errors on dif upload (#465)
* Improve error messages for 502/504 (#459)
* Relax VCS url comparisions to improve on-prem support

## sentry-cli 1.37.2

* Retry on upload-related operations (chunk-upload, assemble) (#456)
* Add new anylog version (#455)

## sentry-cli 1.37.1

* Fix the detection of debug information in ELF files (#437)
* Add support for ELF files in the `difutil` commands (#447)
* Speed up `sentry-cli update` by using the Sentry release registry (#438)
* Dump http requests in debug mode for better debugging (#448)

## sentry-cli 1.37.0

* Support React Native >= 0.46 (@stephan-nordnes-eriksen, #377)
* Cache binaries to speed up NPM package installation (@timfish, #425)
* Check for successful upload of debug files (#429)
* Limit debug file uploads to 2GB (maximum allowed by Sentry) (#432)

## sentry-cli 1.36.4

* Add support for GitLab in `releases set-commits` (#419)
* Fix a bug where uploaded debug files might show up as _"Generic"_ (#420)

## sentry-cli 1.36.3

* Print out how sentry-cli was invoked in debug log

## sentry-cli 1.36.2

* Download packages from Fastly's CDN when installing via NPM and Brew (#417)
* Allow uploading executables and debug symbols in one go (#412)

## sentry-cli 1.36.1

* Fixes a bug that prevented listing and creating releases

## sentry-cli 1.36.0

* Show project IDs in project listing (#384)
* Fetch all projects, repos and releases if you have more than 100 (#388, #390)
* Support debug symbols with DWARF 5 debug information (#389)
* Fix `--no-environ` parameter in `send-event` (#391)
* Remove a misleading success message in `send-event` (#397)
* Improve debug logs and error output (#393, #394, #399)

## sentry-cli 1.35.6

* Fix a bug introduced with the `--url-suffix` option in `upload-sourcemaps`
* Fix broken commit detection for releases (#378, #381)

## sentry-cli 1.35.5

* Add `--url-suffix` option for `upload-sourcemaps` (#373)

## sentry-cli 1.35.4

* Additional compatibility improvements for the Docker image (#368)

## sentry-cli 1.35.3

* Add a warning about new Docker entrypoint (#367)

## sentry-cli 1.35.2

* Change entrypoint for Docker image (#358)
* Use `perl` over `strftime` in bash hook (#359)
* Fix iTunes Connect BCSymbolMap handling in `upload-dif` (#362)
* Display error messages when re-uploading broken DIFs (#363)

## sentry-cli 1.35.1

* Resolve a hang on certain windows versions on shutdown (#349)

## sentry-cli 1.34.0

* Improve the error message for renamed projects (#330)
* Fix appcenter commands on Windows (#331)
* Fix grammar in some help texts (#337, @gorgos)
* Fix frozen upload-dif on some Windows versions (#342)

## sentry-cli 1.33.0

* Add support for AppCenter CLI for codepush releases (#327)
* Deprecate the codepush CLI command (#327)
* Fix a bug where commands would fail with connection errors

## sentry-cli 1.32.3

* Skip invalid ZIP files during debug file upload (#320)
* Generate better error messages for renamed projects (#321)

## sentry-cli 1.32.2

* Compress debug symbols for faster uploads (#315)
* Refactor `send-event` to include more consistent information (#316, #318)

## sentry-cli 1.32.1

* Improve update prompts (#306, @danielcompton)
* Support event environments in bash hook (#312, @geniass)
* Use `DWARF_DSYM_FOLDER_PATH` in upload-dsym (#313)
* Skip malformed object files during upload scan (#313)

## sentry-cli 1.32.0

* Drop support for older macOS versions to work around an old xcode linker bug

## sentry-cli 1.31.2

* Disabled automatic crash reporting

## sentry-cli 1.31.1

* Fixed out of bounds panic for sourcemaps without sources (#299)
* Fixed commit detection when VSTS was used (#300)

## sentry-cli 1.31.0

* Restrict file permissions for newly created `.sentryclirc` (#296)
* Fix `SENTRY_DSN` environment variable parsing for `send-event` action (#292)
* Build statically linked `musl`-based binaries for Linux (#294)
* Detect `HEROKU_SLUG_COMMIT` in propose-version (#298)

## sentry-cli 1.30.5

* Add better error diagnostics (internal change, #288)

## sentry-cli 1.30.4

* Show correct identifiers when uploading Windows symbols (#280)

## sentry-cli 1.30.3

* Attempted to make the windows executable more portable (#269)
* Fixed the JavaScript API (#270)
* Fixed a bug where breadcrumbs were not always sent (#268)

## sentry-cli 1.30.2

* Fixed #252

## sentry-cli 1.30.1

* Expose `execute` on SentryCli js wrapper

## sentry-cli 1.30.0

* Improve the upload for debug information files. It is now faster, allows to resume after network errors, and supports much larger files.
* Add commands to upload Breakpad and ELF (Linux) symbols. See our [documentation page](https://docs.sentry.io/learn/cli/dif/) for more information.
* Fix JavaScript tests on Windows

## sentry-cli 1.29.1

* Fix NPM installation on Windows

## sentry-cli 1.29.0

* **BREAKING**: Drop support for Node 0.12. Please pin version `1.28.4` or install sentry-cli using a [different method](https://docs.sentry.io/learn/cli/installation/#automatic-installation) if you still require Node 0.12.
* Fix NPM installation behind proxies
* Remove console output when using the JS interface

## sentry-cli 1.28.4

* Revert `Info.plist` handling to pre-`1.27.1` as it was causing issues when the `"Preprocess Info.plist File"` setting was turned on in Xcode
* Include CA certificates in the Docker container

## sentry-cli 1.28.3

* Reverted new config handling because of problems it caused.

## sentry-cli 1.28.2

* Fixed use of `SENTRYCLI_CDNURL` to override the npm download URL. See the [documentation](https://docs.sentry.io/learn/cli/installation/#installation-via-npm) for more information
* Better handling of environment variables and config files. Please let us know if one of your configuration files or environments doesn't get recognized anymore after the update
* The official docker image is now smaller and does not require dependencies anymore
* Replaced confusing errors when using `codepush` with hints to resolve the error

## sentry-cli 1.28.1

* Expose getPath() to not break setups

## sentry-cli 1.28.0

* Change JS bindings to be conform with the cli interface
  Please note that this is a breaking change if you used the JS interface before.

## sentry-cli 1.27.1

* Read from the correct `Info.plist` in XCode builds, courtesy of @adbi
* Allow to specify device family and model in `send-event`, courtesy of @kirkins
* Supply environment variables when using the JavaScript API
* Allow to override the NPM download URL via `SENTRYCLI_CDNURL` environment variable

## sentry-cli 1.27.0

* Support all options in the JS binding for `upload-sourcemaps`, courtesy of @montogeek
* Enable automatic IP addresses when sending events with `send-event`, courtesy of @kirkins
* No longer require secret keys to send events with `send-event`
* Improve and speed up debug symbol handling in `upload-dsym`

## sentry-cli 1.26.1

* Faster discovery of debug symbols in `upload-dsyms`
* Fix a bug in sourcemap uploading via JS, courtesy of @roelvanhintum
* Security update to OpenSSL 1.0.2n for Linux builds
* Fix a SSL verification command line flag

## sentry-cli 1.26.0

* The npm package has moved to [`@sentry/cli`](https://www.npmjs.com/package/@sentry/cli)
* Installing with npm on Windows now downloads the 64-bit version
* Exit with a proper error code when `send-event` fails, courtesy of @kirkins
* More informative errors on failed API requests
* No more annoying update reminders in the Docker images

## sentry-cli 1.25.0

* Do not run update nagger if the command is not connected to a terminal
* Source map uploading now correctly determines sourcemap references even if the rewrite
  flag is not passed.
* There is an offical Docker image with `sentry-cli` preinstalled:
  `docker run --rm -it -v $(pwd):/work getsentry/sentry-cli sentry-cli --help`
* Added support for automatically determining corvoda releases.

## sentry-cli 1.24.1

* Fix an issue with bash hooking not working if sentry-cli was installed on a path
  containing whitespace

## sentry-cli 1.24.0

* Improved sending events from bash. See
  [Sending Events](https://docs.sentry.io/learn/cli/send-event) for more information
* Hook into bash and send events for failed commands automatically. See
  [Bash Hooks](https://docs.sentry.io/learn/cli/send-event/#bash-hook) for more
  information
* Set `SENTRY_LOAD_DOTENV=0` to disable automatic loading of `.env` files
* Fix an issue where `info.plist` files were not resolved in XCode projects
* Fix an issue where the `PROJECT_DIR` environment was not used correctly

## sentry-cli 1.23.0

* Fix a bug that prevented uploads of ProGuard mapping files on Windows
* Improve command and parameter descriptions (`--help`)
* Updated dependencies

## sentry-cli 1.22.0

* Add `--ignore` and `--ignore-file` parameters to `upload-dsyms`
* Fix some typos in the CLI (thanks @mbudde and @AdrienDS)

## sentry-cli 1.21.0

* Fix codepush command for android
* Fixed added bitbucket provider support #115

## sentry-cli 1.20.0

* Updated dependencies
* Added encoding detection for javascript files
* Added bitbucket provider support
* Fixed an issue where codepush was not passing the right plist to the parser

## sentry-cli 1.19.1

* Resolved an issue where sourcemaps were not uploaded (#112)

## sentry-cli 1.19.0

* Added support for preprocessor `info.plist` files
* Unified `info.plist` handling in all places
* Added basic validation for the API URL to avoid common user errors
* Resolved an issue with NPM releases on ES5 environments
* Resolved an issue where `releases propose-version` incorrectly required an org to be
  passed
* Added support for handling `BCSymbolMap` files when uploading dsym files

## sentry-cli 1.18.0

* Ensure parent directories exist when writing Proguard meta properties.
* Write Proguard properties even if upload is disabled.
* Reject leading/trailing spaces in releases.

## sentry-cli 1.17.0

* Made npm install compatible with ES5
* Solved a potential issue with spaces in file paths for npm installation
* Added automatic update check (can be disabled with `update.disable_check` in the config
  or the `SENTRY_DISABLE_UPDATE_CHECK` environment variable)
* Resolved a crash when uploading empty files
* Lowered default symbol upload size to work around some server limitations

## sentry-cli 1.16.0

* added ability to upload proguard files with a forced UUID
* added `difutil uuid` command to print the UUID(s) of a mapping file to stdout

## sentry-cli 1.15.0

* Improved the `no-upload` flag to proguard upload
* Added debug info files debug commands

## sentry-cli 1.14.0

* Added support for disabling desktop notifications (only affects xcode builds so far)
* Added support for uploading proguard files on supported sentry server versions

## sentry-cli 1.13.3

* Fixed installation for npm

## sentry-cli 1.13.2

* Put `sentry-cli.exe` directly into the `bin/` folder on windows for npm installations

## sentry-cli 1.13.1

* Fixed another issue with yarn redownloading binaries

## sentry-cli 1.13.0

* Added `dist` support for send-event
* Improved download script for npm installs to not download unnecessarily with yarn.

## sentry-cli 1.12.0

* Added support for explicit bundle IDs for codepush releases
* Added `--print-release-name` to print out the release name for codepush releases to the
  command line to improve scripting capabilities
* Extended `propose-version` for releases to support iOS and android release names if
  projects are automatically discovered
* Parse grade files instead of android manifests for version and bundle IDs for release
  detection
* Fix broken xcode notifications when projects where opened from the command line
* Fixed limitations in automatically detecting the bundle IDs for xcode projects

## sentry-cli 1.11.1

* Resolved an issue where sourcemap uploading failed when empty files were encountered

## sentry-cli 1.11.0

* Initial work for codepush support (pending support in `react-native-sentry`)
* Moved `react-native-xcode` to `react-native xcode`
* Added support for `${FOO}` style variable expansion in xcode

## sentry-cli 1.10.2

* Fixed an issue for windows npm installation
* Stop generating a debug log file in `/tmp` for npm on unixes

## sentry-cli 1.10.1

* fixed a bug that caused the npm install to fail

## sentry-cli 1.10.0

* Added user support for `send-event`

## sentry-cli 1.9.2

* Improved logging facilities
* Fixed npm installation on windows

## sentry-cli 1.9.1

* Changes sourcemap rewriting to ignore bad files on source inlining.
* Fixed a bug in the JSON output of the `info` command.

## sentry-cli 1.9.0

* Added support for referring to previous hashes in `set-commits` with `OLD_REV..NEW_REV`
* Resolve tags and other refs (like `HEAD`) in commits when a repo is available
* Use newer protocol for release commit updating
* Strip commit SHAs for display
* Strip dotted path prefixes in release names for display

## sentry-cli 1.8.1

* Change the log format for api headers in debug logging
* Added request headers to debug logging

## sentry-cli 1.8.0

* The `info` command now returns an exit code of 1 in case the config is incomplete
* Added `--config-status-json` to the `info` command to better support sentry-cli invoked
  from scripts
* dsym batches are now calculated by size and not by file count. This should solve a few
  413 errors some users are experiencing
* The dsym upload will now skip over files that do not contain DWARF debug information
  which resolves issues where release files were uploaded as debug symbols instead of the
  actual dsym files

## sentry-cli 1.7.0

* Sourcemap uploads now automatically replace previous files with the same name.
* Honor `CLICOLOR` environment variable
* Added progress bars for source map and debug symbol upload
* No longer attempt to upload multiple versions of debug symbols with the same UUID. This
  was an issue where signed and unsigned debug symbols were discovered in derived data in
  case of debug builds.
* Support `--validate` and `--rewrite` in one command better for source map upload.

## sentry-cli 1.6.0

* Added `--fingerprint` support to `send-event`
* Added distribution support.

**Breaking Change**: releases managed for react-native and mobile are now using the new
distribution feature. Use older versions of `sentry-cli` if you do not wish to manage
distributions on self hosted Sentry versions.

## sentry-cli 1.5.0

* Added `--uuid` parameter to `upload-dsym`
* Added `--no-zips` parameter to `upload-dsym`
* Added `--derived-data` parameter to `upload-dsym`

## sentry-cli 1.4.1

* resolved an issue with some features of xcode variable expansion not working correctly

## sentry-cli 1.4.0

* Added basic support for working with the improved relases API that span projects in an
  org
* Added deploy support

## sentry-cli 1.3.0

* improved file and release list rendering
* added `sentry-cli releases propose-version`

## sentry-cli 1.2.0

* Resolved references to sourcemaps sometimes being incorrectly detected
* Resolved an issue where an incorrect Info.plist file was found (#48)
* Added support for `.env` files
* Better support SSL CA bundles on linux systems (probe more locations)
* Added `--finalize` option to automatically finalize releases on creation
* Improved `sentry-cli info` command rendering and clarity
* Added background processing for `sentry react-native-xcode`

## sentry-cli 1.1.0

* `upload-dsyms` when launched from xcode will now upload symbols in the background and
  notify with OS X notifications about changes

## sentry-cli 1.0.0

* Added support for associating dsyms with builds on supporting sentry servers

## sentry-cli 0.28.0

* Improved validation of parameters and error reporting
* Added progress bar to updater
* Added command to finalize releases

## sentry-cli 0.27.1

* Resolved an issue that the xcode integration for react native would log out a bogus
  error

## sentry-cli 0.27.0

* Added support for fetching sourcemaps from react-native's packager
* Resolved an issue with some sourcemaps not rewriting correctly

## sentry-cli 0.26.0

* Added `react-native-xcode` command to support react-native sourcemap generation and
  uploading
* Automatically create releases on sourcemap upload

## sentry-cli 0.25.0

* Resolved an issue that caused windows versions to write backslashes in URLs in release
  artifacts

## sentry-cli 0.24.0

* Fix zip upload

## sentry-cli 0.23.0

* Added support for upcoming reprocessing feature on sentry for dsym uploads.

## sentry-cli 0.22.0

* Improved dsym uploading support (fixes #29)

## sentry-cli 0.21.1

* Resolved an issue where release builds of react-native would not automatically find the
  sourcemap references

## sentry-cli 0.21.0

* Upon sourcemap uploading the `sentry-cli` tool is now automatically attempting to find
  matching sourcemaps and emit a `Sourcemap` header with the correct reference. This helps
  in situations like react-native where the source reference in the file is malformed or
  points to a non existing file by default
* fixed a bug with the `--rewrite` flag on the upload sourcemaps tool which caused
  incorrect sources to be inlined. This is now properly supported.
* `--strip-common-prefix` on the upload sourcemaps tool now skips over paths which are not
  absolute.

## sentry-cli 0.20.0

* added support for sourcemap rewriting. This will automatically inline sourcecode and
  flatten indexed sourcemaps and can optionally remove prefixes from source paths. This is
  useful for react native which otherwise will not work since sourcecode is not contained.

## sentry-cli 0.19.5

* Improved symbol uploading

## sentry-cli 0.19.4

* Improved logging of http requests
* Fixed an issue that caused a crash if the `TERM` environment variable was not set

## sentry-cli 0.19.3

* Recompiled for Linux to better support arch linux and others

## sentry-cli 0.19.2

* Resolved issue with multi-chunk dsym uploads failing

## sentry-cli 0.19.1

* Changed domain to `sentry.io`

## sentry-cli 0.19.0

* Improved handling of `SENTRY_DSN` so that it can be set to an invalid value and
  `sentry-cli` continues functioning unless you are trying to send an actual event.

## sentry-cli 0.18.0

* added the new `issues` command to bulk manage issues

## sentry-cli 0.17.0

* Added support for debug logging

## sentry-cli 0.16.1

* Upgraded the internal SHA1 library

## sentry-cli 0.16.0

* Added support for `http.proxy_url`
* Added support for `http.proxy_username`
* Added support for `http.proxy_password`

## sentry-cli 0.15.0

* Added support for the `http.keepalive` setting

## sentry-cli 0.14.0

* added proxy support
* removed global dsym uploading which is now done differently

## sentry-cli 0.13.1

* Fixed an issue that caused validation of sourcemaps to fail if wildcard paths (`~/`)
  were used.

## sentry-cli 0.13.0

* Default sourcemap url prefix to `~` to support the new wildcard feature

## sentry-cli 0.12.1

* Fixed windows support by bundling OpenSSL statically

## sentry-cli 0.12.0

* Added basic windows support
* Added `send-event` to submit events to Sentry

## sentry-cli 0.11.0

* Added `login` command.

## sentry-cli 0.10.1

* Made missing ref failures on non minimized JS files warnings instead of errors

## sentry-cli 0.10.0

* Added support for basic sourcemap validation with the `--validate` flag

## sentry-cli 0.9.0

* Ignore `--ext` for explicitly provided files on sourcemap uploads
* Properly handle `--ext`

## sentry-cli 0.8.0

* Added the ability to upload individual sourcemaps as files

## sentry-cli 0.7.0

* Added `info` command
* Addded `.sentryclirc` config file support

## sentry-cli 0.6.0

* Updated release commands

## sentry-cli 0.5.1

* Fixes uninstall support

## sentry-cli 0.5.0

Added basic sourcemap support.

## sentry-cli 0.4.0

Added sudo support to the update command.

## sentry-cli 0.3.0

Updated sentry CLI to have improved x-code dsym upload support and added an update
command.

## 0.2.0 - Alpha Release

Added support for sentry auth tokens.

## 0.1.0 - Initial Release

An initial release of the tool.
