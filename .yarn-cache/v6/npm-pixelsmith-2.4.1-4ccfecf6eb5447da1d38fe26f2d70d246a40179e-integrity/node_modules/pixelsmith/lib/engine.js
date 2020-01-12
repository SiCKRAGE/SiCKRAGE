// Load in our dependencies
var async = require('async');
var concat = require('concat-stream');
var getPixels = require('get-pixels');
var mime = require('mime-types');
var vinylFile = require('vinyl-file');
var Canvas = require('./canvas');

function Pixelsmith(options) {
  // There are no options for our constructor
}
Pixelsmith.specVersion = '2.0.0';
Pixelsmith.prototype = {
  createCanvas: function (width, height) {
    // Create and return a new canvas
    var canvas = new Canvas(width, height);
    return canvas;
  },
  // Define our mass image population
  createImage: function (file, callback) {
    // In series
    async.waterfall([
      // Load the images into memory
      function loadImage (cb) {
        // If the file is a string, upcast it to buffer-based vinyl
        // DEV: We don't use `Vinyl.isVinyl` since that was introduced in Sep 2015
        //   We want some backwards compatibility with older setups
        if (typeof file === 'string') {
          vinylFile.read(file, cb);
        // Otherwise, callback with the existing vinyl object
        } else {
          cb(null, file);
        }
      },
      function loadPixels (file, cb) {
        // If the vinyl object is null, then load from disk
        if (file.isNull()) {
          getPixels(file.path, cb);
        } else {
          var concatStream = concat(function handleFileBuffer (buff) {
            // https://github.com/scijs/get-pixels/blob/2e8766f62a9043d74a4b1047294a25fea5b2eacf/node-pixels.js#L179
            if (buff.length === 0) {
              return cb(new Error('Expected image "' + file.path + '" to not be empty but it was'));
            }
            getPixels(buff, mime.lookup(file.path), function handleGetPixels (err, contents) {
              if (err) {
                err.message += ' (' + file.path + ')';
              }
              cb(err, contents);
            });
          });
          // https://github.com/gulpjs/vinyl/commit/d14ba4a7b51f0f3682f65f2aa4314d981eb1029d
          if (file.isStream()) {
            file.contents.pipe(concatStream);
          } else if (file.isBuffer()) {
            concatStream.end(file.contents);
          } else {
            throw new Error('Unrecognized Vinyl type');
          }
        }
      },
      function saveImgSize (image, cb) {
        // Save the width and height
        // If there are 4 dimensions, use the last 3
        // DEV: For gifs, the first dimension is frames
        if (image.shape.length === 4) {
          image.width = image.shape[1];
          image.height = image.shape[2];
        // Otherwise, use the normal [width, height, rgba] set
        } else {
          image.width = image.shape[0];
          image.height = image.shape[1];
        }
        cb(null, image);
      }
    ], callback);
  },
  createImages: function (files, callback) {
    // In parallel, calculate each of our images
    async.map(files, this.createImage.bind(this), callback);
  }
};

// Export our engine
module.exports = Pixelsmith;
