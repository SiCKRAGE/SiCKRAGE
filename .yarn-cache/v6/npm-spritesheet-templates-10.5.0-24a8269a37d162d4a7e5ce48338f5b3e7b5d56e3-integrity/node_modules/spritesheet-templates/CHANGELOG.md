# spritesheet-templates changelog
10.5.0 - Upgraded to handlebars@4.6.0 and handlebars-layouts@3.1.4 to allow using latest handlebars. Fixes #58

10.4.3 - Locked down to handlebars@4.5.3 to stop template extension issues

10.4.2 - Added missing text fixture for CircleCI

10.4.1 - Upgraded to handlebars@4.4.5 to fix vulnerability via @ekelvin in #57

10.4.0 - Upgraded to handlebars@4.3.3 to fix vulnerability

10.3.3 - Added missing fixture for CircleCI

10.3.2 - Moved from Travis CI to CircleCI for easier maintenance

10.3.1 - Upgraded to handlebars@4.1.2 to fix vulnerability

10.3.0 - Updated LESS template to use proper `e` function for using quoteless strings instead of JS

10.2.4 - Upgraded to underscore.string@3.3.0 to fix npm vulnerability warning

10.2.3 - Upgraded to express@3.21.2 to fix GitHub vulnerability warning

10.2.2 - Replaced Gratipay with support me pages

10.2.1 - Fixed README typo via @dms1lva in #50

10.2.0 - Moved from `/* */` to `//` syntax for SASS/SCSS files for consistency with convention via @dpolivy in #49. Fixes #48

10.1.4 - Upgraded to Handlebars@4.0.5 to repair nodesecurity.io complaints via @ebdrup in #46

10.1.3 - Upgraded to Ruby@2.1.1 to repair Travis CI errors

10.1.2 - Corrected jsonArray template to json_array for alignment with documentation

10.1.1 - Corrected CSS documentation to not use `img`. Fixes https://github.com/Ensighten/grunt-spritesmith/issues/153

10.1.0 - Added HTML examples to non-CSS templates

10.0.1 - Added foundry for release

10.0.0 - Added escaping to template strings to allow `@2x` names

9.6.1 - Added back iojs to Travis CI

9.6.0 - Added `json_texture` template via @limikael in #41

9.5.2 - Moved iojs to allowed failure in Travis CI until https://github.com/npm/npm/issues/8406 gets patched

9.5.1 - Moved from deprecated `licenses` key to `license` in `package.json`

9.5.0 - Added `registerHandlebarsHelper` to allow handlebars helper registration

9.4.1 - Added `node@0.12` and `iojs` to CI tests. Upgraded test suite to support them.

9.4.0 - Added retina templates

9.3.2 - Dropped `node@0.8` testing due to `jscs` dependency issues

9.3.1 - Fixed regression with `data.spritesheet_info` fallback logic

9.3.0 - Relocated `options.spritesheetName` to `data.spritesheet_info` in preparation for retina conventions

9.2.2 - Made functions block more granular for future proofing

9.2.1 - Fixed naming inconsistency with sprites-comment section

9.2.0 - Moved to `handlebars` and `handlebars-layouts` to support inheritance (and ultimately retina templates)

9.1.1 - Deprecated `libsass@1.0.1` from Travis CI in favor of `libsass@3.0.2`

9.1.0 - Added explicit list syntax for SASS/SCSS and notes for single-sprite spritesheets in LESS/Stylus

9.0.1 - Refactored test suite to make it more transparent

9.0.0 - Reintroduced `8.3.0` as a major change and fixed Ensighten/spritesmith#49

8.4.0 - Reverted `8.3.0` to remove breaking changes

8.3.0 - Added `variableNameTransforms`/`strings` for Mustache templates. Fixes #37

8.2.1 - Corrected CSS sprite example. Fixes Ensighten/grunt-spritesmith#112

8.2.0 - Added `spritesheetName` option, `spritesheet.px`/`spritesheet_name` variables for formatters, and a bunch of spritesheet/sprites variables to preprocessor templates

8.1.0 - Added `spritesheet.escaped_image` to match `item.escaped_image` property

8.0.0 - Moved to `params` as input and requiring spritesheet information

7.2.0 - Moved to more maintainable pattern in code

7.1.1 - Removed unused `grunt` dependencies

7.1.0 - Added `twolfson-style` for consistent styling and linting

7.0.2 - Fixed missing link in README

7.0.1 - Updated README info

7.0.0 - Renamed from `json2css` to `spritesheet-templates` to focus on functionality

6.1.0 - Removed HTML escaping of CSS selectors. Fixes Ensighten/grunt-spritesmith#104

6.0.0 - Renamed `cssClass` option to `cssSelector`

5.2.2 - Added documentation and example for each template flavor

5.2.1 - Updated Travis CI badge via @shinn in #32

5.2.0 - Added comments explaining how to use each template

5.1.1 - Fixed broken tests due to indentation changes

5.1.0 - Fixed indentation and options for LESS, SCSS, and `scss_maps` templates

5.0.0 - Moved `scss_maps` template from map of all sprites to map variable per sprite. Fixes #29

4.4.1 - Fixed broken `sassc` compilation in Travis CI. Fixes #28

4.4.0 - Updated `scss_maps` template to use height for height via @makeable in #26

4.3.0 - Added `scss_maps` template via @leevigraham in #24

4.2.2 - Add `eight-track` to CSS validation to remove third party dependency

4.2.1 - Added CSS validation to test suite

4.2.0 - Moved to mocha, patched regression for SCSS + libsass

4.1.1 - Added .travis.yml

4.1.0 - Added jsonArray template

4.0.0 - Deprecated object as input. Now only accepting arrays.

3.2.0 - Added `total_width` and `total_height` properties

3.1.0 - Moved all templates to `escaped_image` to allow for safely escaped and some quote-free URLs

3.0.0 - Moved `css` as the default engine

Before 3.0.0 - See commit logs
