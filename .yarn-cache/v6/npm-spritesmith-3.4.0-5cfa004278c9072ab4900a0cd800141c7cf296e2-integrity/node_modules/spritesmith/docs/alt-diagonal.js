// Load in dependencies
var fs = require('fs');
var Spritesmith = require('../');

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
