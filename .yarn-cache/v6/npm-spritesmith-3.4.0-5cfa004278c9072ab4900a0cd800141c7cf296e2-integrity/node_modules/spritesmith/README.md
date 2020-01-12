# spritesmith [![Build status](https://travis-ci.org/twolfson/spritesmith.png?branch=master)](https://travis-ci.org/twolfson/spritesmith) [![Subscribe to newsletter](https://img.shields.io/badge/newsletter-subscribe-blue.svg)](http://eepurl.com/bD4qkf)

Convert images into [spritesheets][] and coordinate maps.

[spritesheets]: http://en.wikipedia.org/wiki/Sprite_%28computer_graphics%29#Sprites_by_CSS

`spritesmith` is also available as:

- [grunt plugin](https://github.com/twolfson/grunt-spritesmith)
- [gulp plugin](https://github.com/twolfson/gulp.spritesmith)
- [CLI utility](https://github.com/bevacqua/spritesmith-cli)

A folder of icons processed by `spritesmith`:

![Fork icon][fork-icon] ![+][]
![GitHub icon][github-icon] ![+][]
![Twitter icon][twitter-icon] ![=][]

[fork-icon]: docs/fork.png
[github-icon]: docs/github.png
[twitter-icon]: docs/twitter.png
[+]: docs/plus.png
[=]: docs/equals.png

generates a spritesheet:

![spritesheet](docs/spritesheet.png)

and a coordinate map:

```js
{
  "/home/todd/github/spritesmith/docs/fork.png": {
    "x": 0,
    "y": 0,
    "width": 32,
    "height": 32
  },
  "/home/todd/github/spritesmith/docs/github.png": {
    "x": 32,
    "y": 0,
    "width": 32,
    "height": 32
  },
  // ...
}
```

### Do you like `spritesmith`?
[Support us via donations][support-us] or [spread word on Twitter][twitter]

[support-us]: http://bit.ly/support-spritesmith-1
[twitter]: https://twitter.com/intent/tweet?text=Spritesheets%20made%20easy%20via%20spritesmith&url=https%3A%2F%2Fgithub.com%2Ftwolfson%2Fspritesmith&via=twolfsn

## Breaking changes in 2.0.0
We have moved from `result.image` being a binary string to it being a `Buffer`. This is to use more canonical conventions in Node.js.

We have moved from [spritesmith-engine-spec@1.1.0][] to [spritesmith-engine-spec@2.0.0][]. This means if you use an custom engine (e.g. `gmsmith`, `canvassmith`), then you will need to upgrade it.

```bash
npm install my-engine-smith@latest --save-dev
```

By upgrading the engine, we added support for [Vinyl][] objects via `src` as well as future-proof ourselves for forwarding streaming outputs.

[spritesmith-engine-spec@1.1.0]: https://github.com/twolfson/spritesmith-engine-spec/tree/1.1.0
[spritesmith-engine-spec@2.0.0]: https://github.com/twolfson/spritesmith-engine-spec/tree/2.0.0

## Breaking changes in 3.0.0
We have updated our API to return streams for images. This required moving to a `constructor` and splitting apart image creation and processing.

We have maintained legacy support for `spritesmith` via `Spritesmith.run` which has an identical API to the `spritesmith` function in `spritesmith<3.0.0`.

```js
// Before
var spritesmith = require('spritesmith');
spritesmith({src: sprites}, function handleResult (err, result) { /* ... */ });

// After
var Spritesmith = require('spritesmith');
Spritesmith.run({src: sprites}, function handleResult (err, result) { /* ... */ });
```

## Getting started
`spritesmith` can be installed via npm: `npm install spritesmith`

```js
// Load in dependencies
var Spritesmith = require('spritesmith');

// Generate our spritesheet
var sprites = ['fork.png', 'github.png', 'twitter.png'];
Spritesmith.run({src: sprites}, function handleResult (err, result) {
  result.image; // Buffer representation of image
  result.coordinates; // Object mapping filename to {x, y, width, height} of image
  result.properties; // Object with metadata about spritesheet {width, height}
});
```

### Usage with streaming output
We support streaming output by breaking down `run` into 2 parts:

```js
// Load in dependencies
var Spritesmith = require('spritesmith');

// Create a new spritesmith and process our images
var sprites = ['fork.png', 'github.png', 'twitter.png'];
var spritesmith = new Spritesmith();
spritesmith.createImages(sprites, function handleImages (err, images) {
  images[0].width; // Width of image
  images[0].height; // Height of image

  // Create our result
  var result = spritesmith.processImages(images);
  result.image; // Readable stream outputting image
  result.coordinates; // Object mapping filename to {x, y, width, height} of image
  result.properties; // Object with metadata about spritesheet {width, height}
});
```

## Documentation
`spritesmith` exports a `Spritesmith` constructor as its `module.exports`.

If you would like a faster build time or need to support an obscure image format, see `params.engine`.

If you would like to adjust how images are laid out, see `params.algorithm` and `params.algorithmOpts`.

### `Spritesmith.run(params, callback)`
Helper function that initializes a new `Spritesmith` instance, creates images, and processes them into a spritesheet

- params `Object` - Container for parameters
    - src `String[]|Object[]` - Same as `src` for `spritesmith.createImages`
    - All other parameters accepted by `new Spritesmith` or `processImages` should be passed in here (e.g. `engine`, `algorithm`)
- callback `Function` - Error-first function that receives compiled spritesheet and information
    - `callback` should have signature `function (err, result)`
    - err `Error|null` - If an error occurred, this will be it
    - result `Object` - Container for result items
        - Same signature as content returned by `spritesmith.processImages` (i.e. `{image, coordinates, properties}`)
        - image `Buffer` - In-memory representation of image
        - coordinates `Object` - Same as `coordinates` returned by `spritesmith.processImages`
        - properties `Object` - Same as `properties` returned by `spritesmith.processImages`

### `new Spritesmith(params)`
Constructor for a new `Spritesmith` instance

- params `Object` - Container for parameters
    - engine `String|Object` - Optional engine override to use
        - By default we use [`pixelsmith`][], a node-based `spritesmith` engine
        - An example usage of `engine` can be found in the [Examples section](#engine)
        - For more engine options, see the [Engines section](#engines)
    - engineOpts `Object` - Options to pass through to engine for settings
        - For example `phantomjssmith` accepts `timeout` via `{engineOpts: {timeout: 10000}}`
        - See your engine's documentation for available options

[`pixelsmith`]: https://github.com/twolfson/pixelsmith

### `spritesmith.createImages(src, callback)`
Interpret images via the `spritesmith` engine

- src `String[]|Object[]` - Array of filepaths for images to include in spritesheet
    - If a `String` is provided, then it's used as the image's filepath
    - If an `Object` is provided, then it should be a [Vinyl][] object pointing to the source image
        - Depending on the engine, we may/may not use the contents (e.g. `gmsmith` uses filepaths only)
- callback `Function` - Error-first function that receives compiled spritesheet and map
    - `callback` should have signature `function (err, images)`
    - err `Error|null` - If an error occurred, this will be it
    - images `Object[]` - Array of processed images
        - Each `image` will be a proprietary object for the engine
        - Each `image` will line up with the specification from [spritesmith-engine-spec][spec-createImages]
        - image `Object` - Metadata container about corresponding input image at same index
            - height `Number` - Height in pixels of corresponding input image at same index
            - width `Number` - Width in pixels of corresponding input image at same index

[Vinyl]: https://github.com/gulpjs/vinyl
[spec-createImages]: https://github.com/twolfson/spritesmith-engine-spec/tree/2.0.0#enginecreateimagesimages-cb

### `spritesheet.processImages(images, options)`
Place interpretted images on a canvas and export spritesheet

- images `Object[]` - Images generated via `spritesmith.createImages`
- options `Object` - Container for options
    - padding `Number` - Padding to use between images
        - For example if `2` is provided, then there will be a `2px` gap to the right and bottom between each image
        - An example usage of `padding` can be found in the [Examples section](#padding)
    - exportOpts `Mixed` - Options to pass through to engine for export
        - For example `gmsmith` supports `quality` via `{exportOpts: {quality: 75}}`
        - See your engine's documentation for available options
    - algorithm `String` - Optional algorithm to pack images with
        - By default we use `binary-tree` which packs images as efficiently as possible
        - An example usage of `algorithm` can be found in the [Examples section](#algorithm)
        - For more algorithm options, see the [Algorithms section](#algorithms)
    - algorithmOpts `Object` - Optional algorithm options to pass through to algorithm for layout
        - For example `top-down` supports ignoring sorting via `{algorithmOpts: {sort: false}}`
        - See your algorithm's documentation for available options
            - https://github.com/twolfson/layout#algorithms

**Returns:**

- result `Object` - Container for result information
    - image `ReadableStream` - [Readable stream][] outputting generated image contents
    - coordinates `Object` - Map from filepath to coordinate information between original sprite and spritesheet
        - `filepath` will be the same as provided in `params.src`
        - [filepath] `Object` - Container for coordinate information
            - For those keeping track, this is `result.coordinates[filepath]`
            - x `Number` - Horizontal position of top-left corner of original sprite on spritesheet
            - y `Number` - Vertical position of top-left corner of original sprite on spritesheet
            - width `Number` - Width of original sprite
            - height `Number` - Height of original sprite
    - properties `Object` - Container for information about spritesheet
        - width `Number` - Width of the spritesheet
        - height `Number` - Height of the spritesheet

[Readable stream]: https://nodejs.org/api/stream.html#stream_class_stream_readable

### Algorithms
Images can be laid out in different fashions depending on the algorithm. We use [`layout`][] to provide you as many options as possible. At the time of writing, here are your options for `params.algorithm`:

[`layout`]: https://github.com/twolfson/layout

|         `top-down`        |          `left-right`         |         `diagonal`        |           `alt-diagonal`          |          `binary-tree`          |
|---------------------------|-------------------------------|---------------------------|-----------------------------------|---------------------------------|
| ![top-down][top-down-img] | ![left-right][left-right-img] | ![diagonal][diagonal-img] | ![alt-diagonal][alt-diagonal-img] | ![binary-tree][binary-tree-img] |

[top-down-img]: https://raw.githubusercontent.com/twolfson/layout/2.0.2/docs/top-down.png
[left-right-img]: https://raw.githubusercontent.com/twolfson/layout/2.0.2/docs/left-right.png
[diagonal-img]: https://raw.githubusercontent.com/twolfson/layout/2.0.2/docs/diagonal.png
[alt-diagonal-img]: https://raw.githubusercontent.com/twolfson/layout/2.0.2/docs/alt-diagonal.png
[binary-tree-img]: https://raw.githubusercontent.com/twolfson/layout/2.0.2/docs/binary-tree.png

More information can be found in the [`layout`][] documentation:

https://github.com/twolfson/layout

### Engines
An engine can greatly improve the speed of your build (e.g. `canvassmith`) or support obscure image formats (e.g. `gmsmith`).

All `spritesmith` engines adhere to a common specification:

https://github.com/twolfson/spritesmith-engine-spec

This repository adheres to specification version: **2.0.0**

Below is a list of known engines with their tradeoffs:

#### pixelsmith
[`pixelsmith`][] is a `node` based engine that runs on top of [`get-pixels`][] and [`save-pixels`][].

[`get-pixels`]: https://github.com/mikolalysenko/get-pixels
[`save-pixels`]: https://github.com/mikolalysenko/save-pixels

**Key differences:** Doesn't support uncommon image formats (e.g. `tiff`) and not as fast as a compiled library (e.g. `canvassmith`).

#### phantomjssmith
[`phantomjssmith`][] is a [phantomjs][] based engine. It was originally built to provide cross-platform compatibility but has since been succeeded by [`pixelsmith`][].

**Requirements:** [phantomjs][] must be installed on your machine and on your `PATH` environment variable. Visit [the phantomjs website][phantomjs] for installation instructions.

**Key differences:** `phantomjs` is cross-platform and supports all image formats.

[`phantomjssmith`]: https://github.com/twolfson/phantomjssmith
[phantomjs]: http://phantomjs.org/

#### canvassmith
[`canvassmith`][] is a [node-canvas][] based engine that runs on top of [Cairo][].

**Requirements:** [Cairo][] and [node-gyp][] must be installed on your machine.

Instructions on how to install [Cairo][] are provided in the [node-canvas wiki][].

[node-gyp][] should be installed via `npm`:

```bash
npm install -g node-gyp
```

**Key differences:** `canvas` has the best performance (useful for over 100 sprites). However, it is `UNIX` only.

[`canvassmith`]: https://github.com/twolfson/canvassmith
[node-canvas]: https://github.com/learnboost/node-canvas
[Cairo]: http://cairographics.org/
[node-canvas wiki]: (https://github.com/LearnBoost/node-canvas/wiki/_pages
[node-gyp]: https://github.com/TooTallNate/node-gyp/

#### gmsmith
[`gmsmith`][] is a [`gm`][] based engine that runs on top of either [Graphics Magick][] or [Image Magick][].

**Requirements:** Either [Graphics Magick][] or [Image Magick][] must be installed on your machine.

For the best results, install from the site rather than through a package manager (e.g. `apt-get`). This avoids potential transparency issues which have been reported.

[Image Magick][] is implicitly discovered. However, you can explicitly use it via `engineOpts`

```js
{
  engineOpts: {
    imagemagick: true
  }
}
```

**Key differences:** `gmsmith` allows for configuring image quality whereas others do not.

[`gmsmith`]: https://github.com/twolfson/gmsmith
[`gm`]: https://github.com/aheckmann/gm
[Graphics Magick]: http://www.graphicsmagick.org/
[Image Magick]: http://imagemagick.org/

## Examples
### Algorithm
This is an example of using a custom layout via the `alt-diagonal` algorithm.

```js
// Load in dependencies
var fs = require('fs');
var Spritesmith = require('spritesmith');

// Generate our spritesheet
Spritesmith.run({
  src: [
    __dirname + '/fork.png',
    __dirname + '/github.png',
    __dirname + '/twitter.png'
  ],
  algorithm: 'alt-diagonal'
}, function handleResult (err, result) {
  // If there was an error, throw it
  if (err) {
    throw err;
  }

  // Output the image
  fs.writeFileSync(__dirname + '/alt-diagonal.png', result.image);
  result.coordinates, result.properties; // Coordinates and properties
});
```

**Result:**

![alt-diagonal spritesheet](docs/alt-diagonal.png)

### Engine
This is an example of using a custom engine (`canvassmith` in this case).

```js
// Inside package.json
{
    "dependencies": {
        "canvassmith": "~0.2.4"
    }
}
```

```js
// In our script
// Load in dependencies
var fs = require('fs');
var Spritesmith = require('spritesmith');

// Generate our spritesheet
Spritesmith.run({
  src: [
    __dirname + '/fork.png',
    __dirname + '/github.png',
    __dirname + '/twitter.png'
  ],
  engine: require('canvassmith')
}, function handleResult (err, result) {
  // If there was an error, throw it
  if (err) {
    throw err;
  }

  // Output the image
  fs.writeFileSync(__dirname + '/canvassmith.png', result.image);
  result.coordinates, result.properties; // Coordinates and properties
});
```

**Result:**

![canvassmith spritesheet](docs/canvassmith.png)

### Padding
This is an example of adding padding between images.

```js
// Load in dependencies
var fs = require('fs');
var Spritesmith = require('spritesmith');

// Generate our spritesheet
Spritesmith.run({
  src: [
    __dirname + '/fork.png',
    __dirname + '/github.png',
    __dirname + '/twitter.png'
  ],
  padding: 20 // Exaggerated for visibility, normally 1 or 2
}, function handleResult (err, result) {
  // If there was an error, throw it
  if (err) {
    throw err;
  }

  // Output the image
  fs.writeFileSync(__dirname + '/padding.png', result.image);
  result.coordinates, result.properties; // Coordinates and properties
});
```

**Result:**

![padding spritesheet](docs/padding.png)

## Contributing
In lieu of a formal styleguide, take care to maintain the existing coding style. Add unit tests for any new or changed functionality. Lint via `npm run lint` and test via `npm test`.

## Attribution
[GitHub][github-icon] and [Twitter][twitter-icon] icons were taken from [Alex Peattie's JustVector Social Icons][justvector].

[Fork][noun-fork-icon] designed by [P.J. Onori][onori] from The Noun Project

[Plus][+] and [Equals][=] icons were built using the [Ubuntu Light typeface][ubuntu-light].

[justvector]: http://alexpeattie.com/projects/justvector_icons/
[noun-fork-icon]: http://thenounproject.com/noun/fork/#icon-No2813
[onori]: http://thenounproject.com/somerandomdude
[ubuntu-light]: http://font.ubuntu.com/

## License
Copyright (c) 2012 Todd Wolfson

Licensed under the MIT license.
