var assert = require('assert');
var less = require('less');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An retina array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.retinaMultipleSprites);

  describe('processed by `spritesheet-templates` into retina LESS', function () {
    testUtils.runTemplater({format: 'less_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/less_retina.less');

    describe('processed by LESS into CSS', function () {
      // Process the LESS
      testUtils.processCss(function processLess (cb) {
        // Add some LESS to our result
        var lessStr = this.result;
        lessStr += [
          '.retina-sprites(@retina-groups);'
        ].join('\n');

        // Render the LESS, assert no errors, and valid CSS
        less.render(lessStr, function (err, result) {
          // Verify there are no braces in the CSS (array string coercion)
          assert.strictEqual(err, null);
          var css = result.css;
          assert.notEqual(css, '');
          assert.strictEqual(css.indexOf(']'), -1);
          // DEV: Repair vendor specific validation issues
          css = css.replace(/\(-webkit-min-device-pixel-ratio: 2\),/g, '');
          // Callback with our CSS
          cb(null, css);
        });
      });

      // Assert against generated CSS
      testUtils.assertValidCss();
    });
  });
});
