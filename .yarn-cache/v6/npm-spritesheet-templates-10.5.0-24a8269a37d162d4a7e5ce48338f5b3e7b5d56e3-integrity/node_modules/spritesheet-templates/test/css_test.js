var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into CSS', function () {
    testUtils.runTemplater(null);
    testUtils.assertOutputMatches(__dirname + '/expected_files/css.css');

    testUtils.runFakeJigsaw();
    it('is valid CSS', function (done) {
      var css = this.result;
      testUtils._assertValidCss(css, done);
    });
  });
});

// Edge case test for filepaths with quotes
describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo({
    sprites: configUtils.multipleSprites.sprites,
    spritesheet: {
      width: configUtils.multipleSprites.spritesheet.width,
      height: configUtils.multipleSprites.spritesheet.height,
      image: 'nested/dir/( \'")/spritesheet.png'
    }
  });

  describe('processed by `spritesheet-templates` into CSS with an escapable selector', function () {
    testUtils.runTemplater(null);
    testUtils.assertOutputMatches(__dirname + '/expected_files/css-quote-filepath.css');

    testUtils.runFakeJigsaw();
    it('is valid CSS', function (done) {
      var css = this.result;
      testUtils._assertValidCss(css, done);
    });
  });
});

// Edge case test for https://github.com/Ensighten/grunt-spritesmith/issues/104
describe('An array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.multipleSprites);

  describe('processed by `spritesheet-templates` into CSS with an escapable selector', function () {
    testUtils.runTemplater({
      formatOpts: {
        cssSelector: function (sprite) {
          return '.hello > .icon-' + sprite.name;
        }
      }
    });
    testUtils.assertOutputMatches(__dirname + '/expected_files/css-html-selector.css');

    testUtils.runFakeJigsaw();
    it('is valid CSS', function (done) {
      var css = this.result;
      testUtils._assertValidCss(css, done);
    });
  });
});
