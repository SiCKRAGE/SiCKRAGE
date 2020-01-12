Object.defineProperty(exports, "__esModule", { value: true });
var types_1 = require("@sentry/types");
var utils_1 = require("@sentry/utils");
var global = utils_1.getGlobalObject();
/** Send Console API calls as Sentry Events */
var CaptureConsole = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function CaptureConsole(options) {
        if (options === void 0) { options = {}; }
        /**
         * @inheritDoc
         */
        this.name = CaptureConsole.id;
        /**
         * @inheritDoc
         */
        this._levels = ['log', 'info', 'warn', 'error', 'debug', 'assert'];
        if (options.levels) {
            this._levels = options.levels;
        }
    }
    /**
     * @inheritDoc
     */
    CaptureConsole.prototype.setupOnce = function (_, getCurrentHub) {
        if (!('console' in global)) {
            return;
        }
        this._levels.forEach(function (level) {
            if (!(level in global.console)) {
                return;
            }
            utils_1.fill(global.console, level, function (originalConsoleLevel) { return function () {
                var args = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    args[_i] = arguments[_i];
                }
                var hub = getCurrentHub();
                if (hub.getIntegration(CaptureConsole)) {
                    hub.withScope(function (scope) {
                        scope.setLevel(types_1.Severity.fromString(level));
                        scope.setExtra('arguments', utils_1.normalize(args, 3));
                        scope.addEventProcessor(function (event) {
                            event.logger = 'console';
                            return event;
                        });
                        var message = utils_1.safeJoin(args, ' ');
                        if (level === 'assert') {
                            if (args[0] === false) {
                                message = "Assertion failed: " + (utils_1.safeJoin(args.slice(1), ' ') || 'console.assert');
                                scope.setExtra('arguments', utils_1.normalize(args.slice(1), 3));
                                hub.captureMessage(message);
                            }
                        }
                        else {
                            hub.captureMessage(message);
                        }
                    });
                }
                // this fails for some browsers. :(
                if (originalConsoleLevel) {
                    Function.prototype.apply.call(originalConsoleLevel, global.console, args);
                }
            }; });
        });
    };
    /**
     * @inheritDoc
     */
    CaptureConsole.id = 'CaptureConsole';
    return CaptureConsole;
}());
exports.CaptureConsole = CaptureConsole;
//# sourceMappingURL=captureconsole.js.map