// Load in dependencies
var assert = require('assert');
var ndarray = require('ndarray');
var savePixels = require('save-pixels');

// Define our canvas constructor
function Canvas(width, height) {
  // Calculate and save dimensions/data for later
  var len = width * height * 4;
  this.width = width;
  this.height = height;
  this.data = new global.Uint8ClampedArray(len);
  this.ndarray = new ndarray(this.data, [width, height, 4]);

  // Create a store for images
  this.images = [];
}
Canvas.defaultFormat = 'png';
Canvas.supportedFormats = ['jpg', 'jpeg', 'png', 'gif'];
Canvas.prototype = {
  addImage: function (img, x, y) {
    // Save the image for later
    this.images.push({
      img: img,
      x: x,
      y: y
    });
  },
  'export': function (options) {
    // Determine the export format
    var format = options.format || Canvas.defaultFormat;
    assert(Canvas.supportedFormats.indexOf(format) !== -1,
      '`pixelsmith` doesn\'t support exporting "' + format + '". Please use "jpeg", "png", or "gif"');

    // If we have a custom background, fill it in (otherwise default is transparent black `rgba(0, 0, 0, 0)`)
    var ndarray = this.ndarray;
    var data = this.data;
    if (options.background) {
      for (var i = 0; i < data.length; ++i) {
        data[i] = options.background[i % 4];
      }
    }

    // Add each image to the canvas
    var images = this.images;
    images.forEach(function getUrlPath (imageObj) {
      // Iterate over the image's data across its rows
      // setting the original data at that offset
      // [1, 2, 0, 0,
      //  3, 4, 0, 0,
      //  0, 0, 5, 0,
      //  0, 0, 0, 6]
      var img = imageObj.img;
      var xOffset = imageObj.x;
      var yOffset = imageObj.y;
      var colIndex = 0;
      var colCount = img.width; // DEV: Use `width` for padding
      for (; colIndex < colCount; colIndex += 1) {
        var rowIndex = 0;
        var rowCount = img.height; // DEV: Use `height` for padding
        for (; rowIndex < rowCount; rowIndex += 1) {
          var rgbaIndex = 0;
          var rgbaCount = 4;
          for (; rgbaIndex < rgbaCount; rgbaIndex += 1) {
            // If we are working with a 4 dimensional array, ignore the first dimension
            // DEV: This is a GIF; [frames, width, height, rgba]
            var val;
            if (img.shape.length === 4) {
              val = img.get(0, colIndex, rowIndex, rgbaIndex);
            // Otherwise, transfer data directly
            } else {
              val = img.get(colIndex, rowIndex, rgbaIndex);
            }
            ndarray.set(xOffset + colIndex, yOffset + rowIndex, rgbaIndex, val);
          }
        }
      }
    });

    // Concatenate the ndarray into a png
    return savePixels(ndarray, format, options);
  }
};

// Export Canvas
module.exports = Canvas;
