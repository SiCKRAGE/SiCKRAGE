# pixelsmith changelog
2.4.1 - Removed accidental double callback from `getPixels`

2.4.0 - Added filepath info to when invalid file extension loaded. Fixes #16

2.3.0 - Removed `ndarray-fill` to fix `npm audit` vulnerability via @dawidgarus in #17

2.2.2 - Moved to Node.js>=8 to fix Travis CI

2.2.1 - Moved to Node.js>=4 to fix Travis CI

2.2.0 - Added support for Vinyl@2

2.1.3 - Replaced Gratipay with support me page

2.1.2 - Added file size check. Fixes gulp.spritesmith#131

2.1.1 - Upgraded to `get-pixels@3.3.0` via @BS-Harou in #9

2.1.0 - Added `quality` support for JPEGs

2.0.1 - Upgraded to `save-pixels@2.3.0` to resolve `pngjs2` deprecation warning. Fixes #6

2.0.0 - Upgraded to `spritesmith-engine-spec@2.0.0`

1.3.4 - Added `specVersion` support and `spritesmith-engine` keyword

1.3.3 - Updated documentation to be a little cleaner and link to `spritesmith-engine-spec`

1.3.2 - Upgraded to `spritesmith-engine-test@3.0.0` to clean up technical debt

1.3.1 - Removed bad require

1.3.0 - Cleaned up technical debt (e.g. YAGNI on `exporters`)

1.2.2 - Updated supported node versions to `>= 0.10.0`

1.2.1 - Added `foundry` for release

1.2.0 - Upgraded to get-pixels@3.2.3 to add better PNG support

1.1.2 - Moved from deprecated `licenses` key to `license` in `package.json`

1.1.1 - Fixed example in README via @tmcw in #3

1.1.0 - Added support for custom background. Fixes twolfson/gulp.spritesmith#33

1.0.0 - Initial fork from `pngsmith@0.1.3`
