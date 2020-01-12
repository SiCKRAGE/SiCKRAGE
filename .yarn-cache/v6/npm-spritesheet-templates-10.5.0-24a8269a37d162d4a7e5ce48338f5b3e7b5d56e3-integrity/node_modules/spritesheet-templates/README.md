# spritesheet-templates [![CircleCI](https://circleci.com/gh/twolfson/spritesheet-templates/tree/master.svg?style=svg)](https://circleci.com/gh/twolfson/spritesheet-templates/tree/master)

Convert spritesheet data into CSS or CSS pre-processor data

`spritesheet-templates`, formerly `json2css`, was built as part of [`spritesmith`][], a tool that converts images into spritesheets and CSS variables.

[`spritesmith`]: https://github.com/Ensighten/spritesmith

## Getting Started
Install the module with: `npm install spritesheet-templates`

```js
// Compilation
var templater = require('spritesheet-templates');
templater({
  sprites: [{
    name: 'github', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'twitter', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'rss', x: 30, y: 50, width: 50, height: 50
  }],
  spritesheet: {
    width: 80, height: 100, image: 'url/path/to/spritesheet.png'
  }
}, {format: 'stylus'}); /*
// Result stylus
$github_x = 0px;
$github_y = 0px;
...
$github = 0px 0px 0px 0px 10px 20px 80px 100px 'url/path/to/spritesheet.png' 'github';
...
$twitter = 10px 20px -10px -20px 20px 30px 80px 100px 'url/path/to/spritesheet.png' 'twitter';
...
$rss = 30px 50px -30px -50px 50px 50px 80px 100px 'url/path/to/spritesheet.png' 'rss';
...
spriteWidth($sprite) {
  width: $sprite[0];
}
...
sprite($sprite) {
  spriteImage($sprite)
  spritePosition($sprite)
  spriteWidth($sprite)
  spriteHeight($sprite)
}

// Inside of your Stylus
.github-logo {
  sprite($github);
}
*/
```

## Documentation
`spritesheet-templates` exports the function `templater` as its `module.exports`.

### `templater(data, options)`
Converter for spritesheet/sprite info into spritesheet

