// Load in our dependencies
var assert = require('assert');
var fs = require('fs');
var nineTrack = require('nine-track');
var express = require('express');
var normalizeMultipart = require('eight-track-normalize-multipart');
var Tempfile = require('temporary/lib/file');
var validateCss = require('css-validator');
var templater = require('../../');

// Start our utilities
exports.setInfo = function (info) {
  assert(info, '`testUtils.setInfo` requires `info` but it was not provided. Please provide it.');
  before(function setInfoFn () {
    this.info = info;
  });
  after(function cleanup () {
    delete this.info;
  });
};

exports.runTemplater = function (options) {
  before(function runTemplaterFn () {
    // Convert info into result via templater
    var info = this.info;
    assert(info, '`testUtils.runTemplater` requires `this.info` to be defined. ' +
      'Please make sure `testUtils.setInfo` was run already');
    var result = options ? templater(info, options) : templater(info);
    this.result = result;
  });
  after(function cleanup () {
    delete this.result;
  });
};

exports.assertOutputMatches = function (expectedFilepath) {
  it('matches as expected', function assertOutputMatchesFn () {
    // Load in the files and assert
    var actual = this.result;
    var expected = fs.readFileSync(expectedFilepath, 'utf8');
    assert.strictEqual(actual, expected);
  });
};

exports.generateCssFile = function (content) {
  before(function generateCssFileFn () {
    // Concatenate content with our result
    var result = this.result || '';
    var output = result + (content || '');

    // Output the content to a file
    var tmp = new Tempfile();
    tmp.writeFileSync(output);
    this.tmp = tmp;
  });
  after(function cleanup () {
    this.tmp.unlinkSync();
    delete this.tmp;
  });
};

exports.processCss = function (fn) {
  before(function processCssFn (done) {
    // Run our function
    var that = this;
    fn.call(this, function handleResult (err, css) {
      // Save our CSS and callback with any errors
      that.css = css;
      done(err);
    });
  });
  after(function cleanup () {
    delete this.css;
  });
};

exports.runFakeJigsaw = function () {
  before(function () {
    this.fakeJigsaw = express().use(nineTrack({
      url: 'http://jigsaw.w3.org',
      fixtureDir: __dirname + '/../test_files/fake_jigsaw/',
      normalizeFn: function (info) {
        // Normalize multipart formdata
        normalizeMultipart(info);

        // Normalize node@0.10 vs iojs `connection` header
        if (info.headers && info.headers.connection) {
          info.headers.connection = 'keep-alive';
        }

        // Return our info
        return info;
      },
      preventRecording: process.env.CI
    })).listen(1337);
  });
  after(function (done) {
    this.fakeJigsaw.close(done);
  });
};

exports._assertValidCss = function (css, done) {
  // Assert CSS exists
  assert.notEqual(css, '');

  // Assert it was fully valid via w3c
  validateCss({
    text: css,
    w3cUrl: 'http://localhost:1337/css-validator/validator'
  }, function (err, data) {
    assert.strictEqual(err, null);
    assert.deepEqual(data.errors, []);
    assert.deepEqual(data.warnings, []);
    done();
  });
};

exports.assertValidCss = function () {
  exports.runFakeJigsaw();
  it('is valid CSS', function (done) {
    exports._assertValidCss(this.css, done);
  });
};
