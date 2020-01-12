(function (global, factory) {
  if (typeof define === "function" && define.amd) {
    define('PNotifyCompat', ['exports', './PNotify'], factory);
  } else if (typeof exports !== "undefined") {
    factory(exports, require('./PNotify'));
  } else {
    var mod = {
      exports: {}
    };
    factory(mod.exports, global.PNotify);
    global.PNotifyCompat = mod.exports;
  }
})(this, function (exports, _PNotify2) {
  'use strict';

  Object.defineProperty(exports, "__esModule", {
    value: true
  });

  var _PNotify3 = _interopRequireDefault(_PNotify2);

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule ? obj : {
      default: obj
    };
  }

  var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {
    return typeof obj;
  } : function (obj) {
    return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
  };

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError("Cannot call a class as a function");
    }
  }

  var _createClass = function () {
    function defineProperties(target, props) {
      for (var i = 0; i < props.length; i++) {
        var descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ("value" in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function (Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  }();

  function _possibleConstructorReturn(self, call) {
    if (!self) {
      throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
    }

    return call && (typeof call === "object" || typeof call === "function") ? call : self;
  }

  var _get2 = function get(object, property, receiver) {
    if (object === null) object = Function.prototype;
    var desc = Object.getOwnPropertyDescriptor(object, property);

    if (desc === undefined) {
      var parent = Object.getPrototypeOf(object);

      if (parent === null) {
        return undefined;
      } else {
        return get(parent, property, receiver);
      }
    } else if ("value" in desc) {
      return desc.value;
    } else {
      var getter = desc.get;

      if (getter === undefined) {
        return undefined;
      }

      return getter.call(receiver);
    }
  };

  function _inherits(subClass, superClass) {
    if (typeof superClass !== "function" && superClass !== null) {
      throw new TypeError("Super expression must either be null or a function, not " + typeof superClass);
    }

    subClass.prototype = Object.create(superClass && superClass.prototype, {
      constructor: {
        value: subClass,
        enumerable: false,
        writable: true,
        configurable: true
      }
    });
    if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass;
  }

  var _extends = Object.assign || function (target) {
    for (var i = 1; i < arguments.length; i++) {
      var source = arguments[i];

      for (var key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }

    return target;
  };

  // Translate v3 options to v4 options.
  var translateOptions = function translateOptions(options, module, moduleName) {
    // Merge the classic default options.
    var newOptions = module ? _extends({}, moduleName ? PNotifyCompat.prototype.options[moduleName] : {}, options) : _extends({}, PNotifyCompat.prototype.options, options);
    var translateName = function translateName(badName) {
      var goodName = badName;
      var underscoreIndex = void 0;
      while ((underscoreIndex = goodName.indexOf('_')) !== -1) {
        goodName = goodName.slice(0, underscoreIndex) + goodName.slice(underscoreIndex + 1, underscoreIndex + 2).toUpperCase() + goodName.slice(underscoreIndex + 2);
      }
      return goodName;
    };

    // Translate all options to the new style.
    for (var name in newOptions) {
      if (newOptions.hasOwnProperty(name) && name.indexOf('_') !== -1) {
        var goodName = translateName(name);
        newOptions[goodName] = newOptions[name];
        delete newOptions[name];
      }
    }

    if (!module) {
      // Options that have changed.
      if (newOptions.hasOwnProperty('addclass')) {
        newOptions.addClass = newOptions.addclass;
        delete newOptions.addclass;
      }
      if (newOptions.hasOwnProperty('cornerclass')) {
        newOptions.cornerClass = newOptions.cornerclass;
        delete newOptions.cornerClass;
      }
      if (newOptions.hasOwnProperty('textEscape')) {
        newOptions.textTrusted = !newOptions.textEscape;
        delete newOptions.textEscape;
      }
      if (newOptions.hasOwnProperty('titleEscape')) {
        newOptions.titleTrusted = !newOptions.titleEscape;
        delete newOptions.titleEscape;
      }

      // Styling and icons.
      if (newOptions.hasOwnProperty('styling')) {
        if (newOptions.styling === 'bootstrap3') {
          newOptions.icons = 'bootstrap3';
        } else if (newOptions.styling === 'fontawesome') {
          newOptions.styling = 'bootstrap3';
          newOptions.icons = 'fontawesome4';
        }
      }

      // Stacks.
      if (newOptions.hasOwnProperty('stack')) {
        if (newOptions.stack.overlay_close) {
          newOptions.stack.overlayClose = newOptions.stack.overlay_close;
        }
      }

      // Translate module options.
      newOptions.modules = {};
      if (newOptions.hasOwnProperty('animate')) {
        newOptions.modules.Animate = translateOptions(newOptions.animate, true, 'animate');
        delete newOptions.animate;
      }
      if (newOptions.hasOwnProperty('buttons')) {
        newOptions.modules.Buttons = translateOptions(newOptions.buttons, true, 'buttons');
        delete newOptions.buttons;
        if (newOptions.modules.Buttons.classes) {
          newOptions.modules.Buttons.classes = translateOptions(newOptions.modules.Buttons.classes, true);
        }
      }
      if (newOptions.hasOwnProperty('confirm')) {
        newOptions.modules.Confirm = translateOptions(newOptions.confirm, true, 'confirm');
        if (newOptions.modules.Confirm.promptDefault) {
          newOptions.modules.Confirm.promptValue = newOptions.modules.Confirm.promptDefault;
          delete newOptions.modules.Confirm.promptDefault;
        }
        delete newOptions.confirm;
      }
      if (newOptions.hasOwnProperty('desktop')) {
        newOptions.modules.Desktop = translateOptions(newOptions.desktop, true, 'desktop');
        delete newOptions.desktop;
      }
      if (newOptions.hasOwnProperty('history')) {
        newOptions.modules.History = translateOptions(newOptions.history, true, 'history');
        delete newOptions.history;
      }
      if (newOptions.hasOwnProperty('mobile')) {
        newOptions.modules.Mobile = translateOptions(newOptions.mobile, true, 'mobile');
        delete newOptions.mobile;
      }
      if (newOptions.hasOwnProperty('nonblock')) {
        newOptions.modules.NonBlock = translateOptions(newOptions.nonblock, true, 'nonblock');
        delete newOptions.nonblock;
      }
      if (newOptions.hasOwnProperty('reference')) {
        newOptions.modules.Reference = translateOptions(newOptions.reference, true, 'reference');
        delete newOptions.reference;
      }
      if (newOptions.hasOwnProperty('beforeInit')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.beforeInit = newOptions.beforeInit;
        delete newOptions.beforeInit;
      }
      if (newOptions.hasOwnProperty('afterInit')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.afterInit = newOptions.afterInit;
        delete newOptions.afterInit;
      }
      if (newOptions.hasOwnProperty('beforeOpen')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.beforeOpen = newOptions.beforeOpen;
        delete newOptions.beforeOpen;
      }
      if (newOptions.hasOwnProperty('afterOpen')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.afterOpen = newOptions.afterOpen;
        delete newOptions.afterOpen;
      }
      if (newOptions.hasOwnProperty('beforeClose')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.beforeClose = newOptions.beforeClose;
        delete newOptions.beforeClose;
      }
      if (newOptions.hasOwnProperty('afterClose')) {
        if (!newOptions.modules.Callbacks) {
          newOptions.modules.Callbacks = {};
        }
        newOptions.modules.Callbacks.afterClose = newOptions.afterClose;
        delete newOptions.afterClose;
      }
    }

    return newOptions;
  };

  // The compatibility class.

  var PNotifyCompat = function (_PNotify) {
    _inherits(PNotifyCompat, _PNotify);

    function PNotifyCompat(options) {
      _classCallCheck(this, PNotifyCompat);

      if ((typeof options === 'undefined' ? 'undefined' : _typeof(options)) !== 'object') {
        options = { 'text': options };
      }

      // These need to be called directly, since we're not using PNotify.alert().
      if (_PNotify3.default.modules.Callbacks && options.before_init) {
        options.before_init(options);
      }

      options = translateOptions(options);

      var _this = _possibleConstructorReturn(this, (PNotifyCompat.__proto__ || Object.getPrototypeOf(PNotifyCompat)).call(this, { target: document.body, data: options }));

      // Override the get function to return the element like it did in v3.
      var _get = _this.get;
      _this.get = function (option) {
        if (option === undefined) {
          return _extends(window.jQuery ? window.jQuery(this.refs.elem) : this.refs.elem, _get.call(this));
        }
        return _get.call(this, option);
      };

      // Confirm module events.
      _this.on('pnotify.confirm', function (e) {
        if (window.jQuery) {
          window.jQuery(_this.refs.elem).trigger('pnotify.confirm', [_this, e.value]);
        }
      });
      _this.on('pnotify.cancel', function (e) {
        if (window.jQuery) {
          window.jQuery(_this.refs.elem).trigger('pnotify.cancel', _this);
        }
      });

      if (_PNotify3.default.modules.Callbacks) {
        _PNotify3.default.modules.Callbacks.getCallbacks(_this, null, 'afterInit')(_this);
      }
      return _this;
    }

    _createClass(PNotifyCompat, [{
      key: 'update',
      value: function update(options) {
        options = translateOptions(options);
        return _get2(PNotifyCompat.prototype.__proto__ || Object.getPrototypeOf(PNotifyCompat.prototype), 'update', this).call(this, options);
      }
    }]);

    return PNotifyCompat;
  }(_PNotify3.default);

  // Lets you change defaults the old way.
  PNotifyCompat.prototype.options = {
    text_escape: false,
    title_escape: false
  };

  // Forward static functions.
  PNotifyCompat.reload = function () {
    return PNotifyCompat;
  };
  PNotifyCompat.removeAll = function () {
    return _PNotify3.default.removeAll();
  };
  PNotifyCompat.removeStack = function (stack) {
    return _PNotify3.default.removeStack(stack);
  };
  PNotifyCompat.positionAll = function (animate) {
    return _PNotify3.default.positionAll(animate);
  };

  // Desktop module permission method.
  PNotifyCompat.desktop = {
    permission: function permission() {
      _PNotify3.default.modules.Desktop.permission();
    }
  };

  // Old style showLast() in History module.
  if (window.jQuery) {
    window.jQuery(function () {
      window.jQuery(document.body).on('pnotify.history-last', function () {
        _PNotify3.default.modules.History.showLast();
      });
    });
  }

  exports.default = PNotifyCompat;
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIlBOb3RpZnlDb21wYXQuanMiXSwibmFtZXMiOlsidHJhbnNsYXRlT3B0aW9ucyIsIm9wdGlvbnMiLCJtb2R1bGUiLCJtb2R1bGVOYW1lIiwibmV3T3B0aW9ucyIsIlBOb3RpZnlDb21wYXQiLCJwcm90b3R5cGUiLCJ0cmFuc2xhdGVOYW1lIiwiYmFkTmFtZSIsImdvb2ROYW1lIiwidW5kZXJzY29yZUluZGV4IiwiaW5kZXhPZiIsInNsaWNlIiwidG9VcHBlckNhc2UiLCJuYW1lIiwiaGFzT3duUHJvcGVydHkiLCJhZGRDbGFzcyIsImFkZGNsYXNzIiwiY29ybmVyQ2xhc3MiLCJjb3JuZXJjbGFzcyIsInRleHRUcnVzdGVkIiwidGV4dEVzY2FwZSIsInRpdGxlVHJ1c3RlZCIsInRpdGxlRXNjYXBlIiwic3R5bGluZyIsImljb25zIiwic3RhY2siLCJvdmVybGF5X2Nsb3NlIiwib3ZlcmxheUNsb3NlIiwibW9kdWxlcyIsIkFuaW1hdGUiLCJhbmltYXRlIiwiQnV0dG9ucyIsImJ1dHRvbnMiLCJjbGFzc2VzIiwiQ29uZmlybSIsImNvbmZpcm0iLCJwcm9tcHREZWZhdWx0IiwicHJvbXB0VmFsdWUiLCJEZXNrdG9wIiwiZGVza3RvcCIsIkhpc3RvcnkiLCJoaXN0b3J5IiwiTW9iaWxlIiwibW9iaWxlIiwiTm9uQmxvY2siLCJub25ibG9jayIsIlJlZmVyZW5jZSIsInJlZmVyZW5jZSIsIkNhbGxiYWNrcyIsImJlZm9yZUluaXQiLCJhZnRlckluaXQiLCJiZWZvcmVPcGVuIiwiYWZ0ZXJPcGVuIiwiYmVmb3JlQ2xvc2UiLCJhZnRlckNsb3NlIiwiYmVmb3JlX2luaXQiLCJ0YXJnZXQiLCJkb2N1bWVudCIsImJvZHkiLCJkYXRhIiwiX2dldCIsImdldCIsIm9wdGlvbiIsInVuZGVmaW5lZCIsIndpbmRvdyIsImpRdWVyeSIsInJlZnMiLCJlbGVtIiwiY2FsbCIsIm9uIiwiZSIsInRyaWdnZXIiLCJ2YWx1ZSIsImdldENhbGxiYWNrcyIsInRleHRfZXNjYXBlIiwidGl0bGVfZXNjYXBlIiwicmVsb2FkIiwicmVtb3ZlQWxsIiwicmVtb3ZlU3RhY2siLCJwb3NpdGlvbkFsbCIsInBlcm1pc3Npb24iLCJzaG93TGFzdCJdLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBRUE7QUFDQSxNQUFNQSxtQkFBbUIsU0FBbkJBLGdCQUFtQixDQUFDQyxPQUFELEVBQVVDLE1BQVYsRUFBa0JDLFVBQWxCLEVBQWlDO0FBQ3hEO0FBQ0EsUUFBTUMsYUFBYUYsU0FBUyxTQUFjLEVBQWQsRUFBa0JDLGFBQWFFLGNBQWNDLFNBQWQsQ0FBd0JMLE9BQXhCLENBQWdDRSxVQUFoQyxDQUFiLEdBQTJELEVBQTdFLEVBQWlGRixPQUFqRixDQUFULEdBQXFHLFNBQWMsRUFBZCxFQUFrQkksY0FBY0MsU0FBZCxDQUF3QkwsT0FBMUMsRUFBbURBLE9BQW5ELENBQXhIO0FBQ0EsUUFBTU0sZ0JBQWdCLFNBQWhCQSxhQUFnQixDQUFDQyxPQUFELEVBQWE7QUFDakMsVUFBSUMsV0FBV0QsT0FBZjtBQUNBLFVBQUlFLHdCQUFKO0FBQ0EsYUFBTyxDQUFDQSxrQkFBa0JELFNBQVNFLE9BQVQsQ0FBaUIsR0FBakIsQ0FBbkIsTUFBOEMsQ0FBQyxDQUF0RCxFQUF5RDtBQUN2REYsbUJBQVdBLFNBQVNHLEtBQVQsQ0FBZSxDQUFmLEVBQWtCRixlQUFsQixJQUFxQ0QsU0FBU0csS0FBVCxDQUFlRixrQkFBa0IsQ0FBakMsRUFBb0NBLGtCQUFrQixDQUF0RCxFQUF5REcsV0FBekQsRUFBckMsR0FBOEdKLFNBQVNHLEtBQVQsQ0FBZUYsa0JBQWtCLENBQWpDLENBQXpIO0FBQ0Q7QUFDRCxhQUFPRCxRQUFQO0FBQ0QsS0FQRDs7QUFTQTtBQUNBLFNBQUssSUFBSUssSUFBVCxJQUFpQlYsVUFBakIsRUFBNkI7QUFDM0Is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LE9BQWhCLENBQXdCeUMsUUFBeEI7QUFDRCxPQUZEO0FBR0QsS0FKRDtBQUtEOztvQkFFYzdFLGEiLCJmaWxlIjoic3JjL1BOb3RpZnlDb21wYXQuanMiLCJzb3VyY2VSb290IjoiLi4vIiwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IFBOb3RpZnkgZnJvbSAnLi9QTm90aWZ5Lmh0bWwnO1xuXG4vLyBUcmFuc2xhdGUgdjMgb3B0aW9ucyB0byB2NCBvcHRpb25zLlxuY29uc3QgdHJhbnNsYXRlT3B0aW9ucyA9IChvcHRpb25zLCBtb2R1bGUsIG1vZHVsZU5hbWUpID0+IHtcbiAgLy8gTWVyZ2UgdGhlIGNsYXNzaWMgZGVmYXVsdCBvcHRpb25zLlxuICBjb25zdCBuZXdPcHRpb25zID0gbW9kdWxlID8gT2JqZWN0LmFzc2lnbih7fSwgbW9kdWxlTmFtZSA/IFBOb3RpZnlDb21wYXQucHJvdG90eXBlLm9wdGlvbnNbbW9kdWxlTmFtZV0gOiB7fSwgb3B0aW9ucykgOiBPYmplY3QuYXNzaWduKHt9LCBQTm90aWZ5Q29tcGF0LnByb3RvdHlwZS5vcHRpb25zLCBvcHRpb25zKTtcbiAgY29uc3QgdHJhbnNsYXRlTmFtZSA9IChiYWROYW1lKSA9PiB7XG4gICAgbGV0IGdvb2ROYW1lID0gYmFkTmFtZTtcbiAgICBsZXQgdW5kZXJzY29yZUluZGV4O1xuICAgIHdoaWxlICgodW5kZXJzY29yZUluZGV4ID0gZ29vZE5hbWUuaW5kZXhPZignXycpKSAhPT0gLTEpIHtcbiAgICAgIGdvb2ROYW1lID0gZ29vZE5hbWUuc2xpY2UoMCwgdW5kZXJzY29yZUluZGV4KSArIGdvb2ROYW1lLnNsaWNlKHVuZGVyc2NvcmVJbmRleCArIDEsIHVuZGVyc2NvcmVJbmRleCArIDIpLnRvVXBwZXJDYXNlKCkgKyBnb29kTmFtZS5zbGljZSh1bmRlcnNjb3JlSW5kZXggKyAyKTtcbiAgICB9XG4gICAgcmV0dXJuIGdvb2ROYW1lO1xuICB9O1xuXG4gIC8vIFRyYW5zbGF0ZSBhbGwgb3B0aW9ucyB0byB0aGUgbmV3IHN0eWxlLlxuICBmb3IgKGxldCBuYW1lIGluIG5ld09wdGlvbnMpIHtcbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eShuYW1lKSAmJiBuYW1lLmluZGV4T2YoJ18nKSAhPT0gLTEpIHtcbiAgICAgIGNvbnN0IGdvb2ROYW1lID0gdHJhbnNsYXRlTmFtZShuYW1lKTtcbiAgICAgIG5ld09wdGlvbnNbZ29vZE5hbWVdID0gbmV3T3B0aW9uc1tuYW1lXTtcbiAgICAgIGRlbGV0ZSBuZXdPcHRpb25zW25hbWVdO1xuICAgIH1cbiAgfVxuXG4gIGlmICghbW9kdWxlKSB7XG4gICAgLy8gT3B0aW9ucyB0aGF0IGhhdmUgY2hhbmdlZC5cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnYWRkY2xhc3MnKSkge1xuICAgICAgbmV3T3B0aW9ucy5hZGRDbGFzcyA9IG5ld09wdGlvbnMuYWRkY2xhc3M7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5hZGRjbGFzcztcbiAgICB9XG4gICAgaWYgKG5ld09wdGlvbnMuaGFzT3duUHJvcGVydHkoJ2Nvcm5lcmNsYXNzJykpIHtcbiAgICAgIG5ld09wdGlvbnMuY29ybmVyQ2xhc3MgPSBuZXdPcHRpb25zLmNvcm5lcmNsYXNzO1xuICAgICAgZGVsZXRlIG5ld09wdGlvbnMuY29ybmVyQ2xhc3M7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCd0ZXh0RXNjYXBlJykpIHtcbiAgICAgIG5ld09wdGlvbnMudGV4dFRydXN0ZWQgPSAhbmV3T3B0aW9ucy50ZXh0RXNjYXBlO1xuICAgICAgZGVsZXRlIG5ld09wdGlvbnMudGV4dEVzY2FwZTtcbiAgICB9XG4gICAgaWYgKG5ld09wdGlvbnMuaGFzT3duUHJvcGVydHkoJ3RpdGxlRXNjYXBlJykpIHtcbiAgICAgIG5ld09wdGlvbnMudGl0bGVUcnVzdGVkID0gIW5ld09wdGlvbnMudGl0bGVFc2NhcGU7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy50aXRsZUVzY2FwZTtcbiAgICB9XG5cbiAgICAvLyBTdHlsaW5nIGFuZCBpY29ucy5cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnc3R5bGluZycpKSB7XG4gICAgICBpZiAobmV3T3B0aW9ucy5zdHlsaW5nID09PSAnYm9vdHN0cmFwMycpIHtcbiAgICAgICAgbmV3T3B0aW9ucy5pY29ucyA9ICdib290c3RyYXAzJztcbiAgICAgIH0gZWxzZSBpZiAobmV3T3B0aW9ucy5zdHlsaW5nID09PSAnZm9udGF3ZXNvbWUnKSB7XG4gICAgICAgIG5ld09wdGlvbnMuc3R5bGluZyA9ICdib290c3RyYXAzJztcbiAgICAgICAgbmV3T3B0aW9ucy5pY29ucyA9ICdmb250YXdlc29tZTQnO1xuICAgICAgfVxuICAgIH1cblxuICAgIC8vIFN0YWNrcy5cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnc3RhY2snKSkge1xuICAgICAgaWYgKG5ld09wdGlvbnMuc3RhY2sub3ZlcmxheV9jbG9zZSkge1xuICAgICAgICBuZXdPcHRpb25zLnN0YWNrLm92ZXJsYXlDbG9zZSA9IG5ld09wdGlvbnMuc3RhY2sub3ZlcmxheV9jbG9zZTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICAvLyBUcmFuc2xhdGUgbW9kdWxlIG9wdGlvbnMuXG4gICAgbmV3T3B0aW9ucy5tb2R1bGVzID0ge307XG4gICAgaWYgKG5ld09wdGlvbnMuaGFzT3duUHJvcGVydHkoJ2FuaW1hdGUnKSkge1xuICAgICAgbmV3T3B0aW9ucy5tb2R1bGVzLkFuaW1hdGUgPSB0cmFuc2xhdGVPcHRpb25zKG5ld09wdGlvbnMuYW5pbWF0ZSwgdHJ1ZSwgJ2FuaW1hdGUnKTtcbiAgICAgIGRlbGV0ZSBuZXdPcHRpb25zLmFuaW1hdGU7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdidXR0b25zJykpIHtcbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5CdXR0b25zID0gdHJhbnNsYXRlT3B0aW9ucyhuZXdPcHRpb25zLmJ1dHRvbnMsIHRydWUsICdidXR0b25zJyk7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5idXR0b25zO1xuICAgICAgaWYgKG5ld09wdGlvbnMubW9kdWxlcy5CdXR0b25zLmNsYXNzZXMpIHtcbiAgICAgICAgbmV3T3B0aW9ucy5tb2R1bGVzLkJ1dHRvbnMuY2xhc3NlcyA9IHRyYW5zbGF0ZU9wdGlvbnMobmV3T3B0aW9ucy5tb2R1bGVzLkJ1dHRvbnMuY2xhc3NlcywgdHJ1ZSk7XG4gICAgICB9XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdjb25maXJtJykpIHtcbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5Db25maXJtID0gdHJhbnNsYXRlT3B0aW9ucyhuZXdPcHRpb25zLmNvbmZpcm0sIHRydWUsICdjb25maXJtJyk7XG4gICAgICBpZiAobmV3T3B0aW9ucy5tb2R1bGVzLkNvbmZpcm0ucHJvbXB0RGVmYXVsdCkge1xuICAgICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ29uZmlybS5wcm9tcHRWYWx1ZSA9IG5ld09wdGlvbnMubW9kdWxlcy5Db25maXJtLnByb21wdERlZmF1bHQ7XG4gICAgICAgIGRlbGV0ZSBuZXdPcHRpb25zLm1vZHVsZXMuQ29uZmlybS5wcm9tcHREZWZhdWx0O1xuICAgICAgfVxuICAgICAgZGVsZXRlIG5ld09wdGlvbnMuY29uZmlybTtcbiAgICB9XG4gICAgaWYgKG5ld09wdGlvbnMuaGFzT3duUHJvcGVydHkoJ2Rlc2t0b3AnKSkge1xuICAgICAgbmV3T3B0aW9ucy5tb2R1bGVzLkRlc2t0b3AgPSB0cmFuc2xhdGVPcHRpb25zKG5ld09wdGlvbnMuZGVza3RvcCwgdHJ1ZSwgJ2Rlc2t0b3AnKTtcbiAgICAgIGRlbGV0ZSBuZXdPcHRpb25zLmRlc2t0b3A7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdoaXN0b3J5JykpIHtcbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5IaXN0b3J5ID0gdHJhbnNsYXRlT3B0aW9ucyhuZXdPcHRpb25zLmhpc3RvcnksIHRydWUsICdoaXN0b3J5Jyk7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5oaXN0b3J5O1xuICAgIH1cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnbW9iaWxlJykpIHtcbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5Nb2JpbGUgPSB0cmFuc2xhdGVPcHRpb25zKG5ld09wdGlvbnMubW9iaWxlLCB0cnVlLCAnbW9iaWxlJyk7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5tb2JpbGU7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdub25ibG9jaycpKSB7XG4gICAgICBuZXdPcHRpb25zLm1vZHVsZXMuTm9uQmxvY2sgPSB0cmFuc2xhdGVPcHRpb25zKG5ld09wdGlvbnMubm9uYmxvY2ssIHRydWUsICdub25ibG9jaycpO1xuICAgICAgZGVsZXRlIG5ld09wdGlvbnMubm9uYmxvY2s7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdyZWZlcmVuY2UnKSkge1xuICAgICAgbmV3T3B0aW9ucy5tb2R1bGVzLlJlZmVyZW5jZSA9IHRyYW5zbGF0ZU9wdGlvbnMobmV3T3B0aW9ucy5yZWZlcmVuY2UsIHRydWUsICdyZWZlcmVuY2UnKTtcbiAgICAgIGRlbGV0ZSBuZXdPcHRpb25zLnJlZmVyZW5jZTtcbiAgICB9XG4gICAgaWYgKG5ld09wdGlvbnMuaGFzT3duUHJvcGVydHkoJ2JlZm9yZUluaXQnKSkge1xuICAgICAgaWYgKCFuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzKSB7XG4gICAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MgPSB7fTtcbiAgICAgIH1cbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MuYmVmb3JlSW5pdCA9IG5ld09wdGlvbnMuYmVmb3JlSW5pdDtcbiAgICAgIGRlbGV0ZSBuZXdPcHRpb25zLmJlZm9yZUluaXQ7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdhZnRlckluaXQnKSkge1xuICAgICAgaWYgKCFuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzKSB7XG4gICAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MgPSB7fTtcbiAgICAgIH1cbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MuYWZ0ZXJJbml0ID0gbmV3T3B0aW9ucy5hZnRlckluaXQ7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5hZnRlckluaXQ7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdiZWZvcmVPcGVuJykpIHtcbiAgICAgIGlmICghbmV3T3B0aW9ucy5tb2R1bGVzLkNhbGxiYWNrcykge1xuICAgICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzID0ge307XG4gICAgICB9XG4gICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzLmJlZm9yZU9wZW4gPSBuZXdPcHRpb25zLmJlZm9yZU9wZW47XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5iZWZvcmVPcGVuO1xuICAgIH1cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnYWZ0ZXJPcGVuJykpIHtcbiAgICAgIGlmICghbmV3T3B0aW9ucy5tb2R1bGVzLkNhbGxiYWNrcykge1xuICAgICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzID0ge307XG4gICAgICB9XG4gICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzLmFmdGVyT3BlbiA9IG5ld09wdGlvbnMuYWZ0ZXJPcGVuO1xuICAgICAgZGVsZXRlIG5ld09wdGlvbnMuYWZ0ZXJPcGVuO1xuICAgIH1cbiAgICBpZiAobmV3T3B0aW9ucy5oYXNPd25Qcm9wZXJ0eSgnYmVmb3JlQ2xvc2UnKSkge1xuICAgICAgaWYgKCFuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzKSB7XG4gICAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MgPSB7fTtcbiAgICAgIH1cbiAgICAgIG5ld09wdGlvbnMubW9kdWxlcy5DYWxsYmFja3MuYmVmb3JlQ2xvc2UgPSBuZXdPcHRpb25zLmJlZm9yZUNsb3NlO1xuICAgICAgZGVsZXRlIG5ld09wdGlvbnMuYmVmb3JlQ2xvc2U7XG4gICAgfVxuICAgIGlmIChuZXdPcHRpb25zLmhhc093blByb3BlcnR5KCdhZnRlckNsb3NlJykpIHtcbiAgICAgIGlmICghbmV3T3B0aW9ucy5tb2R1bGVzLkNhbGxiYWNrcykge1xuICAgICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzID0ge307XG4gICAgICB9XG4gICAgICBuZXdPcHRpb25zLm1vZHVsZXMuQ2FsbGJhY2tzLmFmdGVyQ2xvc2UgPSBuZXdPcHRpb25zLmFmdGVyQ2xvc2U7XG4gICAgICBkZWxldGUgbmV3T3B0aW9ucy5hZnRlckNsb3NlO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBuZXdPcHRpb25zO1xufTtcblxuLy8gVGhlIGNvbXBhdGliaWxpdHkgY2xhc3MuXG5jbGFzcyBQTm90aWZ5Q29tcGF0IGV4dGVuZHMgUE5vdGlmeSB7XG4gIGNvbnN0cnVjdG9yIChvcHRpb25zKSB7XG4gICAgaWYgKHR5cGVvZiBvcHRpb25zICE9PSAnb2JqZWN0Jykge1xuICAgICAgb3B0aW9ucyA9IHsgJ3RleHQnOiBvcHRpb25zIH07XG4gICAgfVxuXG4gICAgLy8gVGhlc2UgbmVlZCB0byBiZSBjYWxsZWQgZGlyZWN0bHksIHNpbmNlIHdlJ3JlIG5vdCB1c2luZyBQTm90aWZ5LmFsZXJ0KCkuXG4gICAgaWYgKFBOb3RpZnkubW9kdWxlcy5DYWxsYmFja3MgJiYgb3B0aW9ucy5iZWZvcmVfaW5pdCkge1xuICAgICAgb3B0aW9ucy5iZWZvcmVfaW5pdChvcHRpb25zKTtcbiAgICB9XG5cbiAgICBvcHRpb25zID0gdHJhbnNsYXRlT3B0aW9ucyhvcHRpb25zKTtcblxuICAgIHN1cGVyKHsgdGFyZ2V0OiBkb2N1bWVudC5ib2R5LCBkYXRhOiBvcHRpb25zIH0pO1xuXG4gICAgLy8gT3ZlcnJpZGUgdGhlIGdldCBmdW5jdGlvbiB0byByZXR1cm4gdGhlIGVsZW1lbnQgbGlrZSBpdCBkaWQgaW4gdjMuXG4gICAgY29uc3QgX2dldCA9IHRoaXMuZ2V0O1xuICAgIHRoaXMuZ2V0ID0gZnVuY3Rpb24gKG9wdGlvbikge1xuICAgICAgaWYgKG9wdGlvbiA9PT0gdW5kZWZpbmVkKSB7XG4gICAgICAgIHJldHVybiBPYmplY3QuYXNzaWduKHdpbmRvdy5qUXVlcnkgPyB3aW5kb3cualF1ZXJ5KHRoaXMucmVmcy5lbGVtKSA6IHRoaXMucmVmcy5lbGVtLCBfZ2V0LmNhbGwodGhpcykpO1xuICAgICAgfVxuICAgICAgcmV0dXJuIF9nZXQuY2FsbCh0aGlzLCBvcHRpb24pO1xuICAgIH07XG5cbiAgICAvLyBDb25maXJtIG1vZHVsZSBldmVudHMuXG4gICAgdGhpcy5vbigncG5vdGlmeS5jb25maXJtJywgKGUpID0+IHtcbiAgICAgIGlmICh3aW5kb3cualF1ZXJ5KSB7XG4gICAgICAgIHdpbmRvdy5qUXVlcnkodGhpcy5yZWZzLmVsZW0pLnRyaWdnZXIoJ3Bub3RpZnkuY29uZmlybScsIFt0aGlzLCBlLnZhbHVlXSk7XG4gICAgICB9XG4gICAgfSk7XG4gICAgdGhpcy5vbigncG5vdGlmeS5jYW5jZWwnLCAoZSkgPT4ge1xuICAgICAgaWYgKHdpbmRvdy5qUXVlcnkpIHtcbiAgICAgICAgd2luZG93LmpRdWVyeSh0aGlzLnJlZnMuZWxlbSkudHJpZ2dlcigncG5vdGlmeS5jYW5jZWwnLCB0aGlzKTtcbiAgICAgIH1cbiAgICB9KTtcblxuICAgIGlmIChQTm90aWZ5Lm1vZHVsZXMuQ2FsbGJhY2tzKSB7XG4gICAgICBQTm90aWZ5Lm1vZHVsZXMuQ2FsbGJhY2tzLmdldENhbGxiYWNrcyh0aGlzLCBudWxsLCAnYWZ0ZXJJbml0JykodGhpcyk7XG4gICAgfVxuICB9XG5cbiAgdXBkYXRlIChvcHRpb25zKSB7XG4gICAgb3B0aW9ucyA9IHRyYW5zbGF0ZU9wdGlvbnMob3B0aW9ucyk7XG4gICAgcmV0dXJuIHN1cGVyLnVwZGF0ZShvcHRpb25zKTtcbiAgfVxufVxuXG4vLyBMZXRzIHlvdSBjaGFuZ2UgZGVmYXVsdHMgdGhlIG9sZCB3YXkuXG5QTm90aWZ5Q29tcGF0LnByb3RvdHlwZS5vcHRpb25zID0ge1xuICB0ZXh0X2VzY2FwZTogZmFsc2UsXG4gIHRpdGxlX2VzY2FwZTogZmFsc2Vcbn07XG5cbi8vIEZvcndhcmQgc3RhdGljIGZ1bmN0aW9ucy5cblBOb3RpZnlDb21wYXQucmVsb2FkID0gKCkgPT4gUE5vdGlmeUNvbXBhdDtcblBOb3RpZnlDb21wYXQucmVtb3ZlQWxsID0gKCkgPT4gUE5vdGlmeS5yZW1vdmVBbGwoKTtcblBOb3RpZnlDb21wYXQucmVtb3ZlU3RhY2sgPSAoc3RhY2spID0+IFBOb3RpZnkucmVtb3ZlU3RhY2soc3RhY2spO1xuUE5vdGlmeUNvbXBhdC5wb3NpdGlvbkFsbCA9IChhbmltYXRlKSA9PiBQTm90aWZ5LnBvc2l0aW9uQWxsKGFuaW1hdGUpO1xuXG4vLyBEZXNrdG9wIG1vZHVsZSBwZXJtaXNzaW9uIG1ldGhvZC5cblBOb3RpZnlDb21wYXQuZGVza3RvcCA9IHtcbiAgcGVybWlzc2lvbjogKCkgPT4ge1xuICAgIFBOb3RpZnkubW9kdWxlcy5EZXNrdG9wLnBlcm1pc3Npb24oKTtcbiAgfVxufTtcblxuLy8gT2xkIHN0eWxlIHNob3dMYXN0KCkgaW4gSGlzdG9yeSBtb2R1bGUuXG5pZiAod2luZG93LmpRdWVyeSkge1xuICB3aW5kb3cualF1ZXJ5KCgpID0+IHtcbiAgICB3aW5kb3cualF1ZXJ5KGRvY3VtZW50LmJvZHkpLm9uKCdwbm90aWZ5Lmhpc3RvcnktbGFzdCcsIGZ1bmN0aW9uICgpIHtcbiAgICAgIFBOb3RpZnkubW9kdWxlcy5IaXN0b3J5LnNob3dMYXN0KCk7XG4gICAgfSk7XG4gIH0pO1xufVxuXG5leHBvcnQgZGVmYXVsdCBQTm90aWZ5Q29tcGF0O1xuIl19