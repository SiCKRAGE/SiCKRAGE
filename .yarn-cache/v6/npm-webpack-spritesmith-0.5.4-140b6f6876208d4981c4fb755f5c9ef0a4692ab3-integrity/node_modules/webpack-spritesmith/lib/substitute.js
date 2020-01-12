"use strict";

const loaderUtils = require('loader-utils');

const path = require('path').posix;

module.exports = (fullName, spritesmithResult) => {
  const parsed = path.parse(fullName);
  parsed.base = loaderUtils.interpolateName({}, parsed.base, {
    content: spritesmithResult.image
  });
  return path.format(parsed);
};