- data `Object` - Container for data for template
    - items `Object[]` - Deprecated alternative key to define `data.sprites`
    - sprites `Object[]` - Array of objects with coordinate data about each sprite on the spritesheet
        - * `Object` - Container for sprite coordinate data
            - For reference, `*` symbolizes any index (e.g. `data.sprites[0]`)
            - name `String` - Name to use for the image
            - x `Number` - Horizontal coordinate of top-left corner of image
            - y `Number` - Vertical coordinate of top-left corner of image
            - width `Number` - Horizontal length of image in pixels
            - height `Number` - Vertical length of image in pixels
    - spritesheet `Object` - Information about spritesheet
        - width `Number` - Horizontal length of image in pixels
        - height `Number` - Vertical length of image in pixels
        - image `String` - URL to use for spritesheet
            - This will typically be used in `background-image`
            - For example, `background-image: url({{spritesheet.image}});`
    - spritesheet_info `Object` - Optional container for metadata about `spritesheet` and its representation
        - name `String` - Prefix to use for all spritesheet variables
            - For example, `icons` will generate `$icons-width`/`$icons-image`/etc in a SCSS template
            - By default, this is `spritesheet` (e.g. `$spritesheet-width`, `$spritesheet-image`)
    - Additional parameters for `retina` templates are documented in the [Retina parameters section](#retina-parameters)
- options `Object` - Optional settings
    - spritesheetName `String` - Deprecated alternative for `spritesheet_info.name`
    - format `String` - Format to generate output in
        - We accept any format inside of the [Templates section](#templates)
            - Custom formats can be added via the [custom methods](#custom)
        - By default, we will use the `css` format
    - formatOpts `Mixed` - Options to pass through to the formatter

**Returns:**

- retVal `String` - Result from specified formatter

#### Retina parameters
`retina` templates require additional parameters `data.retina_sprites`, `data.retina_spritesheet` and `data.retina_groups` to be passed in.

For the variables to be useful, the retina spritesheet should be a 2x scale image of the original spritesheet. Similarly, retina sprites should be positioned in the same layout and order as their normal counterparts (e.g. `[{x: 0, y: 0}, {x: 20, y: 20}]` should correspond to `[{x: 0, y: 0}, {x: 40, y: 40}]`).

- data `Object` - Same container as defined above
    - retina_sprites `Object[]` - Array of objects with coordinate data about each retina sprite for the retina spritesheet
        - Properties are retina equivalent of `data.sprites`
        - These should be in the same order as their normal complements
    - retina_spritesheet `Object` - Information about retina spritesheet
        - Properties are retina equivalent of `data.spritesheet`
    - retina_spritesheet_info `Object` - Optional container for metadata about `retina_spritesheet` and its representation
        - name `String` - Prefix to use for all retina spritesheet variables
            - For example, `retina-icons` will generate `$retina-icons-width`/`$retina-icons-image`/etc in a SCSS template
            - By default, this is `retina-spritesheet` (e.g. `$retina-spritesheet-width`, `$retina-spritesheet-image`)
    - retina_groups `Object[]` - Array of objects that maps to normal and retina sprites
        - * `Object` - Container for data about sprite mapping
            - name `String` - Name to refer to mapping by
                - This is typically used for CSS selectors and variable names
            - index `Number` - Index to look up corresponding normal/retina sprites from `data.sprites`/`data.retina_sprites`
    - retina_groups_info `Object` - Optional container for metadata about `retina_groups` and its representation
        - name `String` - Name to use for `retina_groups` variable
            - For example, `icon-groups` will generate `$icons-groups` in a SCSS template
            - By default, this is `retina-groups` (e.g. `$retina-groups`)

### Templates
Below are our template options for `options.format`.

Handlebars-based templates support inheritance via [`handlebars-layouts`][] (e.g. `{{#extend "css"}}`). Inherited templates must copy/paste JSON front matter. An example can be found in the [Examples section](#examples).

[`handlebars-layouts`]: https://github.com/shannonmoeller/handlebars-layouts

Retina templates have the same setup but are located in the [Retina templates section](#retina-templates) for convenience.

#### `css`
Ouput CSS variables as CSS rules.

**Options:**

- cssSelector `Function` - Override mapping for CSS selector
    - `cssSelector` should have signature `function (sprite) { return 'selector'; }`
    - By default this will return `'.icon-' + sprite.name`
    - It will receive `sprite` with all parameters designed for template

**Handlebars blocks:**

`css` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before CSS rules
- `{{#content "sprites"}}` - CSS rules

**Example:**

```css
.icon-sprite1 {
  background-image: url(nested/dir/spritesheet.png);
  background-position: 0px 0px;
  width: 10px;
  height: 20px;
}
.icon-sprite2 {
/* ... */
```

#### `json`
Output CSS variables in JSON format.

**Example:**

```js
{
    "sprite1": {
        "x": 0,
        "y": 0,
        "width": 10,
        "height": 20,
        "total_width": 80,
        "total_height": 100,
        "image": "nested/dir/spritesheet.png",
        "offset_x": 0,
        "offset_y": 0,
        "px": {
            "x": "0px",
            "y": "0px",
            "offset_x": "0px",
            "offset_y": "0px",
            "height": "20px",
            "width": "10px",
            "total_height": "100px",
            "total_width": "80px"
        },
        "escaped_image": "nested/dir/spritesheet.png"
    },
    "sprite2": {
    // ...
```

#### `json_array`
Output CSS variables as an array of objects.

**Example:**

```js
[
    {
        "name": "sprite1",
        "x": 0,
        "y": 0,
        "width": 10,
        "height": 20,
        "total_width": 80,
        "total_height": 100,
        "image": "nested/dir/spritesheet.png",
        "offset_x": 0,
        "offset_y": 0,
        "px": {
            "x": "0px",
            "y": "0px",
            "offset_x": "0px",
            "offset_y": "0px",
            "height": "20px",
            "width": "10px",
            "total_height": "100px",
            "total_width": "80px"
        },
        "escaped_image": "nested/dir/spritesheet.png"
    },
    {
        "name": "sprite2",
        // ...
```

#### `json_texture`
Output CSS variables as an object in format similar to that of [TexturePacker][]. Useful for game frameworks, such as [Phaser][], [Pixi.js][], and others.

[TexturePacker]: https://www.codeandweb.com/texturepacker
[Phaser]: http://phaser.io/
[Pixi.js]: http://www.pixijs.com/

For consistency with [TexturePacker][], we will use the [basename][] of a given image. `spritesmith` provides this via `sprite.source_image`. If you would like to provide a custom name, then please define `sprite.frame_name`:

[basename]: https://nodejs.org/api/path.html#path_path_basename_p_ext

```js
// Input
{
  sprites: [{
    frame_name: 'hello', name: 'github', x: 0, y: 0, width: 10, height: 20
  }]
}

// Output
{
  frames: {
    hello: {x: 0, y: 0, w: 10, h: 20}
  }
}
```

If neither `sprite.source_image` nor `spriteframe` is used, then `sprite.name` will be used.

For integration in `grunt-spritesmith`/`gulp.spritesmith`, please see their `cssVarMap` documentation.

**Example:**
```js
{
    "frames": {
        "mysprite.png": {
            "frame": {
                "x": 10,
                "y": 20,
                "w": 20,
                "h": 30
            }
        },
        // ...
    },
    "meta": {
        "app": "spritesheet-templates",
        // ...
        "image": "nested/dir/spritesheet.png",
        "scale": 1,
        "size": {
            "w": 80,
            "h": 100
        }
    }
}
```
#### `less`
Output CSS variables as [LESS][] variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

`less` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before LESS variable declarations
- `{{#content "sprites"}}` - LESS variable declarations for sprites
- `{{#content "spritesheet"}}` - LESS variable declarations for spritesheet
- `{{#content "sprite-functions-comment"}}` - Comment before LESS functions for sprite variables
- `{{#content "sprite-functions"}}` - LESS functions for sprite variables
- `{{#content "spritesheet-functions-comment"}}` - Comment before LESS functions for spritesheet variables
- `{{#content "spritesheet-functions"}}` - LESS functions for spritesheet variables

**Example:**

```less
@sprite1-name: 'sprite1';
@sprite1-x: 0px;
@sprite1-y: 0px;
@sprite1-offset-x: 0px;
@sprite1-offset-y: 0px;
@sprite1-width: 10px;
@sprite1-height: 20px;
@sprite1-total-width: 80px;
@sprite1-total-height: 100px;
@sprite1-image: 'nested/dir/spritesheet.png';
@sprite1: 0px 0px 0px 0px 10px 20px 80px 100px 'nested/dir/spritesheet.png' 'sprite1';
@sprite2-name: 'sprite2';
// ...
```

[LESS]: http://lesscss.org/

#### `sass`
Output CSS variables as [SASS][] variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

`sass` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before SASS variable declarations
- `{{#content "sprites"}}` - SASS variable declarations for sprites
- `{{#content "spritesheet"}}` - SASS variable declarations for spritesheet
- `{{#content "sprite-functions-comment"}}` - Comment before SASS functions for sprite variables
- `{{#content "sprite-functions"}}` - SASS functions for sprite variables
- `{{#content "spritesheet-functions-comment"}}` - Comment before SASS functions for spritesheet variables
- `{{#content "spritesheet-functions"}}` - SASS functions for spritesheet variables

**Example:**

```sass
$sprite1-name: 'sprite1'
$sprite1-x: 0px
$sprite1-y: 0px
$sprite1-offset-x: 0px
$sprite1-offset-y: 0px
$sprite1-width: 10px
$sprite1-height: 20px
$sprite1-total-width: 80px
$sprite1-total-height: 100px
$sprite1-image: 'nested/dir/spritesheet.png'
$sprite1: 0px 0px 0px 0px 10px 20px 80px 100px 'nested/dir/spritesheet.png' 'sprite1'
$sprite2-name: 'sprite2'
// ...
```

[SASS]: http://sass-lang.com/

#### `scss`
Output CSS variables as [SCSS][] variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

`scss` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before SCSS variable declarations
- `{{#content "sprites"}}` - SCSS variable declarations for sprites
- `{{#content "spritesheet"}}` - SCSS variable declarations for spritesheet
- `{{#content "sprite-functions-comment"}}` - Comment before SCSS functions for sprite variables
- `{{#content "sprite-functions"}}` - SCSS functions for sprite variables
- `{{#content "spritesheet-functions-comment"}}` - Comment before SCSS functions for spritesheet variables
- `{{#content "spritesheet-functions"}}` - SCSS functions for spritesheet variables

**Example:**

```scss
$sprite1-name: 'sprite1';
$sprite1-x: 0px;
$sprite1-y: 0px;
$sprite1-offset-x: 0px;
$sprite1-offset-y: 0px;
$sprite1-width: 10px;
$sprite1-height: 20px;
$sprite1-total-width: 80px;
$sprite1-total-height: 100px;
$sprite1-image: 'nested/dir/spritesheet.png';
$sprite1: 0px 0px 0px 0px 10px 20px 80px 100px 'nested/dir/spritesheet.png' 'sprite1';
$sprite2-name: 'sprite2';
// ...
```

[SCSS]: http://sass-lang.com/

#### `scss_maps`
Output CSS variables as [SCSS][] maps variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['underscored']` which yields a `snake_case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

`scss_maps` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before SCSS variable declarations
- `{{#content "sprites"}}` - SCSS variable declarations for sprites
- `{{#content "spritesheet"}}` - SCSS variable declaration for spritesheet
- `{{#content "sprite-functions-comment"}}` - Comment before SCSS functions for sprite variables
- `{{#content "sprite-functions"}}` - SCSS functions for sprite variables
- `{{#content "spritesheet-functions-comment"}}` - Comment before SCSS functions for spritesheet variables
- `{{#content "spritesheet-functions"}}` - SCSS functions for spritesheet variables

**Example:**

```scss
$sprite1: (
  name: 'sprite1',
  x: 0px,
  y: 0px,
  offset_x: 0px,
  offset_y: 0px,
  width: 10px,
  height: 20px,
  total_width: 80px,
  total_height: 100px,
  image: 'nested/dir/spritesheet.png'
);
$sprite2: (
// ...
```

#### `stylus`
Output CSS variables as [Stylus][] variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['underscored']` which yields a `snake_case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

`stylus` is a Handlebars based template. We allow for overriding the following sections:

- `{{#content "sprites-comment"}}` - Comment before Stylus variable declarations
- `{{#content "sprites"}}` - Stylus variable declarations for sprites
- `{{#content "spritesheet"}}` - Stylus variable declarations for spritesheet
- `{{#content "sprite-functions-comment"}}` - Comment before Stylus functions for sprite variables
- `{{#content "sprite-functions"}}` - Stylus functions for sprite variables
- `{{#content "spritesheet-functions-comment"}}` - Comment before Stylus functions for spritesheet variables
- `{{#content "spritesheet-functions"}}` - Stylus functions for spritesheet variables

**Example:**

```stylus
$sprite1_name = 'sprite1';
$sprite1_x = 0px;
$sprite1_y = 0px;
$sprite1_offset_x = 0px;
$sprite1_offset_y = 0px;
$sprite1_width = 10px;
$sprite1_height = 20px;
$sprite1_total_width = 80px;
$sprite1_total_height = 100px;
$sprite1_image = 'nested/dir/spritesheet.png';
$sprite1 = 0px 0px 0px 0px 10px 20px 80px 100px 'nested/dir/spritesheet.png';
$sprite2_name = 'sprite2';
// ...
```

[Stylus]: http://learnboost.github.io/stylus/

#### Retina templates
These are a subset of templates that support retina spritesheets. These require retina parameters like `retina_sprites` are provided in order to work properly.

#### `css_retina`
Ouput CSS variables as CSS rules with media query and additional rules for retina support.

**Options:**

- cssSelector `Function` - Override mapping for CSS selector
    - `cssSelector` should have signature `function (retinaGroup) { return 'selector'; }`
    - By default this will return `'.icon-' + retinaGroup.name`
    - It will receive `retinaGroup` with all parameters designed for `retina_groups[*]` in templates (e.g. `name`, `normal`, `retina`)

**Handlebars blocks:**

We extend from the [`css` template](#css) and have its blocks. There are no new sections for retina data.

**Example:**

```css
.icon-sprite1 {
  background-image: url(nested/dir/spritesheet.png);
  background-position: 0px 0px;
  width: 10px;
  height: 20px;
}
/* ... */
@media (-webkit-min-device-pixel-ratio: 2),
       (min-resolution: 192dpi) {
  .icon-sprite1 {
    background-image: url(nested/dir/spritesheet@2x.png);
    background-size: 80px 100px;
  }
}
```

#### `json_retina`
Output retina CSS variables in JSON format.

**Example:**

```js
{
    "sprite1": {
        "normal": {
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 20,
            "image": "nested/dir/spritesheet.png",
            "escaped_image": "nested/dir/spritesheet.png",
            "total_width": 80,
            "total_height": 100,
            "offset_x": 0,
            "offset_y": 0,
            "px": {
                "x": "0px",
                "y": "0px",
                "offset_x": "0px",
                "offset_y": "0px",
                "height": "20px",
                "width": "10px",
                "total_height": "100px",
                "total_width": "80px"
            }
        },
        "retina": {
            "x": 0,
            "y": 0,
            // ...
    },
    "sprite2": {
    // ...
```

#### `json_array_retina`
Output retina CSS variables as an array of objects.

**Example:**

```js
[
    {
        "name": "sprite1",
        "normal": {
            "x": 0,
            "y": 0,
            "width": 10,
            "height": 20,
            "total_width": 80,
            "total_height": 100,
            // ...
        },
        "retina": {
            "x": 0,
            "y": 0,
            "width": 20,
            "height": 40,
            "total_width": 160,
            "total_height": 200,
            // ...
        }
    },
    {
        "name": "sprite2",
        // ...
```

#### `less_retina`
Output retina CSS variables as [LESS][] variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

We extend from the [`less` template](#less) and have its blocks. There are no new sections for retina data.

**Example:**

```less
@sprite1-name: 'sprite1';
@sprite1-x: 0px;
@sprite1-y: 0px;
@sprite1-offset-x: 0px;
@sprite1-offset-y: 0px;
@sprite1-total-width: 80px;
@sprite1-total-height: 100px;
// ...
@sprite2-2x-total-width: 160px;
@sprite2-2x-total-height: 200px;
@sprite2-2x-image: 'nested/dir/spritesheet@2x.png';
@sprite2-2x: 0px 0px 0px 0px 20px 40px 160px 200px 'nested/dir/spritesheet@2x.png' 'sprite2@2x';
// ...
@sprite3-group: 'sprite3' @sprite3 @sprite3-2x;
@retina-groups: @sprite1-group @sprite2-group @sprite3-group;
// ...
```

#### `sass_retina`
Output retina CSS variables as [SASS][] variables and mixins.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

We extend from the [`sass` template](#sass) and have its blocks. There are no new sections for retina data.

**Example:**

```scss
$sprite1-name: 'sprite1'
$sprite1-x: 0px
$sprite1-y: 0px
$sprite1-offset-x: 0px
$sprite1-total-width: 80px
$sprite1-total-height: 100px
// ...
$sprite2-2x-total-width: 160px
$sprite2-2x-total-height: 200px
$sprite2-2x-image: 'nested/dir/spritesheet@2x.png'
$sprite2-2x: (20px, 40px, -20px, -40px, 40px, 60px, 160px, 200px, 'nested/dir/spritesheet@2x.png', 'sprite2@2x', )
// ...
$sprite3-group: ('sprite3', $sprite3, $sprite3-2x, )
$retina-groups: ($sprite1-group, $sprite2-group, $sprite3-group, )
// ...
```

#### `scss_retina`
Output retina CSS variables as [SCSS][] variables and mixins.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['dasherize']` which yields a `dash-case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

We extend from the [`scss` template](#scss) and have its blocks. There are no new sections for retina data.

**Example:**

```scss
$sprite1-name: 'sprite1';
$sprite1-x: 0px;
$sprite1-y: 0px;
$sprite1-offset-x: 0px;
$sprite1-total-width: 80px;
$sprite1-total-height: 100px;
// ...
$sprite2-2x-total-width: 160px;
$sprite2-2x-total-height: 200px;
$sprite2-2x-image: 'nested/dir/spritesheet@2x.png';
$sprite2-2x: (20px, 40px, -20px, -40px, 40px, 60px, 160px, 200px, 'nested/dir/spritesheet@2x.png', 'sprite2@2x', );
// ...
$sprite3-group: ('sprite3', $sprite3, $sprite3-2x, );
$retina-groups: ($sprite1-group, $sprite2-group, $sprite3-group, );
// ...
```

#### `scss_maps_retina`
Output retina CSS variables as [SCSS][] maps variables.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['underscored']` which yields a `snake_case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

We extend from the [`scss_maps` template](#scss_maps) and have its blocks. There are no new sections for retina data.

**Example:**

```scss
$sprite1: (
  name: 'sprite1',
  x: 0px,
  y: 0px,
  offset_x: 0px,
  offset_y: 0px,
  total_width: 80px,
  total_height: 100px,
  // ...
);
$sprite2: (
  // ...
  total-width: 160px,
  total-height: 200px,
  image: 'nested/dir/spritesheet@2x.png'
);
// ...
$sprite3-group: (
  name: 'sprite3',
  normal: $sprite3,
  retina: $sprite3-2x
);
$retina-groups: ($sprite1-group, $sprite2-group, $sprite3-group, );
// ...
```

#### `stylus_retina`
Output retina CSS variables as [Stylus][] variables and mixins.

**Options:**

- functions `Boolean` - Flag to include mixins or not
    - By default this is `true` (mixins will be included)
- variableNameTransforms `String[]` - Array of `underscore.string` methods to run on variable names
    - For example, `['camelize']` would transform `icon-home-x` to `iconHomeX`
    - By default, this is `['underscored']` which yields a `snake_case` name
    - `underscore.string`: http://epeli.github.io/underscore.string/#api
        - We use `chain` which allows for `toUpperCase` and `toLowerCase`
        - http://epeli.github.io/underscore.string/#s-string-gt-chain

**Handlebars blocks:**

We extend from the [`stylus` template](#stylus) and have its blocks. There are no new sections for retina data.

**Example:**

```stylus
$sprite1_name = 'sprite1';
$sprite1_x = 0px;
$sprite1_y = 0px;
$sprite1_offset_x = 0px;
$sprite1_offset_y = 0px;
$sprite1_total_width = 80px;
$sprite1_total_height = 100px;
// ...
$sprite2_2x_total_width = 160px;
$sprite2_2x_total_height = 200px;
$sprite2_2x_image = 'nested/dir/spritesheet@2x.png';
$sprite2_2x = 20px 40px -20px -40px 40px 60px 160px 200px 'nested/dir/spritesheet@2x.png' 'sprite2@2x';
// ...
$sprite3_group = 'sprite3' $sprite3 $sprite3_2x;
$retina_groups = $sprite1_group $sprite2_group $sprite3_group;
// ...
```

#### Custom
Custom templates can be added dynamically via `templater.addTemplate` and `templater.addHandlebarsTemplate`.

##### Template data
The parameters passed into your template are known as `data`. These are a cloned copy of the `data` originally passed in. We add some normalized properties for your convenience.

- data `Object` - Data available to template
    - items `Object[]` - Deprecated alias for `data.sprites`
    - sprites `Object[]` - Array of objects with coordinate data about each sprite on the spritesheet
        - * `Object` - Container for sprite coordinate data
            - For reference, `*` symbolizes any index (e.g. `data.sprites[0]`)
            - name `String` - Name to use for the image
            - x `Number` - Horizontal coordinate of top-left corner of image
            - y `Number` - Vertical coordinate of top-left corner of image
            - width `Number` - Horizontal length of image in pixels
            - height `Number` - Vertical length of image in pixels
            - total_width `Number` - Width of entire spritesheet
            - total_height `Number` - Height of entire spritesheet
            - image `String` - URL path to spritesheet
            - escaped_image `String` - URL encoded `image`
            - offset_x `Number` - Negative value of `x`. Useful to `background-position`
            - offset_y `Number` - Negative value of `y`. Useful to `background-position`
            - px `Object` - Container for numeric values including `px`
                - x `String` - `x` suffixed with `px`
                - y `String` - `y` suffixed with `px`
                - width `String` - `width` suffixed with `px`
                - height `String` - `height` suffixed with `px`
                - total_width `String` - `total_width` suffixed with `px`
                - total_height `String` - `total_height` suffixed with `px`
                - offset_x `String` - `offset_x` suffixed with `px`
                - offset_y `String` - `offset_y` suffixed with `px`
    - spritesheet `Object` - Information about spritesheet
        - name `String` - Deprecated alias for `spritesheet_info.name`
        - width `Number` - Horizontal length of image in pixels
        - height `Number` - Vertical length of image in pixels
        - image `String` - URL to use for spritesheet
            - This will typically be used in `background-image`
            - For example, `background-image: url({{spritesheet.image}});`
        - escaped_image `String` - URL encoded `image`
        - px `Object` container for numeric values including `px`
            - width `String` - `width` suffixed with `px`
            - height `String` - `height` suffixed with `px`
    - spritesheet_name `String` - Deprecated alias for `spritesheet_info.name`
    - spritesheet_info `Object` - Container for information about `spritesheet` and its representation
        - name `String` - Name for `spritesheet`
    - options `Mixed` - Options to passed through via `options.formatOpts`
    - If we have retina parameters were passed in, then we prepare additional retina properties as well
        - More info can be found on these parameters in [Retina template data](#retina-template-data)

###### Handlebars template data
We provide an extra set of data for `handlebars` templates for variable/string names.

- data.sprites[*].strings `Object` - Container for sprite-relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - name `String` - Transformed name of sprite (e.g. `icon-home`)
    - name_name `String` - Transformed combination of sprite name and `-name` string (e.g. `icon-home-name`)
    - name_x `String` - Transformed combination of sprite name and `-x` string (e.g. `icon-home-x`)
    - name_y `String` - Transformed combination of sprite name and `-y` string (e.g. `icon-home-y`)
    - name_offset_x `String` - Transformed combination of sprite name and `-offset-x` string (e.g. `icon-home-offset-x`)
    - name_offset_y `String` - Transformed combination of sprite name and `-offset-y` string (e.g. `icon-home-offset-y`)
    - name_width `String` - Transformed combination of sprite name and `-width` string (e.g. `icon-home-width`)
    - name_height `String` - Transformed combination of sprite name and `-height` string (e.g. `icon-home-height`)
    - name_total_width `String` - Transformed combination of sprite name and `-total-width` string (e.g. `icon-home-total-width`)
    - name_total_height `String` - Transformed combination of sprite name and `-total-height` string (e.g. `icon-home-total-height`)
    - name_image `String` - Transformed combination of sprite name and `-image` string (e.g. `icon-home-image`)
    - name_sprites `String` - Transformed combination of sprite name and `-sprites` string (e.g. `icon-home-sprites`)
    - name_group `String` - Transformed combination of sprite name and `-group` string (e.g. `icon-home-group`)
    - name_group_name `String` - Transformed combination of sprite name and `-group-name` string (e.g. `icon-home-group-name`)
    - name_normal `String` - Transformed combination of sprite name and `-normal` string (e.g. `icon-home-normal`)
    - name_retina `String` - Transformed combination of sprite name and `-retina` string (e.g. `icon-home-retina`)
    - bare_name `String` - Transformed word for `name`
    - bare_x `String` - Transformed word for `x`
    - bare_y `String` - Transformed word for `y`
    - bare_offset_x `String` - Transformed word for `offset-x`
    - bare_offset_y `String` - Transformed word for `offset-y`
    - bare_width `String` - Transformed word for `width`
    - bare_height `String` - Transformed word for `height`
    - bare_total_width `String` - Transformed word for `total-width`
    - bare_total_height `String` - Transformed word for `total-height`
    - bare_image `String` - Transformed word for `image`
    - bare_sprites `String` - Transformed word for `sprites`
    - bare_group `String` - Transformed word for `group`
    - bare_group_name `String` - Transformed word for `group-name`
    - bare_normal `String` - Transformed word for `normal`
    - bare_retina `String` - Transformed word for `retina`
- data.spritesheet.strings `Object` - Deprecated container for spritesheet-relevant variable/string names
    - Contents will match the same as `data.spritesheet_info.strings`
- data.spritesheet_info.strings `Object` - Container for spritesheet-relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - name `String` - Transformed name of spritesheet (e.g. `icon-home`)
    - name_name `String` - Transformed combination of spritesheet name and `-name` string (e.g. `icon-home-name`)
    - name_x `String` - Transformed combination of spritesheet name and `-x` string (e.g. `icon-home-x`)
    - name_y `String` - Transformed combination of spritesheet name and `-y` string (e.g. `icon-home-y`)
    - name_offset_x `String` - Transformed combination of spritesheet name and `-offset-x` string (e.g. `icon-home-offset-x`)
    - name_offset_y `String` - Transformed combination of spritesheet name and `-offset-y` string (e.g. `icon-home-offset-y`)
    - name_width `String` - Transformed combination of spritesheet name and `-width` string (e.g. `icon-home-width`)
    - name_height `String` - Transformed combination of spritesheet name and `-height` string (e.g. `icon-home-height`)
    - name_total_width `String` - Transformed combination of spritesheet name and `-total-width` string (e.g. `icon-home-total-width`)
    - name_total_height `String` - Transformed combination of spritesheet name and `-total-height` string (e.g. `icon-home-total-height`)
    - name_image `String` - Transformed combination of spritesheet name and `-image` string (e.g. `icon-home-image`)
    - name_sprites `String` - Transformed combination of spritesheet name and `-sprites` string (e.g. `icon-home-sprites`)
    - name_group `String` - Transformed combination of spritesheet name and `-group` string (e.g. `icon-home-group`)
    - name_group_name `String` - Transformed combination of spritesheet name and `-group-name` string (e.g. `icon-home-group-name`)
    - name_normal `String` - Transformed combination of spritesheet and `-normal` string (e.g. `icon-home-normal`)
    - name_retina `String` - Transformed combination of spritesheet and `-retina` string (e.g. `icon-home-retina`)
    - bare_name `String` - Transformed word for `name`
    - bare_x `String` - Transformed word for `x`
    - bare_y `String` - Transformed word for `y`
    - bare_offset_x `String` - Transformed word for `offset-x`
    - bare_offset_y `String` - Transformed word for `offset-y`
    - bare_width `String` - Transformed word for `width`
    - bare_height `String` - Transformed word for `height`
    - bare_total_width `String` - Transformed word for `total-width`
    - bare_total_height `String` - Transformed word for `total-height`
    - bare_image `String` - Transformed word for `image`
    - bare_sprites `String` - Transformed word for `sprites`
    - bare_group `String` - Transformed word for `group`
    - bare_group_name `String` - Transformed word for `group-name`
    - bare_normal `String` - Transformed word for `normal`
    - bare_retina `String` - Transformed word for `retina`
- data.strings `Object` - Container for generic strings
    - Each of these strings will be transformed via `variableNameTransforms`
    - bare_name `String` - Transformed word for `name`
    - bare_x `String` - Transformed word for `x`
    - bare_y `String` - Transformed word for `y`
    - bare_offset_x `String` - Transformed word for `offset-x`
    - bare_offset_y `String` - Transformed word for `offset-y`
    - bare_width `String` - Transformed word for `width`
    - bare_height `String` - Transformed word for `height`
    - bare_total_width `String` - Transformed word for `total-width`
    - bare_total_height `String` - Transformed word for `total-height`
    - bare_image `String` - Transformed word for `image`
    - bare_sprites `String` - Transformed word for `sprites`
    - bare_group `String` - Transformed word for `group`
    - bare_group_name `String` - Transformed word for `group-name`
    - bare_normal `String` - Transformed word for `normal`
    - bare_retina `String` - Transformed word for `retina`

###### Retina template data
These are additional properties of the template data when retina parameters have been passed in (e.g. `retina_sprites`, `retina_groups`). As with the normal data, it is cloned copy of the original data with additional properties for convenience.

- data `Object` - Same container as defined above
    - retina_sprites `Object[]` - Array of objects with coordinate data about each retina sprite for the retina spritesheet
        - Properties are retina equivalent of `data.sprites` (e.g. `name`, `x`, `offset_y`, `px`)
    - retina_spritesheet `Object` - Information about retina spritesheet
        - Properties are retina equivalent of `data.spritesheet` (e.g. `width`, `image`, `px`)
            - We do not provide `retina_spritesheet.name` as `name` is deprecated
    - retina_spritesheet_info `Object` - Optional container for metadata about `retina_spritesheet` and its representation
        - Properties are retina equivalent of `data.spritesheet_info` (e.g. `name`)
    - retina_groups `Object[]` - Array of objects that maps to normal and retina sprites
        - * `Object` - Container for data about sprite mapping
            - name `String` - Name to refer to mapping by
            - index `Number` - Index of corresponding normal/retina sprites from `data.sprites`/`data.retina_sprites`
            - normal `Object` - Normal sprite from `data.sprites` that corresponds to our mapping
                - This has all the same properties as `data.sprites[*]` (e.g. `name`, `x`, `offset_y`, `px`)
            - retina `Object` - Retina sprite from `data.retina_sprites` that corresponds to our mapping
                - This has all the same properties as `data.retina_sprites[*]` (e.g. `name`, `x`, `offset_y`, `px`)
    - retina_groups_info `Object` - Optional container for metadata about `retina_groups` and its representation
        - name `String` - Name for `retina_groups`

###### Retina Handlebars template data
Retina specific properties will have the same corresponding new data for Handlebars templates

- data.retina_sprites[*].strings `Object` - Container for retina sprite-relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - Properties are retina equivalent of `data.sprites[*].strings` (e.g. `name`, `name_name`, `bare_name`)
- data.retina_spritesheet_info.strings `Object` - Container for retina spritesheet-relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - Properties are retina equivalent of `data.spritesheet_info.strings` (e.g. `name`, `name_sprites`, `bare_name`)
- data.retina_groups[*].strings `Object` - Container for group-relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - name `String` - Transformed name of retina group (e.g. `icon-home`)
    - name_name `String` - Transformed combination of retina group name and `-name` string (e.g. `icon-home-name`)
    - name_x `String` - Transformed combination of retina group name and `-x` string (e.g. `icon-home-x`)
    - name_y `String` - Transformed combination of retina group name and `-y` string (e.g. `icon-home-y`)
    - name_offset_x `String` - Transformed combination of retina group name and `-offset-x` string (e.g. `icon-home-offset-x`)
    - name_offset_y `String` - Transformed combination of retina group name and `-offset-y` string (e.g. `icon-home-offset-y`)
    - name_width `String` - Transformed combination of retina group name and `-width` string (e.g. `icon-home-width`)
    - name_height `String` - Transformed combination of retina group name and `-height` string (e.g. `icon-home-height`)
    - name_total_width `String` - Transformed combination of retina group name and `-total-width` string (e.g. `icon-home-total-width`)
    - name_total_height `String` - Transformed combination of retina group name and `-total-height` string (e.g. `icon-home-total-height`)
    - name_image `String` - Transformed combination of retina group name and `-image` string (e.g. `icon-home-image`)
    - name_sprites `String` - Transformed combination of retina group name and `-sprites` string (e.g. `icon-home-sprites`)
    - name_group `String` - Transformed combination of retina group name and `-group` string (e.g. `icon-home-group`)
    - name_group_name `String` - Transformed combination of retina group name and `-group-name` string (e.g. `icon-home-group-name`)
    - name_normal `String` - Transformed combination of retina group name and `-normal` string (e.g. `icon-home-normal`)
    - name_retina `String` - Transformed combination of retina group name and `-retina` string (e.g. `icon-home-retina`)
    - bare_name `String` - Transformed word for `name`
    - bare_x `String` - Transformed word for `x`
    - bare_y `String` - Transformed word for `y`
    - bare_offset_x `String` - Transformed word for `offset-x`
    - bare_offset_y `String` - Transformed word for `offset-y`
    - bare_width `String` - Transformed word for `width`
    - bare_height `String` - Transformed word for `height`
    - bare_total_width `String` - Transformed word for `total-width`
    - bare_total_height `String` - Transformed word for `total-height`
    - bare_image `String` - Transformed word for `image`
    - bare_sprites `String` - Transformed word for `sprites`
    - bare_group `String` - Transformed word for `group`
    - bare_group_name `String` - Transformed word for `group-name`
    - bare_normal `String` - Transformed word for `normal`
    - bare_retina `String` - Transformed word for `retina`
- data.retina_groups_info.strings `Object` - Container for retina groups relevant variable/string names
    - Each of these strings will be transformed via `variableNameTransforms`
    - name `String` - Transformed name of retina groups (e.g. `icon-home`)
    - name_name `String` - Transformed combination of retina groups name and `-name` string (e.g. `icon-home-name`)
    - name_x `String` - Transformed combination of retina groups name and `-x` string (e.g. `icon-home-x`)
    - name_y `String` - Transformed combination of retina groups name and `-y` string (e.g. `icon-home-y`)
    - name_offset_x `String` - Transformed combination of retina groups name and `-offset-x` string (e.g. `icon-home-offset-x`)
    - name_offset_y `String` - Transformed combination of retina groups name and `-offset-y` string (e.g. `icon-home-offset-y`)
    - name_width `String` - Transformed combination of retina groups name and `-width` string (e.g. `icon-home-width`)
    - name_height `String` - Transformed combination of retina groups name and `-height` string (e.g. `icon-home-height`)
    - name_total_width `String` - Transformed combination of retina groups name and `-total-width` string (e.g. `icon-home-total-width`)
    - name_total_height `String` - Transformed combination of retina groups name and `-total-height` string (e.g. `icon-home-total-height`)
    - name_image `String` - Transformed combination of retina groups name and `-image` string (e.g. `icon-home-image`)
    - name_sprites `String` - Transformed combination of retina groups name and `-sprites` string (e.g. `icon-home-sprites`)
    - name_group `String` - Transformed combination of retina groups name and `-group` string (e.g. `icon-home-group`)
    - name_group_name `String` - Transformed combination of retina groups name and `-group-name` string (e.g. `icon-home-group-name`)
    - name_normal `String` - Transformed combination of retina groups name and `-normal` string (e.g. `icon-home-normal`)
    - name_retina `String` - Transformed combination of retina groups name and `-retina` string (e.g. `icon-home-retina`)
    - bare_name `String` - Transformed word for `name`
    - bare_x `String` - Transformed word for `x`
    - bare_y `String` - Transformed word for `y`
    - bare_offset_x `String` - Transformed word for `offset-x`
    - bare_offset_y `String` - Transformed word for `offset-y`
    - bare_width `String` - Transformed word for `width`
    - bare_height `String` - Transformed word for `height`
    - bare_total_width `String` - Transformed word for `total-width`
    - bare_total_height `String` - Transformed word for `total-height`
    - bare_image `String` - Transformed word for `image`
    - bare_sprites `String` - Transformed word for `sprites`
    - bare_group `String` - Transformed word for `group`
    - bare_group_name `String` - Transformed word for `group-name`
    - bare_normal `String` - Transformed word for `normal`
    - bare_retina `String` - Transformed word for `retina`

##### `templater.addTemplate(name, fn)`
Method to define a custom template under the format of `name`.

- name `String` - Key to store template under for reference via `options.format`
- fn `Function` - Template function
    - Should have signature of `function (data)` and return a `String` output

##### `templater.addHandlebarsTemplate(name, tmplStr)`
Method to define a custom handlebars template under the format of `name`.

As noted in the [Templates section](#templates), these can inherit from existing templates via [`handlebars-layouts`][] conventions (e.g. `{{#extend "scss"}}`). An example can be found in the [Examples section](#examples).

- name `String` - Key to store template under for reference via `options.format`
- tmplStr `String` - Handlebars template to use for formatting
    - This will receive `data` as its `data` (e.g. `{{sprites}}` is `data.sprites`)

##### `templater.addMustacheTemplate(name, tmplStr)`
Deprecated alias for `templater.addHandlebarsTemplate`

## Examples
### Retina configuration
In this example, we will process a template with retina data.

```js
var templater = require('spritesheet-templates');
templater({
  sprites: [{
    name: 'github', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'twitter', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'rss', x: 30, y: 50, width: 50, height: 50
  }],
  // Note that the retina sprites are in the same order as `sprites`
  retina_sprites: [{
    name: 'github@2x', x: 0, y: 0, width: 20, height: 40
  }, {
    name: 'twitter@2x', x: 20, y: 40, width: 40, height: 60
  }, {
    name: 'rss@2x', x: 60, y: 100, width: 100, height: 100
  }],
  spritesheet: {
    width: 80, height: 100, image: 'url/path/to/spritesheet.png'
  },
  retina_spritesheet: {
    width: 160, height: 200, image: 'url/path/to/spritesheet@2x.png'
  },
  retina_groups: [{
    name: 'github', index: 0
  }, {
    name: 'twitter', index: 1
  }, {
    name: 'rss', index: 2
  }]
}, {format: 'scss_retina'}); /*
$github-name: 'github';
$github-x: 0px;
...
$twitter-2x-name: 'twitter@2x';
$twitter-2x-x: 20px;
...
$rss-group-name: 'rss';
$rss-group: ('rss', $rss, $rss-2x, );
$retina-groups: ($github-group, $twitter-group, $rss-group, );
*/
```

### Inheriting from a template
In this example, we will extend the SCSS template to output a minimal set of template data.

It should be noted that we must include the JSON front matter from the original template we are inheriting from to preserve default casing and options.

**scss-minimal.handlebars:**

```handlebars
{
  // Default options
  'functions': true,
  'variableNameTransforms': ['dasherize']
}

{{#extend "scss"}}
{{#content "sprites"}}
{{#each sprites}}
${{strings.name}}: ({{px.x}}, {{px.y}}, {{px.offset_x}}, {{px.offset_y}}, {{px.width}}, {{px.height}}, {{px.total_width}}, {{px.total_height}}, '{{{escaped_image}}}', '{{name}}', );
{{/each}}
{{/content}}
{{#content "spritesheet"}}
${{spritesheet_info.strings.name_sprites}}: ({{#each sprites}}${{strings.name}}, {{/each}});
${{spritesheet_info.strings.name}}: ({{spritesheet.px.width}}, {{spritesheet.px.height}}, '{{{spritesheet.escaped_image}}}', ${{spritesheet_info.strings.name_sprites}}, );
{{/content}}
{{/extend}}
```

**index.js:**

```js
// Load in our dependencies
var fs = require('fs');
var templater = require('spritesheet-templates');

// Register our new template
var scssMinimalHandlebars = fs.readFileSync('scss-minimal.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss-minimal', scssMinimalHandlebars);

// Run our templater
templater({
  sprites: [{
    name: 'github', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'twitter', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'rss', x: 30, y: 50, width: 50, height: 50
  }],
  spritesheet: {
    width: 80, height: 100, image: 'url/path/to/spritesheet.png'
  }
}, {format: 'scss-minimal'}); /*
$github: (0px, 0px, 0px, 0px, 10px, 20px, 80px, 100px, 'url/path/to/spritesheet.png', 'github', );
$twitter: (10px, 20px, -10px, -20px, 20px, 30px, 80px, 100px, 'url/path/to/spritesheet.png', 'twitter', );
$rss: (30px, 50px, -30px, -50px, 50px, 50px, 80px, 100px, 'url/path/to/spritesheet.png', 'rss', );
$spritesheet-sprites: ($github, $twitter, $rss, );
$spritesheet: (80px, 100px, 'url/path/to/spritesheet.png', $spritesheet-sprites, );
*/
```

## Contributing
In lieu of a formal styleguide, take care to maintain the existing coding style. Add unit tests for any new or changed functionality. Lint via `npm run lint` and test via `npm test`.

## Donating
Support this project and [others by twolfson][twolfson-projects] via [donations][twolfson-support-me].

<http://twolfson.com/support-me>

[twolfson-projects]: http://twolfson.com/projects
[twolfson-support-me]: http://twolfson.com/support-me

## Unlicense
As of Sep 08 2013, Todd Wolfson has released this repository and its contents to the public domain.

It has been released under the [UNLICENSE][].

[UNLICENSE]: UNLICENSE

Prior to Sep 08 2013, this repository and its contents were licensed under the [MIT license][].

[MIT license]: https://github.com/twolfson/spritesheet-templates/blob/e601307209b75faa48cb65388a17e0047b561aa0/LICENSE-MIT
