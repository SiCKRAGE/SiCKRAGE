var configUtils = require('./utils/config');
var testUtils = require('./utils/test');

describe('An retina array of image positions, dimensions, and names', function () {
  testUtils.setInfo(configUtils.retinaMultipleSprites);

  describe('processed by `spritesheet-templates` into retina CSS', function () {
    testUtils.runTemplater({format: 'css_retina'});
    testUtils.assertOutputMatches(__dirname + '/expected_files/css_retina.css');

    testUtils.runFakeJigsaw();
    it('is valid CSS', function (done) {
      var css = this.result;
      // DEV: Repair vendor specific validation issues
      css = css.replace(/\(-webkit-min-device-pixel-ratio: 2\),/g, '');
      testUtils._assertValidCss(css, done);
    });
  });
});
