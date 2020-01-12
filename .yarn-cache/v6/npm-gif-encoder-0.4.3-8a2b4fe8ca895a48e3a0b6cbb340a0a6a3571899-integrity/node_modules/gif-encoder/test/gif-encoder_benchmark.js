var imageUtils = require('./utils/image');
var GifEncoder = require('../');

describe('A GifEncoder', function () {
  // DEV: With byte-by-byte buffers, we run into a process.nextTick overflow with all the events
  // Thus, frame based buffers win by default
  describe('encoding a bunch of frames to `data` events', function () {
    before(function createGifEncoder () {
      this.gif = new GifEncoder(200, 200);
      this.gif.writeHeader();

      // Pipe output to nowhere
      // DEV: We should test .read() but we already have frame based buffers as our winner
      this.gif.on('data', function () {});
    });
    imageUtils.load('medium-size.png');
    before(function encodeABunchOfFrames () {
      var startTime = Date.now();
      var i = 500;
      var gif = this.gif;
      var pixels = this.pixels;
      while (i--) {
        gif.addFrame(pixels);
      }
      var endTime = Date.now();
      this.totalTime = endTime - startTime;
    });

    it('can do so efficiently', function () {
      // DEV: We should move to ops/second for other benchmarks but this test has a win-by-default
      // Medium size x 500 frames 13088 ms for frame based buffers
      // Medium size x 500 frames 14245 ms for byte by byte
      console.log('Medium size x 500 frames', this.totalTime + ' ms');
    });
  });
});