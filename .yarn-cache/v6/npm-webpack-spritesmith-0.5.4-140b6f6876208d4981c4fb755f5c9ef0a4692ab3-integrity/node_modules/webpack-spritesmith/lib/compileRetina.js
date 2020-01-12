"use strict";

function _objectSpread(target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i] != null ? arguments[i] : {}; var ownKeys = Object.keys(source); if (typeof Object.getOwnPropertySymbols === 'function') { ownKeys = ownKeys.concat(Object.getOwnPropertySymbols(source).filter(function (sym) { return Object.getOwnPropertyDescriptor(source, sym).enumerable; })); } ownKeys.forEach(function (key) { _defineProperty(target, key, source[key]); }); } return target; }

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function asyncGeneratorStep(gen, resolve, reject, _next, _throw, key, arg) { try { var info = gen[key](arg); var value = info.value; } catch (error) { reject(error); return; } if (info.done) { resolve(value); } else { Promise.resolve(value).then(_next, _throw); } }

function _asyncToGenerator(fn) { return function () { var self = this, args = arguments; return new Promise(function (resolve, reject) { var gen = fn.apply(self, args); function _next(value) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "next", value); } function _throw(err) { asyncGeneratorStep(gen, resolve, reject, _next, _throw, "throw", err); } _next(undefined); }); }; }

const Spritesmith = require('spritesmith');

const path = require('path');

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
    const sourceRecords = srcFiles.map(fileName => {
      const oneRecord = options.retina.classifier(path.resolve(options.src.cwd, fileName));
      return _objectSpread({}, oneRecord, {
        apiName: options.apiOptions.generateSpriteName(oneRecord.normalName)
      });
    });

    const combinedSources = _.map(_.groupBy(sourceRecords, 'apiName'), group => {
      const result = _.clone(group[0]);

      group.forEach(oneRecord => {
        result[oneRecord.type] = true;
      });
      return result;
    });

    const errors = checkMissingImages();

    if (errors.length !== 0) {
      metaOutput.errors.push(...errors);
      return null;
    }

    const results = yield Promise.all([promiseCall(Spritesmith.run.bind(Spritesmith), _objectSpread({}, options.spritesmithOptions, {
      src: _.map(combinedSources, 'normalName')
    })), promiseCall(Spritesmith.run.bind(Spritesmith), _objectSpread({}, options.spritesmithOptions, {
      src: _.map(combinedSources, 'retinaName'),
      padding: (options.spritesmithOptions.padding || 0) * 2
    }))]);
    combinedSources.forEach(oneSource => {
      oneSource.normalCoordinates = results[0].coordinates[oneSource.normalName];
      oneSource.retinaCoordinates = results[1].coordinates[oneSource.retinaName];
    });
    const normalSprites = getSpritesForSpritesheetTemplates('', 'normalCoordinates', 'normalName');
    const retinaSprites = getSpritesForSpritesheetTemplates('retina_', 'retinaCoordinates', 'retinaName');
    const spritesheetTemplatesData = {
      sprites: normalSprites,
      spritesheet: {
        width: results[0].properties.width,
        height: results[0].properties.height,
        image: substitute(options.apiOptions.cssImageRef, results[0])
      },
      retina_sprites: retinaSprites,
      retina_spritesheet: {
        width: results[1].properties.width,
        height: results[1].properties.height,
        image: substitute(options.retina.cssImageRef, results[1])
      },
      retina_groups: combinedSources.map((sprite, i) => ({
        name: sprite.apiName,
        index: i
      }))
    };
    const normalImageName = substitute(options.target.image, results[0]);
    const retinaImageName = substitute(options.retina.targetImage, results[1]);

    const writeImage =
    /*#__PURE__*/
    function () {
      var _ref2 = _asyncToGenerator(function* (fileName, buffer, isInitial) {
        yield writeFileR(fileName, buffer, 'binary');
        yield sendToPast(fileName, !isInitial);
      });

      return function writeImage(_x5, _x6, _x7) {
        return _ref2.apply(this, arguments);
      };
    }();

    const willWriteCss = writeCss(options.target.css, spritesheetTemplatesData, isInitial);
    yield writeImage(normalImageName, results[0].image, isInitial);
    yield writeImage(retinaImageName, results[1].image, isInitial);
    return {
      css: yield willWriteCss,
      images: [normalImageName, retinaImageName]
    };

    function getSpritesForSpritesheetTemplates(prefix, field, sourceField) {
      return _.map(combinedSources, sprite => ({
        name: prefix + sprite.apiName,
        source_image: sprite[sourceField],
        x: sprite[field].x,
        y: sprite[field].y,
        width: sprite[field].width,
        height: sprite[field].height
      }));
    }

    function checkMissingImages() {
      const errors = [];

      _.forEach(combinedSources, group => {
        if (group.retina && !group.normal) {
          errors.push(new Error('webpack-spritesmith: no normal source for sprite "' + group.apiName + '" expected file name is ' + group.normalName));
        }

        if (!group.retina && group.normal) {
          errors.push(new Error('webpack-spritesmith: no retina source for sprite "' + group.apiName + '" expected file name is ' + group.retinaName));
        }
      });

      return errors;
    }
  });

  return function (_x, _x2, _x3, _x4) {
    return _ref.apply(this, arguments);
  };
}();