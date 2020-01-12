var redtape = require('redtape'),
    fs = require('fs'),
    path = require('path'),
    jpeg = require('..');

var it = redtape({
  asserts: {
    bufferEqual: function (a, b) {
      if (a.length != b.length) return false;
      for (var i = 0, len = a.length; i < len; i++) {
        if (a[i] !== b[i]) return false;
      }
      return true;
    }
  }
});

function fixture(name) {
  return fs.readFileSync(path.join(__dirname, 'fixtures', name));
}

it('should be able to decode a JPEG', function(t) {
  var jpegData = fixture('grumpycat.jpg');
  var rawImageData = jpeg.decode(jpegData);
  t.equal(rawImageData.width, 320);
  t.equal(rawImageData.height, 180);
  var expected = fixture('grumpycat.rgba');
  t.deepEqual(rawImageData.data, expected);
  t.end();
});

it('should be able to decode a JPEG with RST intervals', function(t) {
  var jpegData = fixture('redbox-with-rst.jpg');
  var rawImageData = jpeg.decode(jpegData);
  var expected = fixture('redbox.jpg');
  var rawExpectedImageData = jpeg.decode(expected);
  t.deepEqual(rawImageData.data, rawExpectedImageData.data);
  t.end();
});

it('should be able to encode a JPEG', function (t) {
  var frameData = fixture('grumpycat.rgba');
  var rawImageData = {
    data: frameData,
    width: 320,
    height: 180
  };
  var jpegImageData = jpeg.encode(rawImageData, 50);
  t.equal(jpegImageData.width, 320);
  t.equal(jpegImageData.height, 180);
  var expected = fixture('grumpycat-50.jpg');
  t.deepEqual(jpegImageData.data, expected);
  t.end();
});

it('should be able to create a JPEG from an array', function (t) {
  var width = 320, height = 180;
  var frameData = new Buffer(width * height * 4);
  var i = 0;
  while (i < frameData.length) {
    frameData[i++] = 0xFF; // red
    frameData[i++] = 0x00; // green
    frameData[i++] = 0x00; // blue
    frameData[i++] = 0xFF; // alpha - ignored in JPEGs
  }
  var rawImageData = {
    data: frameData,
    width: width,
    height: height
  };
  var jpegImageData = jpeg.encode(rawImageData, 50);
  t.equal(jpegImageData.width, width);
  t.equal(jpegImageData.height, height);
  var expected = fixture('redbox.jpg');
  t.bufferEqual(jpegImageData.data, expected);
  t.end();
});
