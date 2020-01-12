# Change Log

## [2.1.0] - 2018-11-10
- Add wider node support by using `readable-stream` module (thx @coolstuffit and @RignonNoel)

## [2.0.0] - 2018-07-04
- Rename `sortByMsgId` parameter to `sort` (BREAKING)
- Change `sort` parameter to accept custom compare function (thx @probertson)

## [1.3.1] - 2018-02-20
- Fix catastrophic backtracking vulnerability in patch version to reach more users.

## [1.4.0] - 2018-02-19
- Fix catastrophic backtracking vulnerability in line folding regex (thx @davisjam).
- Add sort option for PO compilation (thx @AlexMost).

## [1.3.0] - 2017-08-03
- Add line folding length option to `po.compile` (thx @SleepWalker).
- Update code to use new buffer API.

## [1.2.2] - 2017-01-11
- Use semistandard coding style.
- Remove unreachable code (thx @jelly).
- Replace grunt with npm scripts.
- Replace jshint with eslint.

## [1.2.1] - 2016-11-26
- Fix typo in readme (thx @TimKam).
- New project maintainer.

## [1.2.0] - 2016-06-13
- Fix compilation of plurals when msgstr only contains one element (thx @maufl).
- Fix example in readme (thx @arthuralee).

## [1.1.2] - 2015-10-07
- Update dependencies.

## [1.1.1] - 2015-06-04
- Fix hash table location value in compiled mo files

## [1.1.0] - 2015-01-21
- Add `po.createParseStream` method for parsing PO files from a Stream source
- Update documentation

## [1.0.0] - 2015-01-21
- Bump version to 1.0.0 to be compatible with semver
- Change tests from nodeunit to mocha
- Unify code style in files and added jshint task to check it
- Add Grunt support to check style and run tests on `npm test`

## [0.2.0] - 2013-12-30
- Remove node-iconv dependency
- Fix a global variable leak (`line` was not defined in `pocompiler._addPOString`)
- Apply some code maintenance (applied jshint rules, added "use strict" statements)
- Update e-mail address in .travis.yml
- Add CHANGELOG file

[2.1.0]: https://github.com/smhg/gettext-parser/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/smhg/gettext-parser/compare/v1.4.0...v2.0.0
[1.4.0]: https://github.com/smhg/gettext-parser/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/smhg/gettext-parser/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/smhg/gettext-parser/compare/v1.2.2...v1.3.0
[1.2.2]: https://github.com/smhg/gettext-parser/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/smhg/gettext-parser/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/smhg/gettext-parser/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/smhg/gettext-parser/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/smhg/gettext-parser/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/smhg/gettext-parser/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/smhg/gettext-parser/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/smhg/gettext-parser/compare/v0.1.10...v0.2.0