// Load in dependencies
var fs = require('fs');
var Spritesmith = require('../');

// Generate our spritesheet
var spritesmith = new Spritesmith();
spritesmith.createImages([
  __dirname + '/fork.png',
  __dirname + '/github.png',
  __dirname + '/twitter.png'
], function handleImages (err, images) {
  // If there was an error, throw it
  if (err) {
    throw err;
  }

  // Otherwise, log info
  console.log(images[0].width); // Width of image
  console.log(images[0].height); // Height of image

  // Create our result
  var result = spritesmith.processImages(images);
  console.log(JSON.stringify(result.coordinates, null, 2)); // Object mapping filename to {x, y, width, height} of image
  console.log(JSON.stringify(result.properties, null, 2)); // Object with metadata about spritesheet {width, height}

  // and output the image
  result.image.pipe(fs.createWriteStream(__dirname + '/getting-started-stream.png'));
});
