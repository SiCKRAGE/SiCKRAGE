var fs = require('fs');
var getPixels = require('get-pixels');

exports.load = function (filename) {
  before(function loadImage (done) {
    var that = this;
    getPixels(__dirname + '/../test-files/' + filename, function (err, pixels) {
      if (err) {
        return done(err);
      }
      that.pixels = pixels;
      done();
    });
  });
};

exports.debug = function (filename) {
  if (process.env.DEBUG_TEST) {
    before(function saveDebugImage () {
      try { fs.mkdirSync(__dirname + '/../actual-files/'); } catch (e) {}
      fs.writeFileSync(__dirname + '/../actual-files/' + filename, this.gifData, 'binary');
    });
  }

  if (false && process.env.TRAVIS) {
    before(function outputDebugImage () {
      console.log(encodeURIComponent(this.gifData));
      // Counter to it:
      // var fs = require('fs');
      // var data = "<%= data %>";
      // fs.writeFileSync('tmp.gif', decodeURIComponent(data), 'binary');
    });
  }
};