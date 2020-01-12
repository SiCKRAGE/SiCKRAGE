// Load in our dependencies
var assert = require('assert');
var fs = require('fs');
var _ = require('underscore');
var _s = require('underscore.string');
var handlebars = require('handlebars');
var handlebarsLayouts = require('handlebars-layouts');
var jsonContentDemux = require('json-content-demux');

// Allow for layouts to occur on `handlebars` templates
handlebarsLayouts.register(handlebars);

/**
 * @param {Object} data Container for data for template
 * @param {Object[]} data.sprites Array of objects with coordinate data about each sprite on the spritesheet
 * @param {String} data.sprites.*.name Name to use for the image
 * @param {Number} data.sprites.*.x Horizontal coordinate of top-left corner of image
 * @param {Number} data.sprites.*.y Vertical coordinate of top-left corner of image
 * @param {Number} data.sprites.*.width Horizontal length of image in pixels
 * @param {Number} data.sprites.*.height Vertical length of image in pixels
 * @param {Object} data.spritesheet Information about spritesheet
 * @param {Number} data.spritesheet.width Horizontal length of image in pixels
 * @param {Number} data.spritesheet.height Vertical length of image in pixels
 * @param {Number} data.spritesheet.image URL to use for spritesheet
 * @param {Object} [data.spritesheet_info]  Optional container for metadata about `spritesheet` and its representation
 * @param {String} [data.spritesheet_info.name="spritesheet"] Prefix to use for spritesheet related variables
 * @param {Object[]} [data.retina_sprites] Optional array of objects with coordinate data about retina sprites.
     Signature is same as `data.sprites`
 * @param {Object[]} [data.retina_spritesheet] Optional information about retina spritesheet.
     Signature is same as `data.spritesheet`
 * @param {Object} [data.retina_spritesheet_info]  Optional container for metadata about `retina_spritesheet`
     Signature is same as `data.spritesheet_info`
 * @param {String} [data.retina_spritesheet_info.name="spritesheet-retina"] Prefix to use for retina spritesheet var
 * @param {String} [data.retina_groups] Optional Array of objects that maps to normal and retina sprites
 * @param {String} [data.retina_groups.*.name] Name to use for the mapping
 * @param {Number} [data.retina_groups.*.index] Index to grab sprites from in `sprites`/`retina_sprites`
 * @param {Object} [data.retina_groups_info] Optional information about retina groups
 * @param {String} [data.retina_groups_info.name="retina-groups"] Name to use for retina groups variable
 * @param {Object} [options] Optional settings
 * @param {String} [options.format="css"] Format to generate output in
 * @param {Mixed} [options.formatOpts={}] Options to pass through to the formatter
 */
