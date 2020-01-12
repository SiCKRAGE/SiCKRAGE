var assert = require('assert');
var fs = require('fs');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');
var pkg = require('../package.json');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  function assertValidJson() {
    it('is valid JSON', function () {
      var result = this.result;
      assert.doesNotThrow(function () {
        JSON.parse(result);
      });
    });
  }

  describe('processed by `spritesheet-templates` into JSON', function () {
    testUtils.runTemplater({format: 'json_texture'});

    it('matches as expected the map of texture info, similar to TexturePacker', function () {
      var expected = fs.readFileSync(__dirname + '/expected_files/json_texture.json', 'utf8');
      expected = expected.replace('__VERSION__', pkg.version);
      assert.strictEqual(this.result, expected);
    });

    assertValidJson();
  });
});
