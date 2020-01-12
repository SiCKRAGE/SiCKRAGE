# spritesmith changelog
3.4.0 - Upgraded to `pixelsmith@2.3.0` to propagate `npm audit` fix

3.3.1 - Corrected license attribution and URL

3.3.0 - Upgraded to `pixelsmith@2.2.0` to add support for Vinyl@2

3.2.1 - Switched from `twolfson-style` to ESLint

3.2.0 - Removed support for Node.js < 4

3.1.1 - Added support for transpiled ES6 modules

3.1.0 - Upgraded to `pixelsmith@2.1.0` to add quality support for JPEG images

3.0.1 - Updated donation URL

3.0.0 - Moved to class and added support for outputting streams

2.0.1 - Updated donation URL

2.0.0 - Upgraded to `spritesmith-engine-spec@2.0.0`

1.5.0 - Added requisite for specVersion to be provided by an engine

1.4.6 - Moved to older version of npm to repair Travis CI

1.4.5 - Updated link to specification

1.4.4 - Moved to Gratipay to bit.ly for donations

1.4.3 - Added newsletter badge to README

1.4.2 - Updated supported node version to `>= 0.10.0`

1.4.1 - Added `foundry` for release

1.4.0 - Upgraded to `pixelsmith@1.2.0` to add better PNG support

1.3.2 - Moved off of deprecated "licenses" to "license" in `package.json` via @pdehaan in #54

1.3.1 - Added `node@0.12` and `iojs` to CI tests. Temporarily ignoring `iojs` due to `canvassmith` building issues

1.3.0 - Upgraded to `pixelsmith@1.1.0` to pick up background fill support. Fixes twolfson/gulp.spritesmith#33

1.2.0 - Upgraded to `layout@2.2.0` to restore optimal `binary-tree` packing. Fixes #48

1.1.0 - Upgraded to `layout@2.1.0` to support `Atom`/`node-webkit` environments

1.0.3 - Added links to examples from other documentation sections

1.0.2 - Moved to consistent documentation bullets with `grunt-spritesmith` and `gulp.spritesmith`

1.0.1 - Added attribution to README

1.0.0 - Major release with multiple breaking changes:

- Moved to `pixelsmith` as default engine
- Removed all other engines
- Removed `addEngine`
- Overhauled documentation
- Made tests more explicit
- Moved to `binary-tree` as default algorithm

0.21.2 - Moved to `fix-travis-ci` to resolve `node@0.8` + `jscs` issues

0.21.1 - Fixed up style issues in README

0.21.0 - Added `twolfson-style` for consistent styling and linting

0.20.1 - Fixed bad image handling

0.20.0 - Upgraded to `phantomjssmith@0.5.0` to pick up JPEG support

0.19.6 - Replaced `doubleshot` with `mocha` and cleaned up test suite

0.19.5 - Moved to `npm@1.x.x` in Travis CI to fix `node@0.8` issues

0.19.4 - Added `npm` upgrade to Travis CI to fix `node@0.8` issues

0.19.3 - Added link to CLI utility via @bevacqua in #46

0.19.2 - Updated documentation for adding new engines. Fixes #44

0.19.1 - Added link to `gulp.spritesmith` via @hitautodestruct in #40

0.19.0 - Added ability to turn off image sorting via `imageOpts`

0.18.0 - Upgraded `gmsmith` to implicitly find `imagemagick`

0.17.5 - Upgraded doubleshot to latest for proper exit codes

0.17.4 - Fixed bad name for pngsmith in fallback chain

0.17.3 - Fixed bad fallback chain. Fixes twolfson/grunt-spritesmith#62

0.17.2 - Integrated Travis CI

0.17.1 - Fixed missing links in README

0.17.0 - Added `pngsmith` as an engine, allowing external dependency-free installation

0.16.0 - Moved to `canvassmith@0.2.0` for `giflib` support

0.15.0 - Moved to `phantomjssmith@0.4.0` and added `timeout` option

0.14.0 - Moved to `gmsmith@0.3.0` for detection of imagemagick

0.13.0 - Moved to `phantomjssmith@0.3.0` and fixed bad expected sprite

0.12.1 - Fixed up test files

0.12.0 - Moved to latest `phantomjssmith` for reduced file size output

0.11.1 - Rearranged README and added notes about engines

0.11.0 - Optimize padded spritesheets to ignore trailing padding

0.10.0 - Adding `padding` parameter to `params`

0.9.0 - Added `properties` to output (i.e. spritesheet `height` and `width`)

0.8.0 - Added support for `engineOpts` and upgraded `gmsmith` to `0.2.0` for `imagemagick` `engineOpt`

0.7.1 - See `git log`
