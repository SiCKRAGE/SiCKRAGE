// Load in dependencies
var concat = require('concat-stream');
var Layout = require('layout');
var semver = require('semver');
var through2 = require('through2');

// Specify defaults
var engineDefault = 'pixelsmith';
var algorithmDefault = 'binary-tree';
var SPEC_VERSION_RANGE = '>=2.0.0 <3.0.0';

// Define our spritesmith constructor
function Spritesmith(params) {
  // Process our parameters
  params = params || {};
  var engineName = params.engine || engineDefault;
  var Engine = engineName;

  // If the engine is a `require` path, attempt to load it
  if (typeof engineName === 'string') {
    // Attempt to resolve the engine to verify it is installed at all
    try {
      require.resolve(engineName);
    } catch (err) {
      /* eslint-disable no-console */
      console.error('Attempted to find spritesmith engine "' + engineName + '" but could not.');
      console.error('Please verify you have installed "' + engineName + '" and saved it to your `package.json`');
      console.error('');
      console.error('    npm install ' + engineName + ' --save-dev');
      console.error('');
      /* eslint-enable no-console */
      throw err;
    }

    // Attempt to load the engine
    try {
      // eslint-disable-next-line global-require
      Engine = require(engineName);
      if (typeof Engine !== 'function') {
        Engine = Engine.default;
      }
    } catch (err) {
      /* eslint-disable no-console */
      console.error('Attempted to load spritesmith engine "' + engineName + '" but could not.');
      console.error('Please verify you have installed its dependencies. Documentation should be available at ');
      console.error('');
      // TODO: Consider using pkg.homepage and pkg.repository
      console.error('    https://npm.im/' + encodeURIComponent(engineName));
      console.error('');
      /* eslint-enable no-console */
      throw err;
    }
  }

  // Verify we are on a matching `specVersion`
  if (!semver.satisfies(Engine.specVersion, SPEC_VERSION_RANGE)) {
    throw new Error('Expected `engine` to have `specVersion` within "' + SPEC_VERSION_RANGE + '" ' +
      'but it was "' + Engine.specVersion + '". Please verify you are on the latest version of your engine: ' +
      '`npm install my-engine@latest`');
  }

  // Create and save our engine for later
  this.engine = new Engine(params.engineOpts || {});
}
// Gist of params: {src: files, engine: 'pixelsmith', algorithm: 'binary-tree'}
// Gist of result: image: buffer, coordinates: {filepath: {x, y, width, height}}, properties: {width, height}
Spritesmith.run = function (params, callback) {
  // Create a new spritesmith with our parameters
  var spritesmith = new Spritesmith(params);

  // In an async fashion, create our images
  spritesmith.createImages(params.src, function handleImages(err, images) {
    // If there was an error, callback with it
    if (err) {
      return callback(err);
    }

    // Otherwise, process our images, concat our image, and callback
    // DEV: We don't want to risk dropped `data` events due to calling back with a stream
    var spriteData = spritesmith.processImages(images, params);

    // If an error occurs on the image, then callback with it
    spriteData.image.on('error', callback);

    // Concatenate our image into a buffer
    spriteData.image.pipe(concat({encoding: 'buffer'}, function handleImage(buff) {
      // Callback with all our info
      callback(null, {
        coordinates: spriteData.coordinates,
        properties: spriteData.properties,
        image: buff
      });
    }));
  });
};
Spritesmith.prototype = {
  createImages: function (files, callback) {
    // Forward image creation to our engine
    this.engine.createImages(files, function handleImags(err, images) {
      // If there was an error, callback with it
      if (err) {
        return callback(err);
      }

      // Otherwise, iterate over the images and save their paths (required for coordinates)
      images.forEach(function saveImagePath(img, i) {
        // DEV: We don't use `Vinyl.isVinyl` since that was introduced in Sep 2015
        //   We want some backwards compatibility with older setups
        var file = files[i];
        img._filepath = typeof file === 'object' ? file.path : file;
      });

      // Callback with our images
      callback(null, images);
    });
  },
  processImages: function (images, options) {
    // Set up our algorithm/layout placement and export configuration
    options = options || {};
    var algorithmName = options.algorithm || algorithmDefault;
    var layer = new Layout(algorithmName, options.algorithmOpts);
    var padding = options.padding || 0;
    var exportOpts = options.exportOpts || {};
    var packedObj;

    // Generate stream and info for returning
    var imageStream = through2();
    var retObj = {image: imageStream};

    // Add our images to our canvas (dry run)
    images.forEach(function (img) {
      // Save the non-padded properties as meta data
      var width = img.width;
      var height = img.height;
      var meta = {img: img, actualWidth: width, actualHeight: height};

      // Add the item with padding to our layer
      layer.addItem({
        width: width + padding,
        height: height + padding,
        meta: meta
      });
    });

    // Then, output the coordinates
    // Export and saved packedObj for later
    packedObj = layer.export();

    // Extract the coordinates
    var coordinates = {};
    var packedItems = packedObj.items;
    packedItems.forEach(function (item) {
      var meta = item.meta;
      var img = meta.img;
      var name = img._filepath;
      coordinates[name] = {
        x: item.x,
        y: item.y,
        width: meta.actualWidth,
        height: meta.actualHeight
      };
    });

    // Save the coordinates
    retObj.coordinates = coordinates;

    // Then, generate a canvas
    // Grab and fallback the width/height
    var width = Math.max(packedObj.width || 0, 0);
    var height = Math.max(packedObj.height || 0, 0);

    // If there are items
    var itemsExist = packedObj.items.length;
    if (itemsExist) {
      // Remove the last item's padding
      width -= padding;
      height -= padding;
    }

    // Export the total width and height of the generated canvas
    retObj.properties = {
      width: width,
      height: height
    };

    // After we return the stream and info
    var that = this;
    process.nextTick(function handleNextTick() {
      // If there are no items, return with an empty stream
      var canvas;
      if (!itemsExist) {
        imageStream.push(null);
        return;
      // Otherwise, generate and export our canvas
      } else {
        // Crete our canvas
        canvas = that.engine.createCanvas(width, height);

        // Add the images onto canvas
        try {
          packedObj.items.forEach(function addImage(item) {
            var img = item.meta.img;
            canvas.addImage(img, item.x, item.y);
          });
        } catch (err) {
          imageStream.emit('error', err);
          return;
        }

        // Export our canvas
        var exportStream = canvas.export(exportOpts);
        exportStream.on('error', function forwardError(err) {
          imageStream.emit('error', err);
        });
        exportStream.pipe(imageStream);
      }
    });

    // Return our info
    return retObj;
  }
};

// Export Spritesmith
module.exports = Spritesmith;
