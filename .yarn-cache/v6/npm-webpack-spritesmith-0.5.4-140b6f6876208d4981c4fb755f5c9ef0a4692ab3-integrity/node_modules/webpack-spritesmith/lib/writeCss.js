"use strict";

function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }

const spritesheetTemplater = require('spritesheet-templates');

const _require = require('./utils'),
      sendToPast = _require.sendToPast,
      writeFileR = _require.writeFileR;

module.exports =
/*#__PURE__*/
function () {
  var _ref = _asyncToGenerator(function* (sources, templaterData, shouldSendToPast) {
    return yield Promise.all(sources.map(
    /*#__PURE__*/
    function () {
      var _ref2 = _asyncToGenerator(function* (css) {
        const fileName = css[0];
        const code = spritesheetTemplater(templaterData, css[1]);
        yield writeFileR(fileName, code);
        yield sendToPast(fileName, !shouldSendToPast);
        return fileName;
      });

      return function (_x4) {
        return _ref2.apply(this, arguments);
      };
    }()));
  });

  return function (_x, _x2, _x3) {
    return _ref.apply(this, arguments);
  };
}();