function templater(data, options) {
  // Assert we were given sprites and spritesheet
  assert(data, '`spritesheet-templates` expected to receive "data" but did not. Please provide it.');
  // DEV: Support `data.items` for legacy purposes
  data.sprites = data.sprites || data.items;
  assert(data.sprites, '`spritesheet-templates` expected to receive "data.sprites" but did not. ' +
    'Please provide it.');
  assert(data.spritesheet, '`spritesheet-templates` expected to receive "data.spritesheet" but did not. ' +
    'Please provide it.');

  // Fallback and localize options
  options = options || {};
  var format = options.format || 'css';
  var template = templater.templates[format];

  // Assert that the template exists
  assert(template, 'The templater format "' + format + '" could not be found. Please make sure to either add ' +
    'it via addTemplate or the spelling is correct.');

  // Deep clone the sprites and spritesheet
  var sprites = JSON.parse(JSON.stringify(data.sprites));
  var spritesheet = JSON.parse(JSON.stringify(data.spritesheet));
  // DEV: We have `spritesheet_info` which is the object replacement option for `spritesheetName`
  var spritesheetInfo = data.spritesheet_info ? JSON.parse(JSON.stringify(data.spritesheet_info)) : {};
  spritesheetInfo.name = spritesheetInfo.name || options.spritesheetName || 'spritesheet';
  // DEV: For deprecation purposes, backfill `name` onto `spritesheet`
  spritesheet.name = spritesheetInfo.name;

  // Add on extra data to spritesheet and each sprite
  templater.escapeImage(spritesheet);
  templater.ensureTemplateVariables(spritesheet);
  sprites.forEach(function addExtraData (sprite) {
    templater.addSpritesheetProperties(sprite, spritesheet);
    templater.ensureTemplateVariables(sprite);
  });

  // If we have retina parameters
  var retinaSprites;
  var retinaSpritesheet;
  var retinaSpritesheetInfo;
  var retinaGroups;
  var retinaGroupsInfo;
  if (data.retina_sprites || data.retina_spritesheet || data.retina_groups) {
    // Verify we have all the data
    assert(data.retina_sprites && data.retina_spritesheet && data.retina_groups,
      'Expected `data.retina_sprites`, `data.retina_spritesheet`, and `data.retina_groups` to be provided. ' +
      'However, at least one of them was missing. Please provide all of them.');

    // Collect, clone, and normalize our data
    retinaSprites = JSON.parse(JSON.stringify(data.retina_sprites));
    retinaSpritesheet = JSON.parse(JSON.stringify(data.retina_spritesheet));
    retinaSpritesheetInfo = data.retina_spritesheet_info ?
      JSON.parse(JSON.stringify(data.retina_spritesheet_info)) : {};
    retinaSpritesheetInfo.name = retinaSpritesheetInfo.name || 'retina-spritesheet';
    retinaGroups = JSON.parse(JSON.stringify(data.retina_groups));
    retinaGroupsInfo = data.retina_groups_info ? JSON.parse(JSON.stringify(data.retina_groups_info)) : {};
    retinaGroupsInfo.name = retinaGroupsInfo.name || 'retina-groups';

    // Map groups to their normal/retina counterparts
    // DEV: If `group.index` ever needs to split on a per-normal/retina basis, add `group.normal_index/retina_index`
    retinaGroups.forEach(function getRetinaGroupSprites (retinaGroup) {
      retinaGroup.normal = sprites[retinaGroup.index];
      retinaGroup.retina = retinaSprites[retinaGroup.index];
    });

    // Define normalized variables for retina sprites and its spritesheet (e.g. `px`)
    templater.escapeImage(retinaSpritesheet);
    templater.ensureTemplateVariables(retinaSpritesheet);
    retinaSprites.forEach(function addExtraData (retinaSprite) {
      templater.addSpritesheetProperties(retinaSprite, retinaSpritesheet);
      templater.ensureTemplateVariables(retinaSprite);
    });
  }

  // Process the data via the template
  var retVal = template({
    // DEV: Output `items` for supporting legacy templates
    items: sprites,
    sprites: sprites,
    spritesheet: spritesheet,
    // DEV: Output `spritesheet_name` for supporting legacy templates
    spritesheet_name: spritesheet.name,
    spritesheet_info: spritesheetInfo,
    // Add in retina info
    retina_sprites: retinaSprites,
    retina_spritesheet: retinaSpritesheet,
    retina_spritesheet_info: retinaSpritesheetInfo,
    retina_groups: retinaGroups,
    retina_groups_info: retinaGroupsInfo,
    options: options.formatOpts || {}
  });

  // Return the output
  return retVal;
}

// Helper function to escape image path
templater.escapeImage = function (spritesheet) {
  // Escape the quotes, parentheses, and whitespace
  // http://www.w3.org/TR/CSS21/syndata.html#uri
  var img = spritesheet.image;
  var escapedImg = img.replace(/['"\(\)\s]/g, function encodeCssUri (chr) {
    return '%' + chr.charCodeAt(0).toString(16);
  });
  spritesheet.escaped_image = escapedImg;
};

// Helper function to add spritesheet info
templater.addSpritesheetProperties = function (sprite, spritesheet) {
  // Save spritesheet info
  sprite.image = spritesheet.image;
  sprite.escaped_image = spritesheet.escaped_image;
  sprite.total_width = spritesheet.width;
  sprite.total_height = spritesheet.height;
};

