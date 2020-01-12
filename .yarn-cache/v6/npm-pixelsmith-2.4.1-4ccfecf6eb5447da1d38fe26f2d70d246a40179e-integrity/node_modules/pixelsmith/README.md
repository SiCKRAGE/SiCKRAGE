# pixelsmith [![Build status](https://travis-ci.org/twolfson/pixelsmith.png?branch=master)](https://travis-ci.org/twolfson/pixelsmith)

Node based engine for [spritesmith][] built of top of [get-pixels][] and [save-pixels][].

[spritesmith]: https://github.com/Ensighten/spritesmith
[get-pixels]: https://github.com/mikolalysenko/get-pixels
[save-pixels]: https://github.com/mikolalysenko/save-pixels

This can be used for constructing a canvas, placing images on it, and extracting the result image.

## Getting Started
Install the module with: `npm install pixelsmith`

```js
// Load in our dependencies
var Pixelsmith = require('pixelsmith');

// Create a new engine
var pixelsmith = new Pixelsmith();

// Interpret some images from disk
pixelsmith.createImages(['img1.jpg', 'img2.png'], function handleImages (err, imgs) {
  // If there was an error, throw it
  if (err) {
    throw err;
  }

  // We recieve images in the same order they were given
  imgs[0].width; // 50 (pixels)
  imgs[0].height; // 100 (pixels)

  // Create a canvas that fits our images (200px wide, 300px tall)
  var canvas = pixelsmith.createCanvas(200, 300);

  // Add the images to our canvas (at x=0, y=0 and x=50, y=100 respectively)
  canvas.addImage(imgs[0], 0, 0);
  canvas.addImage(imgs[1], 50, 100);

  // Export canvas to image
  var resultStream = canvas['export']({format: 'png'});
  resultStream; // Readable stream outputting PNG image of the canvas
});
```

## Documentation
This module was built to the specification for spritesmith engines.

**Specification version:** 2.0.0

https://github.com/twolfson/spritesmith-engine-spec/tree/2.0.0

### `engine.createImages(images, cb)`
Our `createImages` methods supports the following types of images:

- image `String` - Filepath to image
- image `Object` - Vinyl object with buffer for image (uses buffer)
- image `Object` - Vinyl object with stream for image (uses stream)
- image `Object` - Vinyl object with `null` for image (reads buffer from provided filepath)

### `canvas.export(options)`
Our `export` method provides support for the following options:

- options `Object`
    - background `Number[]` - `rgba` array of value for background
        - By default, the background is `[0, 0, 0, 0]` (transparent black)
        - `[0]` - Red value for background
            - Can range from 0 to 255
        - `[1]` - Green value for background
            - Can range from 0 to 255
        - `[2]` - Blue value for background
            - Can range from 0 to 255
        - `[3]` - Alpha/transparency value for background
            - Can range from 0 to 255
    - quality `Number` - Optional quality percentage for JPEG images
        - This value can range from 0 to 100

## Contributing
In lieu of a formal styleguide, take care to maintain the existing coding style. Add unit tests for any new or changed functionality. Lint via `npm run lint` and test via `npm test`.

## Donating
Support this project and [others by twolfson][twolfson-projects] via [donations][twolfson-support-me].

<http://twolfson.com/support-me>

[twolfson-projects]: http://twolfson.com/projects
[twolfson-support-me]: http://twolfson.com/support-me

## Unlicense
As of Nov 24 2014, Todd Wolfson has released this repository and its contents to the public domain.

It has been released under the [UNLICENSE][].

[UNLICENSE]: UNLICENSE
