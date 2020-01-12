// Load in modules
var assert = require('assert');
var fs = require('fs');
var path = require('path');
var getPixels = require('get-pixels');
var pixelmatch = require('pixelmatch');
var Vinyl = require('vinyl');
var Spritesmith = require('../src/smith.js');

// Set up paths
var spriteDir = path.join(__dirname, 'test_sprites');
var expectedDir = __dirname + '/expected_files';

// DEV: These were unsorted for testing `sort: false` but these work for all tests as is =D
var multipleSprites = [
  path.join(spriteDir, 'sprite1.png'),
  path.join(spriteDir, 'sprite3.png'),
  path.join(spriteDir, 'sprite2.jpg')
];

// Define common utilities
var spritesmithUtils = {
  run: function (params) {
    before(function runFn(done) {
      // Attempt to process the sprites via Spritesmith
      var that = this;
      Spritesmith.run(params, function handleRun(err, result) {
        that.err = err;
        that.result = result;
        done();
      });
    });
    after(function cleanup() {
      delete this.err;
      delete this.result;
    });
  },

  assertNoError: function () {
    return function assertNoErrorFn() {
      assert.strictEqual(this.err, null);
    };
  },

  assertCoordinates: function (filename) {
    return function assertCoordinatesFn() {
      // Load in the coordinates
      var result = this.result;

      // DEV: Write out to actual_files
      if (process.env.TEST_DEBUG) {
        try { fs.mkdirSync(__dirname + '/actual_files'); } catch (e) { /* Ignore error */ }
        fs.writeFileSync(__dirname + '/actual_files/' + filename, JSON.stringify(result.coordinates, null, 4));
      }

      // Normalize the actual coordinates
      // eslint-disable-next-line global-require
      var expectedCoords = require(expectedDir + '/' + filename);
      var actualCoords = result.coordinates;
      var normCoords = {};
      assert(actualCoords, 'Result does not have a coordinates property');

      Object.getOwnPropertyNames(actualCoords).forEach(function (filepath) {
        var file = path.relative(spriteDir, filepath);
        normCoords[file] = actualCoords[filepath];
      });

      // Assert that the returned coordinates deep equal those in the coordinates.json
      assert.deepEqual(expectedCoords, normCoords, 'Actual coordinates do not match expected coordinates');
    };
  },

  assertProps: function (filename) {
    return function assertPropsFn() {
      // Load in the properties
      var result = this.result;

      // DEV: Write out to actual_files
      if (process.env.TEST_DEBUG) {
        try { fs.mkdirSync(__dirname + '/actual_files'); } catch (e) { /* Ignore error */ }
        fs.writeFileSync(__dirname + '/actual_files/' + filename, JSON.stringify(result.properties, null, 4));
      }

      // Assert that the returned properties equals the expected properties
      var actualProps = result.properties;
      // eslint-disable-next-line global-require
      var expectedProps = require(expectedDir + '/' + filename);
      assert.deepEqual(expectedProps, actualProps, 'Actual properties do not match expected properties');
    };
  },

  assertSpritesheet: function (filename) {
    return function assertSpritesheetFn(done) {
      // Load our variables
      var actualImageBuff = this.result.image;
      var expectedFilepath = path.join(expectedDir, filename);

      // DEV: Write out to actual_files
      if (process.env.TEST_DEBUG) {
        try { fs.mkdirSync(__dirname + '/actual_files'); } catch (e) { /* Ignore error */ }
        fs.writeFileSync(__dirname + '/actual_files/' + filename, actualImageBuff);
      }

      // Assert the actual image is close to the expected image
      // DEV: We are using pngjs for decoding/encoding in the library but this is testing one more cycle
      getPixels(actualImageBuff, 'image/png', function handleActualPixels(err, actualImage) {
        if (err) { return done(err); }
        getPixels(expectedFilepath, function handleExpectedPixels(err, expectedImage) {
          if (err) { return done(err); }
          assert.deepEqual(actualImage.shape, expectedImage.shape,
            'Actual image shape does not match expected image shape');
          var numDiffPixels = pixelmatch(actualImage.data, expectedImage.data, null,
            actualImage.shape[0], actualImage.shape[1]);
          assert(numDiffPixels < 10, 'Expected at most 10 pixels to be different but received ' + numDiffPixels);
          done();
        });
      });
    };
  }
};

