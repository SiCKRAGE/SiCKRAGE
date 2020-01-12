var assert = require('assert');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.retinaMultipleSprites);

  function assertValidJson() {
    it('is valid JSON', function () {
      var result = this.result;
      assert.doesNotThrow(function () {
        JSON.parse(result);
      });
    });
  }

  describe('processed by `spritesheet-templates` into retina JSON', function () {
    testUtils.runTemplater({format: 'json_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/json_retina.json');

    assertValidJson();
  });

  describe('processed by `spritesheet-templates` into an retina array', function () {
    testUtils.runTemplater({format: 'json_array_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/json_array_retina.json');

    assertValidJson();
  });
});
