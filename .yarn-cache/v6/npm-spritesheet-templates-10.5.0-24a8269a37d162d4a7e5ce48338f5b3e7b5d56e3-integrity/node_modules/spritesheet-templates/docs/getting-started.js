// Load in dependencies
var templater = require('../');

// Render spritesheet information into Stylus variables/mixins
console.log(templater({
  sprites: [{
    name: 'github', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'twitter', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'rss', x: 30, y: 50, width: 50, height: 50
  }],
  spritesheet: {
    width: 80, height: 100, image: 'url/path/to/spritesheet.png'
  }
}, {format: 'stylus'}));
