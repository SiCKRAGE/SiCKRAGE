define(['exports', './utils', './exception', './helpers', './decorators', './logger'], function (exports, _utils, _exception, _helpers, _decorators, _logger) {
  'use strict';

  exports.__esModule = true;
  exports.HandlebarsEnvironment = HandlebarsEnvironment;
  // istanbul ignore next

  function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { 'default': obj }; }

  var _Exception = _interopRequireDefault(_exception);

  var _logger2 = _interopRequireDefault(_logger);

  var VERSION = '4.7.0';
  exports.VERSION = VERSION;
  var COMPILER_REVISION = 8;
  exports.COMPILER_REVISION = COMPILER_REVISION;
  var LAST_COMPATIBLE_COMPILER_REVISION = 7;

  exports.LAST_COMPATIBLE_COMPILER_REVISION = LAST_COMPATIBLE_COMPILER_REVISION;
  var REVISION_CHANGES = {
    1: '<= 1.0.rc.2', // 1.0.rc.2 is actually rev2 but doesn't report it
    2: '== 1.0.0-rc.3',
    3: '== 1.0.0-rc.4',
    4: '== 1.x.x',
    5: '== 2.0.0-alpha.x',
    6: '>= 2.0.0-beta.1',
    7: '>= 4.0.0 <4.3.0',
    8: '>= 4.3.0'
  };

  exports.REVISION_CHANGES = REVISION_CHANGES;
  var objectType = '[object Object]';

  function HandlebarsEnvironment(helpers, partials, decorators) {
    this.helpers = helpers || {};
    this.partials = partials || {};
    this.decorators = decorators || {};

    _helpers.registerDefaultHelpers(this);
    _decorators.registerDefaultDecorators(this);
  }

  HandlebarsEnvironment.prototype = {
    constructor: HandlebarsEnvironment,

    logger: _logger2['default'],
    log: _logger2['default'].log,

    registerHelper: function registerHelper(name, fn) {
      if (_utils.toString.call(name) === objectType) {
        if (fn) {
          throw new _Exception['default']('Arg not supported with multiple helpers');
        }
        _utils.extend(this.helpers, name);
      } else {
        this.helpers[name] = fn;
      }
    },
    unregisterHelper: function unregisterHelper(name) {
      delete this.helpers[name];
    },

    registerPartial: function registerPartial(name, partial) {
      if (_utils.toString.call(name) === objectType) {
        _utils.extend(this.partials, name);
      } else {
        if (typeof partial === 'undefined') {
          throw new _Exception['default']('Attempting to register a partial called "' + name + '" as undefined');
        }
        this.partials[name] = partial;
      }
    },
    unregisterPartial: function unregisterPartial(name) {
      delete this.partials[name];
    },

    registerDecorator: function registerDecorator(name, fn) {
      if (_utils.toString.call(name) === objectType) {
        if (fn) {
          throw new _Exception['default']('Arg not supported with multiple decorators');
        }
        _utils.extend(this.decorators, name);
      } else {
        this.decorators[name] = fn;
      }
    },
    unregisterDecorator: function unregisterDecorator(name) {
      delete this.decorators[name];
    }
  };

  var log = _logger2['default'].log;

  exports.log = log;
  exports.createFrame = _utils.createFrame;
  exports.logger = _logger2['default'];
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi4uLy4uLy4uL2xpYi9oYW5kbGViYXJzL2Jhc2UuanMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7Ozs7OztBQU1PLE1BQU0sT0FBTyxHQUFHLE9BQU8sQ0FBQzs7QUFDeEIsTUFBTSxpQkFBaUIsR0FBRyxDQUFDLENBQUM7O0FBQzVCLE1BQU0saUNBQWlDLEdBQUcsQ0FBQyxDQUFDOzs7QUFFNUMsTUFBTSxnQkFBZ0IsR0FBRztBQUM5QixLQUFDLEVBQUUsYUFBYTtBQUNoQixLQUFDLEVBQUUsZUFBZTtBQUNsQixLQUFDLEVBQUUsZUFBZTtBQUNsQixLQUFDLEVBQUUsVUFBVTtBQUNiLEtBQUMsRUFBRSxrQkFBa0I7QUFDckIsS0FBQyxFQUFFLGlCQUFpQjtBQUNwQixLQUFDLEVBQUUsaUJBQWlCO0FBQ3BCLEtBQUMsRUFBRSxVQUFVO0dBQ2QsQ0FBQzs7O0FBRUYsTUFBTSxVQUFVLEdBQUcsaUJBQWlCLENBQUM7O0FBRTlCLFdBQVMscUJBQXFCLENBQUMsT0FBTyxFQUFFLFFBQVEsRUFBRSxVQUFVLEVBQUU7QUFDbkUsUUFBSSxDQUFDLE9BQU8sR0FBRyxPQUFPLElBQUksRUFBRSxDQUFDO0FBQzdCLFFBQUksQ0FBQyxRQUFRLEdBQUcsUUFBUSxJQUFJLEVBQUUsQ0FBQztBQUMvQixRQUFJLENBQUMsVUFBVSxHQUFHLFVBQVUsSUFBSSxFQUFFLENBQUM7O0FBRW5DLGFBMUJPLHNCQUFzQixDQTBCTixJQUFJLENBQUMsQ0FBQztBQUM3QixnQkExQk8seUJBQXlCLENBMEJOLElBQUksQ0FBQyxDQUFDO0dBQ2pDOztBQUVELHVCQUFxQixDQUFDLFNBQVMsR0FBRztBQUNoQyxlQUFXLEVBQUUscUJBQXFCOztBQUVsQyxVQUFNLHFCQUFRO0FBQ2QsT0FBRyxFQUFFLG9CQUFPLEdBQUc7O0FBRWYsa0JBQWMsRUFBRSx3QkFBUyxJQUFJLEVBQUUsRUFBRSxFQUFFO0FBQ2pDLFVBQUksT0F2Q3NCLFFBQVEsQ0F1Q3JCLElBQUksQ0FBQyxJQUFJLENBQUMsS0FBSyxVQUFVLEVBQUU7QUFDdEMsWUFBSSxFQUFFLEVBQUU7QUFDTixnQkFBTSwwQkFBYyx5Q0FBeUMsQ0FBQyxDQUFDO1NBQ2hFO0FBQ0QsZUEzQ2dCLE1BQU0sQ0EyQ2YsSUFBSSxDQUFDLE9BQU8sRUFBRSxJQUFJLENBQUMsQ0FBQztPQUM1QixNQUFNO0FBQ0wsWUFBSSxDQUFDLE9BQU8sQ0FBQyxJQUFJLENBQUMsR0FBRyxFQUFFLENBQUM7T0FDekI7S0FDRjtBQUNELG9CQUFnQixFQUFFLDBCQUFTLElBQUksRUFBRTtBQUMvQixhQUFPLElBQUksQ0FBQyxPQUFPLENBQUMsSUFBSSxDQUFDLENBQUM7S0FDM0I7O0FBRUQsbUJBQWUsRUFBRSx5QkFBUyxJQUFJLEVBQUUsT0FBTyxFQUFFO0FBQ3ZDLFVBQUksT0FyRHNCLFFBQVEsQ0FxRHJCLElBQUksQ0FBQyxJQUFJLENBQUMsS0FBSyxVQUFVLEVBQUU7QUFDdEMsZUF0RGdCLE1BQU0sQ0FzRGYsSUFBSSxDQUFDLFFBQVEsRUFBRSxJQUFJLENBQUMsQ0FBQztPQUM3QixNQUFNO0FBQ0wsWUFBSSxPQUFPLE9BQU8sS0FBSyxXQUFXLEVBQUU7QUFDbEMsZ0JBQU0sd0VBQ3dDLElBQUksb0JBQ2pELENBQUM7U0FDSDtBQUNELFlBQUksQ0FBQyxRQUFRLENBQUMsSUFBSSxDQUFDLEdBQUcsT0FBTyxDQUFDO09BQy9CO0tBQ0Y7QUFDRCxxQkFBaUIsRUFBRSwyQkFBUyxJQUFJLEVBQUU7QUFDaEMsYUFBTyxJQUFJLENBQUMsUUFBUSxDQUFDLElBQUksQ0FBQyxDQUFDO0tBQzVCOztBQUVELHFCQUFpQixFQUFFLDJCQUFTLElBQUksRUFBRSxFQUFFLEVBQUU7QUFDcEMsVUFBSSxPQXJFc0IsUUFBUSxDQXFFckIsSUFBSSxDQUFDLElBQUksQ0FBQyxLQUFLLFVBQVUsRUFBRTtBQUN0QyxZQUFJLEVBQUUsRUFBRTtBQUNOLGdCQUFNLDBCQUFjLDRDQUE0QyxDQUFDLENBQUM7U0FDbkU7QUFDRCxlQXpFZ0IsTUFBTSxDQXlFZixJQUFJLENBQUMsVUFBVSxFQUFFLElBQUksQ0FBQyxDQUFDO09BQy9CLE1BQU07QUFDTCxZQUFJLENBQUMsVUFBVSxDQUFDLElBQUksQ0FBQyxHQUFHLEVBQUUsQ0FBQztPQUM1QjtLQUNGO0FBQ0QsdUJBQW1CLEVBQUUsNkJBQVMsSUFBSSxFQUFFO0FBQ2xDLGFBQU8sSUFBSSxDQUFDLFVBQVUsQ0FBQyxJQUFJLENBQUMsQ0FBQztLQUM5QjtHQUNGLENBQUM7O0FBRUssTUFBSSxHQUFHLEdBQUcsb0JBQU8sR0FBRyxDQUFDOzs7VUFFbkIsV0FBVyxVQXJGWCxXQUFXO1VBcUZFLE1BQU0iLCJmaWxlIjoiYmFzZS5qcyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IGNyZWF0ZUZyYW1lLCBleHRlbmQsIHRvU3RyaW5nIH0gZnJvbSAnLi91dGlscyc7XG5pbXBvcnQgRXhjZXB0aW9uIGZyb20gJy4vZXhjZXB0aW9uJztcbmltcG9ydCB7IHJlZ2lzdGVyRGVmYXVsdEhlbHBlcnMgfSBmcm9tICcuL2hlbHBlcnMnO1xuaW1wb3J0IHsgcmVnaXN0ZXJEZWZhdWx0RGVjb3JhdG9ycyB9IGZyb20gJy4vZGVjb3JhdG9ycyc7XG5pbXBvcnQgbG9nZ2VyIGZyb20gJy4vbG9nZ2VyJztcblxuZXhwb3J0IGNvbnN0IFZFUlNJT04gPSAnNC43LjAnO1xuZXhwb3J0IGNvbnN0IENPTVBJTEVSX1JFVklTSU9OID0gODtcbmV4cG9ydCBjb25zdCBMQVNUX0NPTVBBVElCTEVfQ09NUElMRVJfUkVWSVNJT04gPSA3O1xuXG5leHBvcnQgY29uc3QgUkVWSVNJT05fQ0hBTkdFUyA9IHtcbiAgMTogJzw9IDEuMC5yYy4yJywgLy8gMS4wLnJjLjIgaXMgYWN0dWFsbHkgcmV2MiBidXQgZG9lc24ndCByZXBvcnQgaXRcbiAgMjogJz09IDEuMC4wLXJjLjMnLFxuICAzOiAnPT0gMS4wLjAtcmMuNCcsXG4gIDQ6ICc9PSAxLngueCcsXG4gIDU6ICc9PSAyLjAuMC1hbHBoYS54JyxcbiAgNjogJz49IDIuMC4wLWJldGEuMScsXG4gIDc6ICc+PSA0LjAuMCA8NC4zLjAnLFxuICA4OiAnPj0gNC4zLjAnXG59O1xuXG5jb25zdCBvYmplY3RUeXBlID0gJ1tvYmplY3QgT2JqZWN0XSc7XG5cbmV4cG9ydCBmdW5jdGlvbiBIYW5kbGViYXJzRW52aXJvbm1lbnQoaGVscGVycywgcGFydGlhbHMsIGRlY29yYXRvcnMpIHtcbiAgdGhpcy5oZWxwZXJzID0gaGVscGVycyB8fCB7fTtcbiAgdGhpcy5wYXJ0aWFscyA9IHBhcnRpYWxzIHx8IHt9O1xuICB0aGlzLmRlY29yYXRvcnMgPSBkZWNvcmF0b3JzIHx8IHt9O1xuXG4gIHJlZ2lzdGVyRGVmYXVsdEhlbHBlcnModGhpcyk7XG4gIHJlZ2lzdGVyRGVmYXVsdERlY29yYXRvcnModGhpcyk7XG59XG5cbkhhbmRsZWJhcnNFbnZpcm9ubWVudC5wcm90b3R5cGUgPSB7XG4gIGNvbnN0cnVjdG9yOiBIYW5kbGViYXJzRW52aXJvbm1lbnQsXG5cbiAgbG9nZ2VyOiBsb2dnZXIsXG4gIGxvZzogbG9nZ2VyLmxvZyxcblxuICByZWdpc3RlckhlbHBlcjogZnVuY3Rpb24obmFtZSwgZm4pIHtcbiAgICBpZiAodG9TdHJpbmcuY2FsbChuYW1lKSA9PT0gb2JqZWN0VHlwZSkge1xuICAgICAgaWYgKGZuKSB7XG4gICAgICAgIHRocm93IG5ldyBFeGNlcHRpb24oJ0FyZyBub3Qgc3VwcG9ydGVkIHdpdGggbXVsdGlwbGUgaGVscGVycycpO1xuICAgICAgfVxuICAgICAgZXh0ZW5kKHRoaXMuaGVscGVycywgbmFtZSk7XG4gICAgfSBlbHNlIHtcbiAgICAgIHRoaXMuaGVscGVyc1tuYW1lXSA9IGZuO1xuICAgIH1cbiAgfSxcbiAgdW5yZWdpc3RlckhlbHBlcjogZnVuY3Rpb24obmFtZSkge1xuICAgIGRlbGV0ZSB0aGlzLmhlbHBlcnNbbmFtZV07XG4gIH0sXG5cbiAgcmVnaXN0ZXJQYXJ0aWFsOiBmdW5jdGlvbihuYW1lLCBwYXJ0aWFsKSB7XG4gICAgaWYgKHRvU3RyaW5nLmNhbGwobmFtZSkgPT09IG9iamVjdFR5cGUpIHtcbiAgICAgIGV4dGVuZCh0aGlzLnBhcnRpYWxzLCBuYW1lKTtcbiAgICB9IGVsc2Uge1xuICAgICAgaWYgKHR5cGVvZiBwYXJ0aWFsID09PSAndW5kZWZpbmVkJykge1xuICAgICAgICB0aHJvdyBuZXcgRXhjZXB0aW9uKFxuICAgICAgICAgIGBBdHRlbXB0aW5nIHRvIHJlZ2lzdGVyIGEgcGFydGlhbCBjYWxsZWQgXCIke25hbWV9XCIgYXMgdW5kZWZpbmVkYFxuICAgICAgICApO1xuICAgICAgfVxuICAgICAgdGhpcy5wYXJ0aWFsc1tuYW1lXSA9IHBhcnRpYWw7XG4gICAgfVxuICB9LFxuICB1bnJlZ2lzdGVyUGFydGlhbDogZnVuY3Rpb24obmFtZSkge1xuICAgIGRlbGV0ZSB0aGlzLnBhcnRpYWxzW25hbWVdO1xuICB9LFxuXG4gIHJlZ2lzdGVyRGVjb3JhdG9yOiBmdW5jdGlvbihuYW1lLCBmbikge1xuICAgIGlmICh0b1N0cmluZy5jYWxsKG5hbWUpID09PSBvYmplY3RUeXBlKSB7XG4gICAgICBpZiAoZm4pIHtcbiAgICAgICAgdGhyb3cgbmV3IEV4Y2VwdGlvbignQXJnIG5vdCBzdXBwb3J0ZWQgd2l0aCBtdWx0aXBsZSBkZWNvcmF0b3JzJyk7XG4gICAgICB9XG4gICAgICBleHRlbmQodGhpcy5kZWNvcmF0b3JzLCBuYW1lKTtcbiAgICB9IGVsc2Uge1xuICAgICAgdGhpcy5kZWNvcmF0b3JzW25hbWVdID0gZm47XG4gICAgfVxuICB9LFxuICB1bnJlZ2lzdGVyRGVjb3JhdG9yOiBmdW5jdGlvbihuYW1lKSB7XG4gICAgZGVsZXRlIHRoaXMuZGVjb3JhdG9yc1tuYW1lXTtcbiAgfVxufTtcblxuZXhwb3J0IGxldCBsb2cgPSBsb2dnZXIubG9nO1xuXG5leHBvcnQgeyBjcmVhdGVGcmFtZSwgbG9nZ2VyIH07XG4iXX0=
