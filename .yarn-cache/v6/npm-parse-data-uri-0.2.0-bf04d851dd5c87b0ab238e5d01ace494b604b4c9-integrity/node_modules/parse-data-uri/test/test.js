var mochi = require('mochi')
var test = require('fs').readFileSync(__dirname + '/test.datauri').toString()


describe('parse-data-uri', function () {
  var parseDataUri = require('../')
  
  it('works with crazy messed up mime types', function () {
    var t = test.replace('image/gif','image/image/gif') 
    // this is a test case i've seen from some datauris in the wild
    parseDataUri(t).mimeType
      .should.equal('image/gif')
  })

  it('returns an object', function () {

    parseDataUri(test)
      .should.have.keys(['mimeType', 'data'])
    
  })

  it('parses mime type', function () {

    parseDataUri(test).mimeType
      .should.equal('image/gif')
    
  })

  it('decodes the buffer', function () {

    parseDataUri(test).data.constructor
      .should.equal(Buffer)

  })


})