# gif-encoder [![Build status](https://travis-ci.org/twolfson/gif-encoder.png?branch=master)](https://travis-ci.org/twolfson/gif-encoder)

Streaming [GIF][] encoder

[GIF]: http://en.wikipedia.org/wiki/Graphics_Interchange_Format

This is built as part of the [gifsockets][] project. It is forked from [gif.js][] to allow for a streaming API and performance optimization.

[gifsockets]: https://github.com/twolfson/gifsockets-server

## Getting Started
Install the module with: `npm install gif-encoder`

```js
// Create a 10 x 10 gif
var GifEncoder = require('gif-encoder');
var gif = new GifEncoder(10, 10);

// using an rgba array of pixels [r, g, b, a, ... continues on for every pixel]
// This can be collected from a <canvas> via context.getImageData(0, 0, width, height).data
var pixels = [0, 0, 0, 255/*, ...*/];

// Collect output
var file = require('fs').createWriteStream('img.gif');
gif.pipe(file);

// Write out the image into memory
gif.writeHeader();
gif.addFrame(pixels);
// gif.addFrame(pixels); // Write subsequent rgba arrays for more frames
gif.finish();
```

## Documentation
`gif-encoder` exports `GifEncoder`, a constructor function which extends `readable-stream@~1.1.9`. This means you can use any `streams1`/`streams2` functionality. I will re-iterate what this means below.

```js
// streams1
var gif = new GifEncoder(10, 10);
gif.on('data', console.log);
gif.on('end', process.exit);

// streams2
var gif = new GifEncoder(10, 10);
gif.on('readable', function () {
  console.log(gif.read());
});
```

### `new GifEncoder(width, height, [options])`
Constructor for a new `GifEncoder`

- width `Number` - Width, in pixels, of the `GIF` to output
- height `Number` - Height, in pixels, of the `GIF` to output
- options `Object` - Optional container for any options
    - highWaterMark `Number` - Number, in bytes, to store in internal buffer. Defaults to 64kB.

**NEVER CALL `.removeAllListeners()`. NO DATA EVENTS WILL BE ABLE TO EMIT.**

> We implement the GIF89a specification which can be found at
>
> http://www.w3.org/Graphics/GIF/spec-gif89a.txt

### Events
#### Event: `data`
`function (buffer) {}`

Emits a [`Buffer`][] containing either header bytes, frame bytes, or footer bytes.

[`Buffer`]: http://nodejs.org/api/buffer.html

#### Event: `end`
`function () {}`

Signifies end of the encoding has been reached. This will be emitted once `.finish()` is called.

#### Event: `error`
`function (error) {}`

Emits an `Error` when internal buffer is exceeded. This occurs when you do not `read` (either via `.on('data')` or `.read()`) and we cannot flush prepared data.

> If you have a very large GIF, you can update [`options.highWaterMark`][Constructor] via the [Constructor][].

[Constructor]: #constructor

#### Event: `readable`
`function () {}`

Emits when the stream is ready to be `.read()` from.

#### Event: `writeHeader#start/stop`
`function () {}`

Emits when at the start and end of `.writeHeader()`.

#### Event: `frame#start/stop`
`function () {}`

Emits when at the start and end of `.addFrame()`

#### Event: `finish#start/stop`
`function () {}`

Emits when at the start and end of `.finish()`

### Settings
#### `gif.setDelay(ms)`
Set milliseconds to wait between frames

- ms `Number` - Amount of milliseconds to delay between frames

#### `setFrameRate(framesPerSecond)`
Set delay based on amount of frames per second. Cannot be used with `gif.setDelay`.

- framesPerSecond `Number` - Amount of frames per second

#### `setDispose(disposalCode)`
Set the disposal code

- disposalCode `Number` - Alters behavior of how to render between frames
    - If no transparent color has been set, defaults to 0.
    - Otherwise, defaults to 2.

