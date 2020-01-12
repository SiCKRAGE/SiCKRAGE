Object.defineProperty(exports, "__esModule", { value: true });
var tslib_1 = require("tslib");
var core_1 = require("@sentry/core");
var types_1 = require("@sentry/types");
var utils_1 = require("@sentry/utils");
var eventbuilder_1 = require("../eventbuilder");
var helpers_1 = require("../helpers");
/** Global handlers */
var GlobalHandlers = /** @class */ (function () {
    /** JSDoc */
    function GlobalHandlers(options) {
        /**
         * @inheritDoc
         */
        this.name = GlobalHandlers.id;
        /** JSDoc */
        this._global = utils_1.getGlobalObject();
        /** JSDoc */
        this._oldOnErrorHandler = null;
        /** JSDoc */
        this._oldOnUnhandledRejectionHandler = null;
        /** JSDoc */
        this._onErrorHandlerInstalled = false;
        /** JSDoc */
        this._onUnhandledRejectionHandlerInstalled = false;
        this._options = tslib_1.__assign({ onerror: true, onunhandledrejection: true }, options);
    }
    /**
     * @inheritDoc
     */
    GlobalHandlers.prototype.setupOnce = function () {
        Error.stackTraceLimit = 50;
        if (this._options.onerror) {
            utils_1.logger.log('Global Handler attached: onerror');
            this._installGlobalOnErrorHandler();
        }
        if (this._options.onunhandledrejection) {
            utils_1.logger.log('Global Handler attached: onunhandledrejection');
            this._installGlobalOnUnhandledRejectionHandler();
        }
    };
    /** JSDoc */
    GlobalHandlers.prototype._installGlobalOnErrorHandler = function () {
        if (this._onErrorHandlerInstalled) {
            return;
        }
        var self = this; // tslint:disable-line:no-this-assignment
        this._oldOnErrorHandler = this._global.onerror;
        this._global.onerror = function (msg, url, line, column, error) {
            var currentHub = core_1.getCurrentHub();
            var hasIntegration = currentHub.getIntegration(GlobalHandlers);
            var isFailedOwnDelivery = error && error.__sentry_own_request__ === true;
            if (!hasIntegration || helpers_1.shouldIgnoreOnError() || isFailedOwnDelivery) {
                if (self._oldOnErrorHandler) {
                    return self._oldOnErrorHandler.apply(this, arguments);
                }
                return false;
            }
            var client = currentHub.getClient();
            var event = utils_1.isPrimitive(error)
                ? self._eventFromIncompleteOnError(msg, url, line, column)
                : self._enhanceEventWithInitialFrame(eventbuilder_1.eventFromUnknownInput(error, undefined, {
                    attachStacktrace: client && client.getOptions().attachStacktrace,
                    rejection: false,
                }), url, line, column);
            utils_1.addExceptionMechanism(event, {
                handled: false,
                type: 'onerror',
            });
            currentHub.captureEvent(event, {
                originalException: error,
            });
            if (self._oldOnErrorHandler) {
                return self._oldOnErrorHandler.apply(this, arguments);
            }
            return false;
        };
        this._onErrorHandlerInstalled = true;
    };
    /** JSDoc */
    GlobalHandlers.prototype._installGlobalOnUnhandledRejectionHandler = function () {
        if (this._onUnhandledRejectionHandlerInstalled) {
            return;
        }
        var self = this; // tslint:disable-line:no-this-assignment
        this._oldOnUnhandledRejectionHandler = this._global.onunhandledrejection;
        this._global.onunhandledrejection = function (e) {
            var error = e;
            try {
                error = e && 'reason' in e ? e.reason : e;
            }
            catch (_oO) {
                // no-empty
            }
            var currentHub = core_1.getCurrentHub();
            var hasIntegration = currentHub.getIntegration(GlobalHandlers);
            var isFailedOwnDelivery = error && error.__sentry_own_request__ === true;
            if (!hasIntegration || helpers_1.shouldIgnoreOnError() || isFailedOwnDelivery) {
                if (self._oldOnUnhandledRejectionHandler) {
                    return self._oldOnUnhandledRejectionHandler.apply(this, arguments);
                }
                return true;
            }
            var client = currentHub.getClient();
            var event = utils_1.isPrimitive(error)
                ? self._eventFromIncompleteRejection(error)
                : eventbuilder_1.eventFromUnknownInput(error, undefined, {
                    attachStacktrace: client && client.getOptions().attachStacktrace,
                    rejection: true,
                });
            event.level = types_1.Severity.Error;
            utils_1.addExceptionMechanism(event, {
                handled: false,
                type: 'onunhandledrejection',
            });
            currentHub.captureEvent(event, {
                originalException: error,
            });
            if (self._oldOnUnhandledRejectionHandler) {
                return self._oldOnUnhandledRejectionHandler.apply(this, arguments);
            }
            return true;
        };
        this._onUnhandledRejectionHandlerInstalled = true;
    };
    /**
     * This function creates a stack from an old, error-less onerror handler.
     */
    GlobalHandlers.prototype._eventFromIncompleteOnError = function (msg, url, line, column) {
        var ERROR_TYPES_RE = /^(?:[Uu]ncaught (?:exception: )?)?(?:((?:Eval|Internal|Range|Reference|Syntax|Type|URI|)Error): )?(.*)$/i;
        // If 'message' is ErrorEvent, get real message from inside
        var message = utils_1.isErrorEvent(msg) ? msg.message : msg;
        var name;
        if (utils_1.isString(message)) {
            var groups = message.match(ERROR_TYPES_RE);
            if (groups) {
                name = groups[1];
                message = groups[2];
            }
        }
        var event = {
            exception: {
                values: [
                    {
                        type: name || 'Error',
                        value: message,
                    },
                ],
            },
        };
        return this._enhanceEventWithInitialFrame(event, url, line, column);
    };
    /**
     * This function creates an Event from an TraceKitStackTrace that has part of it missing.
     */
    GlobalHandlers.prototype._eventFromIncompleteRejection = function (error) {
        return {
            exception: {
                values: [
                    {
                        type: 'UnhandledRejection',
                        value: "Non-Error promise rejection captured with value: " + error,
                    },
                ],
            },
        };
    };
    /** JSDoc */
    GlobalHandlers.prototype._enhanceEventWithInitialFrame = function (event, url, line, column) {
        event.exception = event.exception || {};
        event.exception.values = event.exception.values || [];
        event.exception.values[0] = event.exception.values[0] || {};
        event.exception.values[0].stacktrace = event.exception.values[0].stacktrace || {};
        event.exception.values[0].stacktrace.frames = event.exception.values[0].stacktrace.frames || [];
        var colno = isNaN(parseInt(column, 10)) ? undefined : column;
        var lineno = isNaN(parseInt(line, 10)) ? undefined : line;
        var filename = utils_1.isString(url) && url.length > 0 ? url : utils_1.getLocationHref();
        if (event.exception.values[0].stacktrace.frames.length === 0) {
            event.exception.values[0].stacktrace.frames.push({
                colno: colno,
                filename: filename,
                function: '?',
                in_app: true,
                lineno: lineno,
            });
        }
        return event;
    };
    /**
     * @inheritDoc
     */
    GlobalHandlers.id = 'GlobalHandlers';
    return GlobalHandlers;
}());
exports.GlobalHandlers = GlobalHandlers;
//# sourceMappingURL=globalhandlers.js.map