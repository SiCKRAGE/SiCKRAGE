// Load in our dependencies
var fs = require('fs');
var templater = require('../../');

// Register our new template
var scssMinimalHandlebars = fs.readFileSync(__dirname + '/scss-minimal.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss-minimal', scssMinimalHandlebars);

// Run our templater
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
}, {format: 'scss-minimal'}));
