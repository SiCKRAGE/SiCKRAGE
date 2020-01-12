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
