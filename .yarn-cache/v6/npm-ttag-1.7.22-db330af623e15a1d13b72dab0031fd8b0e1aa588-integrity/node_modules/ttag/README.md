# ttag
[![travis](https://api.travis-ci.org/ttag-org/ttag.svg?master)](https://travis-ci.org/ttag-org/ttag) [![codecov](https://codecov.io/gh/ttag-org/ttag/branch/master/graph/badge.svg)](https://codecov.io/gh/ttag-org/ttag)
![downloads](https://img.shields.io/npm/dm/ttag.svg)

[![NPM](https://nodei.co/npm/ttag.png?downloads=true)](https://nodei.co/npm/ttag/)

> :warning: This project [was previously named `c-3po`](https://github.com/ttag-org/ttag/issues/105).
> Some of the talks, presentations, and documentation _may_ reference it with both names.


## Modern javascript i18n localization library based on ES6 tagged templates and the good old GNU gettext

* **Docs** - [https://ttag.js.org/](https://ttag.js.org/)
* **Changelog** - [https://ttag.js.org/docs/changelog.html](https://ttag.js.org/docs/changelog.html)

## Key features
* Uses ES6 template literals for string formatting (no need for sprintf).
* Contexts [support](https://ttag.js.org/docs/context.html)
* It can precompile translations on a build step.
* Plurals support [ngettext](https://ttag.js.org/docs/ngettext.html).
* It can be integrated in any build tool that works with babel.
* Has a builtin [validation](https://ttag.js.org/docs/translations-validation.html) for translated strings format.
* It can use any default locale in sources (not only English).
* Handles [React (jsx) translations](https://ttag.js.org/docs/jsx-gettext.html).
* Can be easily integrated with Create React App. [CRA doc](https://ttag.js.org/docs/create-react-app.html)

## Usage example
```js
import { t, ngettext, msgid } from 'ttag'

// formatted strings
const name = 'Mike';
const helloMike = t`Hello ${name}`;

// plurals (works for en locale out of the box)
const n = 5;
const msg = ngettext(msgid`${ n } task left`, `${ n } tasks left`, n)
```

## Installation

```bash
npm install --save ttag
```
## CLI
You may also need to install ttag-cli for `po` files manipulation.

**ttag cli** - [https://github.com/ttag-org/ttag-cli](https://github.com/ttag-org/ttag-cli)

```bash
npm install --save-dev ttag-cli
```

## Usage from CDN

[https://unpkg.com/ttag/dist/ttag.min.js](https://unpkg.com/ttag/dist/ttag.min.js)

> This project is designed to work in pair with [babel-plugin-ttag](https://github.com/ttag-org/babel-plugin-ttag).  
> But you can also play with it [without transpilation](https://ttag.js.org/docs/quickstart.html).

## Useful links
* [Documentation](https://ttag.js.org)
* [Changelog](https://ttag.js.org/docs/changelog.html)
* [Quick view on JsFiddle playground](https://jsfiddle.net/0atw0hgh/)

## Tutorials
* [Quick Start](https://ttag.js.org/docs/quickstart.html)

## Slides from talks
* [Kyivjs 2017](https://docs.google.com/presentation/d/1oj6ZaXfIfcClROe-4kOMMjnXFExn1gUfF6D30VyznWs/edit?usp=sharing)
* [Odessajs 2017](https://docs.google.com/presentation/d/1XB82-hTLQxP456Bk8UWJb-tZBsHnUHp4lJzmQorxNgs/edit?usp=sharing)

## Talks
* [Odessajs 2017 (video RU)](https://www.youtube.com/watch?v=9QjzpfA9LH4)


