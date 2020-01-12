var assert = require('assert');
var less = require('less');
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into LESS', function () {
    testUtils.runTemplater({format: 'less'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/less.less');

    describe('processed by LESS into CSS', function () {
      // Process the LESS
      testUtils.processCss(function processLess (cb) {
        // Add some LESS to our result
        var lessStr = this.result;
        lessStr += [
          '.feature {',
          '  height: @sprite-dash-case-height;',
          '  .sprite-width(@sprite-snake-case);',
          '  .sprite-image(@sprite-camel-case);',
          '}',
          '',
          '.feature2 {',
          '  .sprite(@sprite-snake-case);',
          '}',
          '',
          '.sprites(@spritesheet-sprites);'
        ].join('\n');

        // Render the LESS, assert no errors, and valid CSS
        less.render(lessStr, function (err, result) {
          // Verify there are no braces in the CSS (array string coercion)
          assert.strictEqual(err, null);
          var css = result.css;
          assert.notEqual(css, '');
          assert.strictEqual(css.indexOf(']'), -1);

          // Callback with our CSS
          cb(null, css);
        });
      });

      // Assert against generated CSS
      testUtils.assertValidCss();
    });
  });
});
