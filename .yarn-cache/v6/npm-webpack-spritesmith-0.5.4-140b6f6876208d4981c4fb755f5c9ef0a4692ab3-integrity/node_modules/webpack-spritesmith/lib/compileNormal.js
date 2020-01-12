"use strict";

function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i] != null ? arguments[i] : {}; var ownKeys = Object.keys(source); if (typeof Object.getOwnPropertySymbols === 'function') { ownKeys = ownKeys.concat(Object.getOwnPropertySymbols(source).filter(function (sym) { return Object.getOwnPropertyDescriptor(source, sym).enumerable; })); } ownKeys.forEach(function (key) { _defineProperty(target, key, source[key]); }); } return target; }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }

const path = require('path');

const Spritesmith = require('spritesmith');

const _ = require('lodash');

const substitute = require('./substitute');

const writeCss = require('./writeCss');

const _require = require('./utils'),
      sendToPast = _require.sendToPast,
      promiseCall = _require.promiseCall,
      writeFileR = _require.writeFileR;

module.exports =
/*#__PURE__*/
function () {
  var _ref = _asyncToGenerator(function* (options, metaOutput, isInitial, srcFiles) {
    const spritesmithResult = yield promiseCall(Spritesmith.run.bind(Spritesmith), _objectSpread({}, options.spritesmithOptions, {
      src: srcFiles.map(fileName => path.resolve(options.src.cwd, fileName))
    }));
    const imageNameWithSubstitutions = substitute(options.target.image, spritesmithResult);
    const willWriteCss = writeCss(options.target.css, toSpritesheetTemplatesFormat(spritesmithResult), isInitial);
    yield writeFileR(imageNameWithSubstitutions, spritesmithResult.image, 'binary');
    yield sendToPast(imageNameWithSubstitutions, !isInitial);
    return {
      css: yield willWriteCss,
      images: [imageNameWithSubstitutions]
    };

    function toSpritesheetTemplatesFormat(spritesmithResult) {
      const generateSpriteName = options.apiOptions.generateSpriteName;

      const sprites = _.map(spritesmithResult.coordinates, (oneSourceInfo, fileName) => _objectSpread({}, oneSourceInfo, {
        name: generateSpriteName(fileName),
        source_image: fileName
      }));

      const imageRefWithSubstitutions = substitute(options.apiOptions.cssImageRef, spritesmithResult);

      const spritesheet = _objectSpread({
        image: imageRefWithSubstitutions
      }, spritesmithResult.properties);

      return {
        sprites,
        spritesheet
      };
    }
  });

  return function (_x, _x2, _x3, _x4) {
    return _ref.apply(this, arguments);
  };
}();