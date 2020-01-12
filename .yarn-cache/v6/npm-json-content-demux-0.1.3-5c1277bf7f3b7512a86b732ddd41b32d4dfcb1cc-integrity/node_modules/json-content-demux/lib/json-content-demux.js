/**
 * @param {String} muxStr Muxed content to break up
 * TODO: options is not yet used
 * @param {Object} [options] Options to break up by
 * @param {String|RegExp} [options.delimiter=/\n\r?\n\r?/] Delimiter between JSON and content
 * @returns {Object} retObj
 * @returns {Object} retObj.json JSON found at the head of the content
 * @returns {String} retObj.content Content found in the body
 */
function jsonContentDemux(muxStr, options) {
  // Find where the JSON ends
  var delimiter = /\n\r?\n\r?/g,
      result = delimiter.exec(muxStr),
      delimiterIndex = delimiter.lastIndex;

  // By default, lastIndex = 0 so no fallbacking is necessary
  // // Fallback the dblLineBreakIndex
  // if (delimiterIndex === -1) {
  //   delimiterIndex = 0;
  // }

  // Break up the json and content
  var jsonStr = muxStr.slice(0, delimiterIndex) || '{}',
      json = {};

  // Attempt to interpret the JSON
  try {
    json = new Function('return ' + jsonStr + ';')();
  } catch (e) {
  // Upon failure, reset the delimiterIndex to 0
    delimiterIndex = 0;
  }

  // Extract the content
  var content = muxStr.slice(delimiterIndex);

  // Prepare a retObj and return
  var retObj = {
        'json': json,
        'content': content
      };
  return retObj;
}

// Export jsonContentDemux
module.exports = jsonContentDemux;