```
Values :    0 -   No disposal specified. The decoder is
                  not required to take any action.
            1 -   Do not dispose. The graphic is to be left
                  in place.
            2 -   Restore to background color. The area used by the
                  graphic must be restored to the background color.
            3 -   Restore to previous. The decoder is required to
                  restore the area overwritten by the graphic with
                  what was there prior to rendering the graphic.
         4-7 -    To be defined.
```

Taken from http://www.w3.org/Graphics/GIF/spec-gif89a.txt

#### `setRepeat(n)`
Sets amount of times to repeat `GIF`

- n `Number`
    - If `n` is -1, play once.
    - If `n` is 0, loop indefinitely.
    - If `n` is a positive number, loop `n` times.

#### `setTransparent(color)`
Define the color which represents transparency in the `GIF`.

- color `Hexadecimal Number` - Color to represent transparent background
  - Example: `0x00FF00`

#### `setQuality(quality)`
Set the quality (computational/performance trade-off).

- quality `Positive number`
    - 1 is best colors, worst performance.
    - 20 is suggested maximum but there is no limit.
    - 10 is the default, provided an even trade-off.

### Input/output
#### `read([size])`
Read out `size` bytes or until the end of the buffer. This is implemented by `readable-stream`.

- size `Number` - Optional number of bytes to read out

#### `writeHeader()`
Write out header bytes. We are following `GIF89a` specification.

#### `addFrame(imageData)`
Write out a new frame to the GIF.

- imageData `Array` - Array of pixels for the new frame. It should follow the sequence of `r, g, b, a` and be `4 * height * width` in length.

#### `finish()`
Write out footer bytes.

### Low-level
For performance in [gifsockets][], we needed to open up some lower level methods for fancy tricks.

**Don't use these unless you know what you are doing.**

#### `flushData()`
We have a secondary internal buffer that collects each byte from `writeByte`. This is to prevent create a new `Buffer` and `data` event for *every byte of data*.

This method empties the internal buffer and pushes it out to the `stream` buffer for reading.

#### `pixels`
Internal store for `imageData` passed in by `addFrame`.

#### `analyzeImage(imageData)`
First part of `addFrame`; runs `setImagePixels(removeAlphaChannel(imageData))` and runs `analyzePixels()`.

- imageData `Array` - Same as that in [`addFrame`][]

[`addFrame`]: #addframeimagedata

#### `removeAlphaChannel(imageData)`
Reduces `imageData` into a `Uint8Array` of length `3 * width * height` containing sequences of `r, g, b`; removing the alpha channel.

- imageData `Array` - Same as that in [`addFrame`][]; array containing `r, g, b, a` sequences.

#### `setImagePixels(pixels)`
Save `pixels` as `this.pixels` for image analysis.

- pixels `Array` - Same as `imageData` from [`addFrame`][]
    - **`GifEncoder` will mutate the original data.**

#### `writeImageInfo()`
Second part of `addFrame`; behavior varies on if it is the first frame or following frame.

In either case, it writes out a bunch of bytes about the image (e.g. palette, color tables).

#### `outputImage()`
Third part of `addFrame`; encodes the analyzed/indexed pixels for the GIF format.

## Donating
Support this project and [others by twolfson][gittip] via [gittip][].

[![Support via Gittip][gittip-badge]][gittip]

[gittip-badge]: https://rawgithub.com/twolfson/gittip-badge/master/dist/gittip.png
[gittip]: https://www.gittip.com/twolfson/

## Contributing
In lieu of a formal styleguide, take care to maintain the existing coding style. Add unit tests for any new or changed functionality. Lint via [grunt](https://github.com/gruntjs/grunt) and test via `npm test`.

## UNLICENSE
As of Nov 11 2013, Todd Wolfson has released all code differences since initial fork from [gif.js][] to the public domain.

These differences have been released under the [UNLICENSE][].

[UNLICENSE]: UNLICENSE

At the [gif.js][] time of forking, [gif.js][] was using the [MIT license][].

[gif.js]: https://github.com/jnordberg/gif.js/tree/faee238491302de05a1ed05e4fbe562738a76310

[MIT license]: https://github.com/jnordberg/gif.js/tree/faee238491302de05a1ed05e4fbe562738a76310#license
