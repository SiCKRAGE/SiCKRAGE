var jsonContentDemux = require('../lib/json-content-demux.js'),
    fs = require('fs'),
    testFilesDir = __dirname + '/test_files',
    expectedFilesDir = __dirname + '/expected_files';

/*
  ======== A Handy Little Nodeunit Reference ========
  https://github.com/caolan/nodeunit

  Test methods:
    test.expect(numAssertions)
    test.done()
  Test assertions:
    test.ok(value, [message])
    test.equal(actual, expected, [message])
    test.notEqual(actual, expected, [message])
    test.deepEqual(actual, expected, [message])
    test.notDeepEqual(actual, expected, [message])
    test.strictEqual(actual, expected, [message])
    test.notStrictEqual(actual, expected, [message])
    test.throws(block, [error], [message])
    test.doesNotThrow(block, [error], [message])
    test.ifError(value)
*/

exports['json-content-demux'] = {
  setUp: function(done) {
    // setup here
    done();
  },
  'simple': function(test) {
    test.expect(2);

    // Simple content
    var muxContent = fs.readFileSync(testFilesDir + '/simple.md', 'utf8');
      // when demuxed
      var demuxObj = jsonContentDemux(muxContent);
        // has the expected JSON and content
        var expectedJSON = require(expectedFilesDir + '/simple.json'),
            expectedContent = fs.readFileSync(expectedFilesDir + '/simple.content.md', 'utf8');
        test.deepEqual(expectedJSON, demuxObj.json, 'Actual JSON and expected JSON are not equal');
        test.strictEqual(expectedContent, demuxObj.content, 'Actual content and expected content are not equal');

    test.done();
  },
  'jsonless': function (test) {
    test.expect(1);

    // JSON-less content
    var muxContent = fs.readFileSync(testFilesDir + '/jsonless.md', 'utf8');
      // when demuxed
      var demuxObj = jsonContentDemux(muxContent);
        // has the expected content
        var expectedContent = fs.readFileSync(expectedFilesDir + '/jsonless.content.md', 'utf8');
        test.strictEqual(expectedContent, demuxObj.content, 'Actual content and expected content are not equal');

    test.done();
  },
  'jsonless with lines': function (test) {
    test.expect(1);

    // JSON-less content
    var muxContent = fs.readFileSync(testFilesDir + '/jsonless_with_lines.md', 'utf8');
      // when demuxed
      var demuxObj = jsonContentDemux(muxContent);
        // has the expected content
        var expectedContent = fs.readFileSync(expectedFilesDir + '/jsonless_with_lines.content.md', 'utf8');
        test.strictEqual(expectedContent, demuxObj.content, 'Actual content and expected content are not equal');

    test.done();
  }
};
