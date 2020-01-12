var assert = require('assert');
var exec = require('child_process').exec;
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An retina array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.retinaMultipleSprites);

  describe('processed by `spritesheet-templates` into retina SASS', function () {
    testUtils.runTemplater({format: 'sass_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/sass_retina.sass');

    testUtils.generateCssFile('\n' + [
      '@include retina-sprites($retina-groups)'
    ].join('\n'));

    describe('processed by SASS into CSS', function () {
      // Process the SASS
      testUtils.processCss(function processSass (cb) {
        exec('sass ' + this.tmp.path, function (err, css, stderr) {
          // Assert no errors during conversion and save our CSS
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          // DEV: Repair vendor specific validation issues
          css = css.replace(/\(-webkit-min-device-pixel-ratio: 2\),/g, '');
          cb(err, css);
        });
      });

      // Assert agains the generated CSS
      testUtils.assertValidCss();
    });
  });
});
