var fs = require('fs');
var templater = require('../');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into LESS with `variableNameTransforms`', function () {
    testUtils.runTemplater({
      format: 'less',
      formatOpts: {
        variableNameTransforms: ['underscored', 'toUpperCase']
      }
    });

    testUtils.assertOutputMatches(__dirname + '/expected_files/less-transform.less');
  });
});

// DEV: Legacy test
describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` via custom template with no `variableNameTransforms`', function () {
    before(function addCustomTemplate () {
      var customTemplate = fs.readFileSync(__dirname + '/test_files/transform_custom.template.mustache', 'utf8');
      templater.addMustacheTemplate('transform_custom', customTemplate);
    });
    testUtils.runTemplater({
      format: 'transform_custom'
    });

    testUtils.assertOutputMatches(__dirname + '/expected_files/transform-custom.less');
  });
});
