function jsonTemplate(data) {
  // Convert sprites from an array into an object
  var sprites = data.sprites;
  var spriteObj = {};
  sprites.forEach(function (sprite) {
    // Grab the name and store the sprite under it
    var name = sprite.name;
    spriteObj[name] = sprite;

    // Delete the name from the sprite
    delete sprite.name;
  });

  // Stringify the spriteObj
  var retStr = JSON.stringify(spriteObj, null, 4);

  // Return the stringified JSON
  return retStr;
}

// Export our JSON template
module.exports = jsonTemplate;