// Start our tests
describe('An array of sprites', function () {
  describe('when processed via spritesmith', function () {
    spritesmithUtils.run({
      src: multipleSprites
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a binary-tree spritesheet', spritesmithUtils.assertSpritesheet('binaryTree.pixelsmith.png'));
    it('has the proper coordinates', spritesmithUtils.assertCoordinates('binaryTree.coordinates.json'));
    it('has the proper properties', spritesmithUtils.assertProps('binaryTree.properties.json'));
  });

  describe('when converted from left to right', function () {
    spritesmithUtils.run({
      src: multipleSprites,
      algorithm: 'left-right'
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a left-right spritesheet', spritesmithUtils.assertSpritesheet('leftRight.pixelsmith.png'));
    it('has the proper coordinates', spritesmithUtils.assertCoordinates('leftRight.coordinates.json'));
    it('has the proper properties', spritesmithUtils.assertProps('leftRight.properties.json'));
  });

  describe('when provided with a padding parameter', function () {
    spritesmithUtils.run({
      src: multipleSprites,
      algorithm: 'binary-tree',
      padding: 2
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a padded spritesheet', spritesmithUtils.assertSpritesheet('padding.pixelsmith.png'));
    it('has the proper coordinates', spritesmithUtils.assertCoordinates('padding.coordinates.json'));
    it('has the proper properties', spritesmithUtils.assertProps('padding.properties.json'));
  });

  describe('when told not to sort', function () {
    spritesmithUtils.run({
      src: multipleSprites,
      algorithm: 'top-down',
      algorithmOpts: {sort: false}
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders an unsorted spritesheet', spritesmithUtils.assertSpritesheet('unsorted.pixelsmith.png'));
    it('has the proper coordinates', spritesmithUtils.assertCoordinates('unsorted.coordinates.json'));
    it('has the proper properties', spritesmithUtils.assertProps('unsorted.properties.json'));
  });
});

describe('An array of vinyl object sprites', function () {
  describe('when processed via spritesmith', function () {
    spritesmithUtils.run({
      src: multipleSprites.map(function createVinylObject(filepath) {
        return new Vinyl({
          path: filepath,
          contents: fs.readFileSync(filepath)
        });
      })
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a binary-tree spritesheet', spritesmithUtils.assertSpritesheet('binaryTree.pixelsmith.png'));
    it('has the proper coordinates', spritesmithUtils.assertCoordinates('binaryTree.coordinates.json'));
    it('has the proper properties', spritesmithUtils.assertProps('binaryTree.properties.json'));
  });
});

describe('An empty array', function () {
  var emptySprites = [];

  describe('when processed via spritesmith', function () {
    spritesmithUtils.run({
      src: emptySprites
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders an empty spritesheet', function () {
      assert.deepEqual(this.result.image, new Buffer(0));
    });
    it('returns an empty coordinate mapping', function () {
      assert.deepEqual(this.result.coordinates, {});
    });
    it('has the proper properties', spritesmithUtils.assertProps('empty.properties.json'));
  });
});

describe('`spritesmith` using a custom engine via string', function () {
  describe('processing a set of images', function () {
    spritesmithUtils.run({
      src: multipleSprites,
      engine: 'phantomjssmith'
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a spritesheet', spritesmithUtils.assertSpritesheet('binaryTree.phantomjs.png'));
  });
});

describe('`spritesmith` using a custom engine via an object', function () {
  describe('processing a set of images', function () {
    spritesmithUtils.run({
      src: multipleSprites,
      // eslint-disable-next-line global-require
      engine: require('phantomjssmith')
    });

    it('has no errors', spritesmithUtils.assertNoError());
    it('renders a spritesheet', spritesmithUtils.assertSpritesheet('binaryTree.phantomjs.png'));
  });
});

// Edge cases
// Test for https://github.com/twolfson/gulp.spritesmith/issues/22
var canvassmith;
try {
  // eslint-disable-next-line global-require
  canvassmith = require('canvassmith');
} catch (err) { /* Ignore error */ }
var describeIfCanvassmithExists = canvassmith ? describe : describe.skip;
describeIfCanvassmithExists('`spritesmith` using `canvassmith`', function () {
  describe('processing a bad image', function () {
    spritesmithUtils.run({
      src: [path.join(spriteDir, 'malformed.png')],
      engine: 'canvassmith'
    });

    it('calls back with an error', function () {
      assert.notEqual(this.err, null);
    });
  });
});
