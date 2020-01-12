// Load in our dependencies
var templater = require('../../');

// Run our templater
console.log(templater({
  sprites: [{
    name: 'github', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'twitter', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'rss', x: 30, y: 50, width: 50, height: 50
  }],
  // Note that the retina sprites are in the same order as `sprites`
  retina_sprites: [{
    name: 'github@2x', x: 0, y: 0, width: 20, height: 40
  }, {
    name: 'twitter@2x', x: 20, y: 40, width: 40, height: 60
  }, {
    name: 'rss@2x', x: 60, y: 100, width: 100, height: 100
  }],
  spritesheet: {
    width: 80, height: 100, image: 'url/path/to/spritesheet.png'
  },
  retina_spritesheet: {
    width: 160, height: 200, image: 'url/path/to/spritesheet@2x.png'
  },
  retina_groups: [{
    name: 'github', index: 0
  }, {
    name: 'twitter', index: 1
  }, {
    name: 'rss', index: 2
  }]
}, {format: 'scss_retina'}));