// Helper function to ensure offset values exist as well as values with pixels in the name
templater.ensureTemplateVariables = function (item) {
  // Guarantee offsets exist
  if (item.x !== undefined) {
    item.offset_x = -item.x;
  }
  if (item.y !== undefined) {
    item.offset_y = -item.y;
  }

  // Create a px namespace
  var px = {};
  item.px = px;

  // For each of the x, y, offset_x, offset_y, height, width, add a px after that
  ['x', 'y', 'offset_x', 'offset_y', 'height', 'width', 'total_height', 'total_width'].forEach(function (key) {
    if (item[key] !== undefined) {
      px[key] = item[key] + 'px';
    }
  });
};

templater.ensureHandlebarsVariables = function (item, transformFn) {
  // Define strings in the appropriate case
  item.strings = {};

  // If we have a name, add on name keys
  if (item.name) {
    // Replace names such that they are safe for variables
    //   e.g. icon-home@2x -> icon-home-2x
    var escapedName = item.name.replace(/[^\-_0-9a-zA-Z]+/g, '-');
    _.extend(item.strings, {
      // icon-home
      name: transformFn(escapedName),
      // icon-home-name
      name_name: transformFn(escapedName + '-name'),
      // icon-home-x
      name_x: transformFn(escapedName + '-x'),
      // icon-home-y
      name_y: transformFn(escapedName + '-y'),
      // icon-home-offset-x
      name_offset_x: transformFn(escapedName + '-offset-x'),
      // icon-home-offset-y
      name_offset_y: transformFn(escapedName + '-offset-y'),
      // icon-home-width
      name_width: transformFn(escapedName + '-width'),
      // icon-home-height
      name_height: transformFn(escapedName + '-height'),
      // icon-home-total-width
      name_total_width: transformFn(escapedName + '-total-width'),
      // icon-home-total-height
      name_total_height: transformFn(escapedName + '-total-height'),
      // icon-home-image
      name_image: transformFn(escapedName + '-image'),
      // icon-home-sprites
      name_sprites: transformFn(escapedName + '-sprites'),
      // icon-home-group
      name_group: transformFn(escapedName + '-group'),
      // icon-home-group-name
      name_group_name: transformFn(escapedName + '-group-name'),
      // icon-home-normal
      name_normal: transformFn(escapedName + '-normal'),
      // icon-home-retina
      name_retina: transformFn(escapedName + '-retina')
    });
  }

  // Bare strings for maps
  _.extend(item.strings, {
    bare_name: transformFn('name'),
    bare_x: transformFn('x'),
    bare_y: transformFn('y'),
    bare_offset_x: transformFn('offset-x'),
    bare_offset_y: transformFn('offset-y'),
    bare_width: transformFn('width'),
    bare_height: transformFn('height'),
    bare_total_width: transformFn('total-width'),
    bare_total_height: transformFn('total-height'),
    bare_image: transformFn('image'),
    bare_sprites: transformFn('sprites'),
    bare_group: transformFn('group'),
    bare_group_name: transformFn('group-name'),
    bare_normal: transformFn('normal'),
    bare_retina: transformFn('retina')
  });
};

