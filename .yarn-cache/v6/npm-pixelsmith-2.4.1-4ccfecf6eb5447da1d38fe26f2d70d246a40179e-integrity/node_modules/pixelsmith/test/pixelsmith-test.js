// Load our dependencies
var assert = require('assert');
var fs = require('fs');
var spritesmithEngineTest = require('spritesmith-engine-test');
var Pixelsmith = require('../');

// Run our test
// DEV: This covers png and jpeg inputs
spritesmithEngineTest.run({
  engine: Pixelsmith,
  engineName: 'pixelsmith'
});

// Define custom tests
var spritesmithUtils = spritesmithEngineTest.spritesmithUtils;
describe('pixelsmith', function () {
  spritesmithUtils.createEngine(Pixelsmith);
  describe('outputting a spritesheet with a custom background', function () {
    var multiplePngImages = spritesmithEngineTest.config.multiplePngImages;
    spritesmithUtils.interpretStringImages(multiplePngImages.filepaths);

    describe('when rendered', function () {
      // Render a gif image
      spritesmithUtils.renderCanvas({
        width: multiplePngImages.width,
        height: multiplePngImages.height,
        coordinateArr: multiplePngImages.coordinateArr,
        exportParams: {
          background: [255, 0, 255, 255],
          format: 'jpeg'
        }
      });

      // Allow for debugging
      if (process.env.TEST_DEBUG) {
        spritesmithUtils.debugResult('debug-background.jpeg');
      }

      it('used the expected background', function () {
        var actualImg = fs.readFileSync(__dirname + '/expected-files/background.jpeg');
        assert.deepEqual(this.result, actualImg);
      });
    });
  });

  // DEV: Written for https://github.com/twolfson/pixelsmith/issues/16
  describe('loading a JPEG with `.png` extension', function () {
    it('outputs a reasonable error', function (done) {
      this.engine.createImage(__dirname + '/test-files/jpeg-wrong-extension.png',
          function handleCreateImage (err, imgs) {
        assert(err.message.match('jpeg-wrong-extension.png'));
        assert(err.stack.match('jpeg-wrong-extension.png'));
        done();
      });
    });
  });
});
