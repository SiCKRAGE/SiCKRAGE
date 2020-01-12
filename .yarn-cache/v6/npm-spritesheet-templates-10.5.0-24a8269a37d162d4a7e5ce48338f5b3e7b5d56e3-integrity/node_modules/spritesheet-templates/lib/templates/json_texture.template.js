var pkg = require('../../package.json');
var path = require('path');

function jsonTextureTemplate(data) {
  var spriteObj = {};

  // Create frame data for each sprite.
  spriteObj.frames = {};

  data.sprites.forEach(function saveSprite (sprite) {
    var frameName;
    var entry = {
      frame: {
        x: sprite.x,
        y: sprite.y,
        w: sprite.width,
        h: sprite.height
      }
    };

    if (sprite.frame_name) {
      frameName = sprite.frame_name;
    } else if (sprite.source_image) {
      frameName = path.basename(sprite.source_image);
    } else {
      frameName = sprite.name;
    }

    spriteObj.frames[frameName] = entry;
  });

  // Create the meta data.
  spriteObj.meta = {
    app: pkg.name,
    version: pkg.version,
    image: data.spritesheet.image,
    scale: 1,
    size: {
      w: data.spritesheet.width,
      h: data.spritesheet.height
    }
  };

  // Stringify the spriteObj
  var retStr = JSON.stringify(spriteObj, null, 4);

  // Return the stringified JSON
  return retStr;
}

// Export our JSON texture template
module.exports = jsonTextureTemplate;