// Add template store and helper methods to add new templates
templater.templates = {};
templater.addTemplate = function (name, fn) {
  templater.templates[name] = fn;
};
templater.addHandlebarsTemplate = function (name, tmplStr) {
  // Break up the template and default options
  var tmplObj = jsonContentDemux(tmplStr);
  var defaults = tmplObj.json || {};
  var tmpl = tmplObj.content;

  // Generate a function which processes objects through the handlebars template
  function templateFn(data) {
    // Set up the defaults for the data
    _.defaults(data.options, defaults);

    // If we want to transform our variables, then transform them
    var transformFn = _.identity;
    var variableNameTransforms = data.options.variableNameTransforms;
    if (variableNameTransforms) {
      assert(Array.isArray(variableNameTransforms),
        '`options.variableNameTransforms` was expected to be an array but it was not');
      transformFn = function (str) {
        var strObj = _s(str);
        variableNameTransforms.forEach(function runTransform (transformKey) {
          strObj = strObj[transformKey]();
        });
        return strObj.value();
      };
    }

    // Generate strings for our variables
    templater.ensureHandlebarsVariables(data, transformFn);
    templater.ensureHandlebarsVariables(data.spritesheet, transformFn);
    templater.ensureHandlebarsVariables(data.spritesheet_info, transformFn);
    data.sprites.forEach(function addHandlebarsVariables (sprite) {
      templater.ensureHandlebarsVariables(sprite, transformFn);
    });

    // If we have retina data, generate strings for it as well
    if (data.retina_sprites) {
      data.retina_sprites.forEach(function addHandlebarsVariables (retinaSprite) {
        templater.ensureHandlebarsVariables(retinaSprite, transformFn);
      });
    }
    if (data.retina_spritesheet_info) {
      templater.ensureHandlebarsVariables(data.retina_spritesheet_info, transformFn);
    }
    if (data.retina_groups) {
      data.retina_groups.forEach(function addHandlebarsVariables (retinaGroup) {
        templater.ensureHandlebarsVariables(retinaGroup, transformFn);
      });
    }
    if (data.retina_groups_info) {
      templater.ensureHandlebarsVariables(data.retina_groups_info, transformFn);
    }

    // Render our template
    var retStr = handlebars.compile(tmpl)(data);
    return retStr;
  }

  // Save the template to our collection as well as handlebars for inheritance
  handlebars.registerPartial(name, tmpl);
  templater.addTemplate(name, templateFn);
};
templater.addMustacheTemplate = templater.addHandlebarsTemplate;

// Add in the templates from templates
var templatesDir = __dirname + '/templates';

templater.addTemplate('json', require(templatesDir + '/json.template.js'));
templater.addTemplate('json_array', require(templatesDir + '/json_array.template.js'));
templater.addTemplate('css', require(templatesDir + '/css.template.js'));

templater.addTemplate('json_texture', require(templatesDir + '/json_texture.template.js'));

var stylusHandlebars = fs.readFileSync(templatesDir + '/stylus.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('stylus', stylusHandlebars);

var lessHandlebars = fs.readFileSync(templatesDir + '/less.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('less', lessHandlebars);

var sassHandlebars = fs.readFileSync(templatesDir + '/sass.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('sass', sassHandlebars);

var scssHandlebars = fs.readFileSync(templatesDir + '/scss.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss', scssHandlebars);

var scssMapsHandlebars = fs.readFileSync(templatesDir + '/scss_maps.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss_maps', scssMapsHandlebars);

// Add retina templates :sparkles:
templater.addTemplate('json_retina', require(templatesDir + '/json_retina.template.js'));
templater.addTemplate('json_array_retina', require(templatesDir + '/json_array_retina.template.js'));
templater.addTemplate('css_retina', require(templatesDir + '/css_retina.template.js'));

var stylusRetinaHandlebars = fs.readFileSync(templatesDir + '/stylus_retina.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('stylus_retina', stylusRetinaHandlebars);

var lessRetinaHandlebars = fs.readFileSync(templatesDir + '/less_retina.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('less_retina', lessRetinaHandlebars);

var sassRetinaHandlebars = fs.readFileSync(templatesDir + '/sass_retina.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('sass_retina', sassRetinaHandlebars);

var scssRetinaHandlebars = fs.readFileSync(templatesDir + '/scss_retina.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss_retina', scssRetinaHandlebars);

var scssMapsRetinaHandlebars = fs.readFileSync(templatesDir + '/scss_maps_retina.template.handlebars', 'utf8');
templater.addHandlebarsTemplate('scss_maps_retina', scssMapsRetinaHandlebars);

// Expose helper registration on `templater`
templater.registerHandlebarsHelper = function (name, helperFn) {
  handlebars.registerHelper(name, helperFn);
};

// Expose templater
module.exports = templater;
