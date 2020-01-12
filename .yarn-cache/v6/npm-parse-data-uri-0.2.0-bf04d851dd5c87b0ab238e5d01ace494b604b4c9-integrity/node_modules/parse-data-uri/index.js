var toBuffer = require('data-uri-to-buffer')

function parseDataUri (dataUri) {

  return {
    mimeType: normalizeMimeType(parseMimeType(dataUri)),
    data: toBuffer(dataUri)
  }
}

function parseMimeType(uri) {
  return uri.substring(5, uri.indexOf(';'))
}

var prefix = /^(\w+\/)+/
function normalizeMimeType(mime) {
  mime = mime.toLowerCase()
  var once = mime.match(prefix)
  if (!once || !(once = once[1])) {
    return mime
  }
  return mime.replace(prefix, once)

}

module.exports = parseDataUri