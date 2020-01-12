save-pixels
===========
Saves an ndarray to an image.

Example
=======
```javascript
var zeros = require("zeros")
var savePixels = require("save-pixels")

//Create an image
var x = zeros([32, 32])
x.set(16, 16, 255)

//Save to a file
savePixels(x, "png").pipe(process.stdout)
```

This writes the foll owing image to stdout:

<img src=https://raw.github.com/mikolalysenko/save-pixels/master/example/example.png>

Install
=======

    npm install save-pixels

### `require("save-pixels")(array, type[, options])`
Saves an ndarray as an image with the given format

* `array` is an `ndarray` of pixels.  Assumes that shape is `[width, height, channels]`
* `type` is the type of the image to save.  Currently supported formats:

  + `"jpeg"`, `"jpg"` - Joint Photographic Experts Group format
  + `"gif"` - Graphics Interchange Format
  + `"png"` - Portable Network Graphics format
  + `"canvas"` - A canvas element

* `options` is an object that alters saving behavior

  + `quality` is the `Number` to use for saved image quality

    + This can only be used with a `"jpeg"` image
    + It range between 1 (low quality) and 100 (high quality) inclusively

**Returns** A stream that you can pipe to serialize the result, or a canvas element if the `type` is `"canvas"`.

# Credits
(c) 2013 Mikola Lysenko. MIT License
