function jsonArrayTemplate(data) {
  // Stringify the array of sprites
  var sprites = data.sprites;
  var retStr = JSON.stringify(sprites, null, 4);

  // Return the stringified JSON
  return retStr;
}

// Export our JSON template
module.exports = jsonArrayTemplate;
