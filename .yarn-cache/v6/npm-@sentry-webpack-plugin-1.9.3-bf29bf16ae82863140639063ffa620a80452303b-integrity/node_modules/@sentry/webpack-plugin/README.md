<p align="center">
    <a href="https://sentry.io" target="_blank" align="center">
        <img src="https://sentry-brand.storage.googleapis.com/sentry-logo-black.png" width="280">
    </a>
<br/>
    <h1>Sentry Webpack Plugin</h1>
</p>

[![Travis](https://img.shields.io/travis/getsentry/sentry-webpack-plugin.svg?maxAge=2592000)](https://travis-ci.org/getsentry/sentry-webpack-plugin)
[![codecov](https://codecov.io/gh/getsentry/sentry-webpack-plugin/branch/master/graph/badge.svg)](https://codecov.io/gh/getsentry/sentry-webpack-plugin)
[![npm version](https://img.shields.io/npm/v/@sentry/webpack-plugin.svg)](https://www.npmjs.com/package/@sentry/webpack-plugin)
[![npm dm](https://img.shields.io/npm/dm/@sentry/webpack-plugin.svg)](https://www.npmjs.com/package/@sentry/webpack-plugin)
[![npm dt](https://img.shields.io/npm/dt/@sentry/webpack-plugin.svg)](https://www.npmjs.com/package/@sentry/webpack-plugin)

[![deps](https://david-dm.org/getsentry/sentry-webpack-plugin/status.svg)](https://david-dm.org/getsentry/sentry-webpack-plugin?view=list)
[![deps dev](https://david-dm.org/getsentry/sentry-webpack-plugin/dev-status.svg)](https://david-dm.org/getsentry/sentry-webpack-plugin?type=dev&view=list)
[![deps peer](https://david-dm.org/getsentry/sentry-webpack-plugin/peer-status.svg)](https://david-dm.org/getsentry/sentry-webpack-plugin?type=peer&view=list)

A webpack plugin acting as an interface to
[Sentry CLI](https://docs.sentry.io/learn/cli/).

### Installation

Using npm:

```
$ npm install @sentry/webpack-plugin --only=dev
```

Using yarn:

```
$ yarn add @sentry/webpack-plugin --dev
```

### CLI Configuration

You can use either `.sentryclirc` file or ENV variables described here
https://docs.sentry.io/learn/cli/configuration/

### Usage

```js
const SentryCliPlugin = require('@sentry/webpack-plugin');

const config = {
  plugins: [
    new SentryCliPlugin({
      include: '.',
      ignoreFile: '.sentrycliignore',
      ignore: ['node_modules', 'webpack.config.js'],
      configFile: 'sentry.properties',
    }),
  ],
};
```

Also, check the [example](example) directory.

#### Options

| Option | Type | Required | Description |
---------|------|----------|-------------
release | `string` | optional | unique name of a release, must be a `string`, should uniquely identify your release, defaults to `sentry-cli releases propose-version` command which should always return the correct version (**requires access to `git` CLI and root directory to be a valid repository**).
include | `string`/`array` | required | one or more paths that Sentry CLI should scan recursively for sources. It will upload all `.map` files and match associated `.js` files |
entries | `array`/`RegExp`/`function(key: string): bool` | optional | a filter for entry points that should be processed. By default, the release will be injected into all entry points. |
| ignoreFile | `string` | optional | path to a file containing list of files/directories to ignore. Can point to `.gitignore` or anything with same format |
| ignore | `string`/`array` | optional | one or more paths to ignore during upload. Overrides entries in `ignoreFile` file. If neither `ignoreFile` or `ignore` are present, defaults to `['node_modules']` |
| configFile | `string` | optional | path to Sentry CLI config properties, as described in https://docs.sentry.io/learn/cli/configuration/#properties-files. By default, the config file is looked for upwards from the current path and defaults from `~/.sentryclirc` are always loaded |
| ext | `array` | optional | this sets the file extensions to be considered. By default the following file extensions are processed: js, map, jsbundle and bundle. |
| urlPrefix | `string` | optional | this sets an URL prefix at the beginning of all files. This defaults to `~/` but you might want to set this to the full URL. This is also useful if your files are stored in a sub folder. eg: `url-prefix '~/static/js'` |
| urlSuffix | `string` | optional | this sets an URL suffix at the end of all files. Useful for appending query parameters. |
| validate | `boolean` | optional | this attempts sourcemap validation before upload when rewriting is not enabled. It will spot a variety of issues with source maps and cancel the upload if any are found. This is not the default as this can cause false positives. |
| stripPrefix | `array` | optional | when paired with `rewrite` this will chop-off a prefix from uploaded files. For instance you can use this to remove a path that is build machine specific. |
| stripCommonPrefix | `boolean` | optional |  when paired with `rewrite` this will add `~` to the `stripPrefix` array. |
| sourceMapReference | `boolean` | optional | this prevents the automatic detection of sourcemap references. |
| rewrite | `boolean` | optional | enables rewriting of matching sourcemaps so that indexed maps are flattened and missing sources are inlined if possible. defaults to `true` |
| dryRun | `boolean` | optional | attempts a dry run (useful for dev environments) |
| debug | `boolean` | optional | print some useful debug information |
| silent | `boolean` | optional | if `true`, all logs are suppressed (useful for `--json` option) |
| errorHandler | `function(err: Error, invokeErr: function(): void, compilation: Compilation): void` | optional | when Cli error occurs, plugin calls this function. webpack compilation failure can be chosen by calling `invokeErr` callback or not. If you don't want this plugin to prevent further compilation, you can use a compilation warning instead by setting this option to `(err, invokeErr, compilation) => { compilation.warnings.push('Sentry CLI Plugin: ' + err.message) }` instead. defaults to `(err, invokeErr) => { invokeErr() }` |
| setCommits | `Object` | optional | Adds commits to sentry - [see own table below](#setCommits) for more details |


#### <a name="setCommits"></a>options.setCommits:

| Option | Type | Required | Description |
---------|------|----------|-------------
| repo | `string` | required | the full git repo name as defined in Sentry |
| commit | `string` | optional/required | the current (last) commit in the release |
| previousCommit | `string` | optional | the commit before the beginning of this release (in other words, the last commit of the previous release). If omitted, this will default to the last commit of the previous release in Sentry. If there was no previous release, the last 10 commits will be used |
| auto | `boolean` | optional/required | automatically choose the associated commit (uses the current commit). Overrides other options |

You can find more information about these options in our official docs:
https://docs.sentry.io/cli/releases/#sentry-cli-sourcemaps
