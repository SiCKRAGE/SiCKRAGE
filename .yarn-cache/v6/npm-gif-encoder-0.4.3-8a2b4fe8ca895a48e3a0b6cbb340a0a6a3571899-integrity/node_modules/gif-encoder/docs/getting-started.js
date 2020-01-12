// Create a 10 x 10 gif
var GifEncoder = require('../'); // #DEVONLY
// var GifEncoder = require('gif-encoder');  // #DEVONLY
var gif = new GifEncoder(10, 10);

// using an rgba array of pixels [r, g, b, a, ... continues on for every pixel]
// This can be collected from a <canvas> via context.getImageData(0, 0, width, height).data
// var pixels = [0, 0, 0, 255/*, ...*/];  // #DEVONLY
var pixels = require('../test/test-files/checkerboard-pixels.json');

// Collect output
var file = require('fs').createWriteStream(__dirname + '/img.gif');  // #DEVONLY
// var file = require('fs').createWriteStream('img.gif');  // #DEVONLY
gif.pipe(file);

// Write out the image into memory
gif.writeHeader();
gif.addFrame(pixels);
// gif.addFrame(pixels); // Write subsequent rgba arrays for more frames
gif.finish();