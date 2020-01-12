var assert = require('assert');
var exec = require('child_process').exec;
var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into SCSS', function () {
    testUtils.runTemplater({format: 'scss'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/scss.scss');

    testUtils.generateCssFile('\n' + [
      '.feature {',
      '  height: $sprite-dash-case-height;',
      '  @include sprite-width($sprite-snake-case);',
      '  @include sprite-image($sprite-camel-case);',
      '}',
      '',
      '.feature2 {',
      '  @include sprite($sprite-snake-case);',
      '}',
      '',
      '@include sprites($spritesheet-sprites);'
    ].join('\n'));

    describe('processed by `sass --scss` (ruby) into CSS', function () {
      // Process the SCSS
      testUtils.processCss(function processScss (cb) {
        exec('sass --scss ' + this.tmp.path, function (err, css, stderr) {
          // Assert no errors during conversion
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });

      // Assert agains the generated CSS
      testUtils.assertValidCss();
    });

    describe('processed by `sassc` (libsass) into CSS', function () {
      // Process the SCSS
      testUtils.processCss(function processScss (cb) {
        exec('sassc ' + this.tmp.path, function (err, css, stderr) {
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });
      testUtils.assertValidCss();
    });
  });
});

describe('An array of 1 image', function () {
  testUtils.setInfo(configUtils.singleSprite);

  describe('processed by `spritesheet-templates` into SCSS', function () {
    testUtils.runTemplater({format: 'scss'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/scss-single.scss');

    testUtils.generateCssFile('\n' + [
      '@include sprites($spritesheet-sprites);'
    ].join('\n'));

    describe('processed by `sass --scss` (ruby) into CSS', function () {
      testUtils.processCss(function processScss (cb) {
        exec('sass --scss ' + this.tmp.path, function (err, css, stderr) {
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });
      testUtils.assertValidCss();
    });

    describe('processed by `sassc` (libsass) into CSS', function () {
      testUtils.processCss(function processScss (cb) {
        exec('sassc ' + this.tmp.path, function (err, css, stderr) {
          assert.strictEqual(stderr, '');
          assert.notEqual(css, '');
          cb(err, css);
        });
      });
      testUtils.assertValidCss();
    });
  });
});
