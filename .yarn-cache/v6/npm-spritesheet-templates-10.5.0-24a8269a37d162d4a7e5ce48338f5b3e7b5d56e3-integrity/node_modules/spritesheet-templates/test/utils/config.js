exports.singleSprite = {
  sprites: [{
    name: 'sprite-dash-case', x: 0, y: 0, width: 10, height: 20
  }],
  spritesheet: {
    width: 10, height: 20, image: 'nested/dir/spritesheet.png'
  }
};

exports.multipleSprites = {
  sprites: [{
    name: 'sprite-dash-case', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'sprite_snake_case', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'spriteCamelCase', x: 30, y: 50, width: 50, height: 50
  }],
  spritesheet: {
    width: 80, height: 100, image: 'nested/dir/spritesheet.png'
  }
};

exports.retinaMultipleSprites = {
  sprites: [{
    name: 'sprite-dash-case', x: 0, y: 0, width: 10, height: 20
  }, {
    name: 'sprite_snake_case', x: 10, y: 20, width: 20, height: 30
  }, {
    name: 'spriteCamelCase', x: 30, y: 50, width: 50, height: 50
  }],
  spritesheet: {
    width: 80, height: 100, image: 'nested/dir/spritesheet.png'
  },
  retina_sprites: [{
    name: 'sprite-dash-case@2x', x: 0, y: 0, width: 20, height: 40
  }, {
    name: 'sprite_snake_case@2x', x: 20, y: 40, width: 40, height: 60
  }, {
    name: 'spriteCamelCase@2x', x: 60, y: 100, width: 100, height: 100
  }],
  retina_spritesheet: {
    width: 160, height: 200, image: 'nested/dir/spritesheet@2x.png'
  },
  retina_groups: [{
    name: 'sprite-dash-case',
    index: 0
  }, {
    name: 'sprite_snake_case',
    index: 1
  }, {
    name: 'spriteCamelCase',
    index: 2
  }]
};
