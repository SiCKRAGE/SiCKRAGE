# plural-forms
Provides information about the plural forms from any language that you may know

## Installation

```bash
yarn add plural-forms
# or
npm install --save plural-forms
```

## Usage example
```js
import { getNPlurals } from 'plural-forms'

const englishPluralsNumber = getNPlurals('en'); // 2 
```

## Available methods

### getNPlurals(language: string): number
* *language* - language ISO code.
Returns the number of plural forms for locale

**Example**:

```js
import { getNPlurals } from 'plural-forms'

const englishPluralsNumber = getNPlurals('en'); // 2 
```

### getFormula(language: string) : string
* *language* - language ISO code.
Returns plural form formula for locale

**Example**:

```js
import { getFormula } from 'plural-forms'

const englishPluralsNumber = getFormula('en'); // "n!==1'"
```

### getPluralFunc(language: string) : function
* *language* - language ISO code.
Returns function that can compute appropriate form for locale

**Example**:

```js
import { getPluralFunc } from 'plural-forms'
const fn = getPluralFunc('en')

fn(1, ['banana', 'bananas']) // 'banana'
fn(2, ['banana', 'bananas']) // 'bananas'
```

### hasLang(language: string): boolean
* *language* - language ISO code
Returns if language definition exists in catalog

**Example**:

```js
import { hasLang } from 'plural-forms'
hasLang('en') // true
hasLang('zzz') // false
```

## getAvailLangs(): [string]
Returns list with all existing ISO codes of languages from the catalog.

**Example**

```js
import { getAvailLangs } from 'plural-forms';
getAvailLangs() // [en, uk, ...]
```
