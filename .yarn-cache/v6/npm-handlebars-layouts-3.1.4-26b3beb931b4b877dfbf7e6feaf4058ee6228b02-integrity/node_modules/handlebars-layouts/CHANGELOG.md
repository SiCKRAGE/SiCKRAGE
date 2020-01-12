## 3.1.3

Bugfixes:

- Added support for objects with a null prototype. ([#27](https://github.com/shannonmoeller/handlebars-layouts/issues/27), [#28](https://github.com/shannonmoeller/handlebars-layouts/pull/28))

## 3.1.2

Bugfixes:

- Handlebars wasn't playing nice with Object.create, so all cases have been removed in favor of property copying.
- Now using `handlebars.createFrame` with `options.data` and using the result with partials.

## 3.1.1

Bugfixes:

- Corrected handling of partial context when the native syntax is used inside of an embed. ([#25](https://github.com/shannonmoeller/handlebars-layouts/pull/25))

## 3.1.0

Features:

- The `extend` and `embed` helpers now support a [custom context](http://handlebarsjs.com/partials.html#partial-context) to match the signature and features of the default partials syntax: `{{> partialName contextObject foo=bar }}`. ([#21](https://github.com/shannonmoeller/handlebars-layouts/pull/21))

## 3.0.0

Breaking Changes:

- The `@content` value has been removed in favor of the updated `content` helper.

Features:

- The `content` helper may now be used as a subexpression to check for the existance of block content. ([#22](https://github.com/shannonmoeller/handlebars-layouts/issues/22))

```handlebars
Before: {{#if @content.foo}}    {{{block "foo"}}} {{/if}}
After:  {{#if (content "foo")}} {{{block "foo"}}} {{/if}}
```

## 2.0.2

Bugfixes:

- Fixed a regression in the order of content rendering. ([#18](https://github.com/shannonmoeller/handlebars-layouts/issues/18))

## 2.0.1

Bugfixes:

- Added files missing from a bad commit.

## 2.0.0

Breaking changes:

- The `handlebarsLayouts(handlebars)` function no longer automatically registers helpers. Instead it returns an object which is compatible with the `Handlebars.registerHelper` method. If you want the helpers to automatically be registered, use `handlebarsLayouts.register(handlebars)` instead. The return value of both functions has been changed to be the object of helpers rather than the passed-in handlebars instance. ([#15](https://github.com/shannonmoeller/handlebars-layouts/issues/15))

Features:

- Exposed `@content` variable to facilitate conditional blocks. ([#16](https://github.com/shannonmoeller/handlebars-layouts/issues/16))

## 1.1.0

Features:

- Arbitrary attributes may now be given to `extend` and `embed` and are added to the partial's data context.

## 1.0.0

Breaking changes:

- Consolidated `append`, `prepend`, and `replace` helpers into a single `content` helper that accepts a `mode` attribute. (Thank you [Assemble](https://github.com/assemble/handlebars-helpers/blob/master/lib/helpers/helpers-layouts.js#L86) contributors).

Features:

- Deep inheritance.
- Added an `embed` helper to insert a partial that extends from its own layout.
- Added test server for use with Express.

Bugfixes:

- Browserify build was not properly wrapping module with UMD due to missing `standalone` option. Fixes AMD issues.

## 0.3.3

Bugfixes:

- Corrected git paths in `package.json`.

## 0.3.2

Features:

- Added support for Assemble-style registration by exposing a `register` method.

## 0.3.0 - 0.3.1

Features:

- Refactor.
- Switched from Grunt to Gulp.
- Improved tests including coverage.

## 0.2.0

Features:

- Blocks may now be appended to, prepended to, and replaced multiple times.

## 0.1.4

Bugfixes:

- Support precompiled templates.
