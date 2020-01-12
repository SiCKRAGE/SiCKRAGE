var assert = require('assert');
var exec = require('child_process').exec;
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into SASS', function () {
    testUtils.runTemplater({format: 'sass'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/sass.sass');

    testUtils.generateCssFile('\n' + [
      '.feature',
      '  height: $sprite-dash-case-height',
      '  @include sprite-width($sprite-snake-case)',
      '  @include sprite-image($sprite-camel-case)',
      '',
      '.feature2',
      '  @include sprite($sprite-snake-case)',
      '',
      '@include sprites($spritesheet-sprites)'
    ].join('\n'));

    describe('processed by SASS into CSS', function () {
      // Process the SASS
      testUtils.processCss(function processSass (cb) {
        exec('sass ' + this.tmp.path, function (err, css, stderr) {
          // Assert no errors during conversion and save our CSS
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });

      // Assert agains the generated CSS
      testUtils.assertValidCss();
    });
  });
});

describe('An array of 1 image', function () {
  testUtils.setInfo(configUtils.singleSprite);

  describe('processed by `spritesheet-templates` into SASS', function () {
    testUtils.runTemplater({format: 'sass'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/sass-single.sass');

    testUtils.generateCssFile('\n' + [
      '@include sprites($spritesheet-sprites)'
    ].join('\n'));

    describe('processed by SASS into CSS', function () {
      testUtils.processCss(function processSass (cb) {
        exec('sass ' + this.tmp.path, function (err, css, stderr) {
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });
      testUtils.assertValidCss();
    });
  });
});
