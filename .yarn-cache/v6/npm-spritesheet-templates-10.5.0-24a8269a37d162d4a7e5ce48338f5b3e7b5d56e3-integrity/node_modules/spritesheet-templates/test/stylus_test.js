var assert = require('assert');
var stylus = require('stylus');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into Stylus', function () {
    testUtils.runTemplater({format: 'stylus'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/stylus.styl');

    describe('processed by Stylus into CSS', function () {
      // Process the Stylus
      testUtils.processCss(function processStylus (cb) {
        // Add some stylus which hooks into our result
        var styl = this.result;
        styl += [
          '.feature',
          '  height: $sprite_dash_case_height;',
          '  spriteWidth($sprite_snake_case)',
          '  spriteImage($sprite_camel_case)',
          '',
          '.feature2',
          '  sprite($sprite_snake_case)',
          '',
          'sprites($spritesheet_sprites)'
        ].join('\n');

        // Render the stylus
        stylus.render(styl, function handleStylus (err, css) {
          // Assert no errors, CSS was generated, and callback
          assert.strictEqual(err, null);
          assert.notEqual(css, '');
          cb(null, css);
        });
      });

      testUtils.assertValidCss();
    });
  });
});
