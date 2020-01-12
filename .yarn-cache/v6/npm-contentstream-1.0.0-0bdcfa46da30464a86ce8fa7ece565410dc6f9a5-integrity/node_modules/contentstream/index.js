/**!
 * contentstream - index.js
 *
 * Copyright(c) fengmk2 and other contributors.
 * MIT Licensed
 *
 * Authors:
 *   fengmk2 <fengmk2@gmail.com> (http://fengmk2.github.com)
 */

'use strict';

/**
 * Module dependencies.
 */

var Readable = require('readable-stream').Readable;
var util = require('util');

module.exports = ContentStream;

function ContentStream(obj, options) {
  if (!(this instanceof ContentStream)) {
    return new ContentStream(obj, options);
  }
  Readable.call(this, options);
  if (obj === null || obj === undefined) {
    obj = String(obj);
  }
  this._obj = obj;
}

util.inherits(ContentStream, Readable);

ContentStream.prototype._read = function (n) {
  var obj = this._obj;
  if (typeof obj === 'string') {
    this.push(new Buffer(obj));
  } else if (Buffer.isBuffer(obj)) {
    this.push(obj);
  } else {
    this.push(new Buffer(JSON.stringify(obj)));
  }
  this.push(null);
};
