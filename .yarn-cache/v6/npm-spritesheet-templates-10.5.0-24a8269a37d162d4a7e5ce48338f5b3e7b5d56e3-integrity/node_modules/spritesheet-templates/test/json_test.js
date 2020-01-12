var assert = require('assert');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

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
    testUtils.runTemplater({format: 'json'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/json.json');

    assertValidJson();
  });

  describe('processed by `spritesheet-templates` into an array', function () {
    testUtils.runTemplater({format: 'json_array'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/json_array.json');

    assertValidJson();
  });
});
