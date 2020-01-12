var assert = require('assert');
var stylus = require('stylus');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An retina array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.retinaMultipleSprites);

  describe('processed by `spritesheet-templates` into retina Stylus', function () {
    testUtils.runTemplater({format: 'stylus_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/stylus_retina.styl');

    describe('processed by Stylus into CSS', function () {
      // Process the Stylus
      testUtils.processCss(function processStylus (cb) {
        // Add some stylus which hooks into our result
        var styl = this.result;
        styl += [
          'retinaSprites($retina_groups)'
        ].join('\n');

        // Render the stylus
        stylus.render(styl, function handleStylus (err, css) {
          // Assert no errors, CSS was generated, and callback
          assert.strictEqual(err, null);
          assert.notEqual(css, '');
          // DEV: Repair vendor specific validation issues
          css = css.replace(/\(-webkit-min-device-pixel-ratio: 2\),/g, '');
          cb(null, css);
        });
      });

      testUtils.assertValidCss();
    });
  });
});
