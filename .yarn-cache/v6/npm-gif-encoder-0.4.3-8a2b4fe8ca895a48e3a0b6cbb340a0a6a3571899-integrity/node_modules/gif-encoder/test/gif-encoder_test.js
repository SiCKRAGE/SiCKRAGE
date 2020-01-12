var assert = require('assert');
var fs = require('fs');

var async = require('async');

var GifEncoder = require('../lib/GIFEncoder.js');
var checkerboardPixels = require('./test-files/checkerboard-pixels.json');

function createGif(height, width) {
  before(function () {
    this.gif = new GifEncoder(height, width);
  });
}

describe('GifEncoder encoding a checkerboard', function () {
  createGif(10, 10);
  before(function () {
    this.gif.writeHeader();
    this.gif.addFrame(checkerboardPixels);
    this.gif.finish();
  });
  before(function (done) {
    this.gif.once('readable', done);
  });

  it('generates the expected bytes', function () {
    // TODO: Output canvas to a file, perceptual diff GIF to canvas output =3
    // Grab the expected and actual content
    var expectedBytes = fs.readFileSync(__dirname + '/expected-files/checkerboard.gif');
    var actualBytes = this.gif.read();

    // DEV: Write out actual file to expected file
    if (process.env.DEBUG_TEST) {
      try { fs.mkdirSync(__dirname + '/actual-files'); } catch (e) {}
      fs.writeFileSync(__dirname + '/actual-files/checkerboard.gif', actualBytes);
    }

    // Assert the expected matches the actual content
    assert.deepEqual(expectedBytes, actualBytes);
  });
});

describe('GifEncoder encoding a multi-framed checkerboard', function () {
  createGif(10, 10);
  before(function () {
    this.gif.writeHeader();
    this.gif.setDelay(500);
    this.gif.setRepeat(0);
    this.gif.addFrame(checkerboardPixels);
    this.gif.addFrame(require('./test-files/inverse-checkerboard-pixels.json'));
    this.gif.finish();
  });
  before(function (done) {
    this.gif.once('readable', done);
  });

  it('generates the expected bytes', function () {
    var expectedBytes = fs.readFileSync(__dirname + '/expected-files/alternating-checkerboard.gif');
    var actualBytes = this.gif.read();
    if (process.env.DEBUG_TEST) {
      try { fs.mkdirSync(__dirname + '/actual-files'); } catch (e) {}
      fs.writeFileSync(__dirname + '/actual-files/alternating-checkerboard.gif', actualBytes);
    }
    assert.deepEqual(expectedBytes, actualBytes);
  });
});

describe('GifEncoder encoding an overly large, underly read checkerboard', function () {
  createGif(10, 10);
  before(function (done) {
    var that = this;
    this.gif.writeHeader();
    this.gif.on('error', function saveError (err) {
      that.error = err;
    });

    // Write out a new frame until we encounter an error
    // DEV: This is async so mocha can time us out
    async.until(function errorHasOccurred () {
      return that.error;
    }, function addNewFrame(cb) {
      process.nextTick(function () {
        that.gif.addFrame(checkerboardPixels);
        cb();
      });
    }, done);
  });

  it('emits an error', function () {
    assert.notEqual(this.error, undefined);
  });
});
