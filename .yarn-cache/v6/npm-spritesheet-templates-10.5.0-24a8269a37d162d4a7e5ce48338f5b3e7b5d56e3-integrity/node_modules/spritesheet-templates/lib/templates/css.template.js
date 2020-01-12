// Load in local modules
var fs = require('fs');
var handlebars = require('handlebars');
var tmpl = fs.readFileSync(__dirname + '/css.template.handlebars', 'utf8');

// Register the CSS as a partial for extension
handlebars.registerPartial('css', tmpl);

// Define our css template fn ({sprites, options}) -> css
function cssTemplate(data) {
  // Localize parameters
  var sprites = data.sprites;
  var options = data.options;

  // Fallback class naming function
  var selectorFn = options.cssSelector || function defaultCssClass (sprite) {
    return '.icon-' + sprite.name;
  };

  // Add class to each of the options
  sprites.forEach(function saveClass (sprite) {
    sprite.selector = selectorFn(sprite);
  });

  // Render and return CSS
  var css = handlebars.compile(tmpl)(data);
  return css;
}

// Export our CSS template
module.exports = cssTemplate;
