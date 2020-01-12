(function (__window) {
var exports = {};

Object.defineProperty(exports, '__esModule', { value: true });

/*! *****************************************************************************
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
MERCHANTABLITY OR NON-INFRINGEMENT.

See the Apache Version 2.0 License for specific language governing permissions
and limitations under the License.
***************************************************************************** */
/* global Reflect, Promise */

var extendStatics = function(d, b) {
    extendStatics = Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
        function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
    return extendStatics(d, b);
};

function __extends(d, b) {
    extendStatics(d, b);
    function __() { this.constructor = d; }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
}

var __assign = function() {
    __assign = Object.assign || function __assign(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};

/**
 * Consumes the promise and logs the error when it rejects.
 * @param promise A promise to forget.
 */

var setPrototypeOf = Object.setPrototypeOf || ({ __proto__: [] } instanceof Array ? setProtoOf : mixinProperties); // tslint:disable-line:no-unbound-method
/**
 * setPrototypeOf polyfill using __proto__
 */
function setProtoOf(obj, proto) {
    // @ts-ignore
    obj.__proto__ = proto;
    return obj;
}
/**
 * setPrototypeOf polyfill using mixin
 */
function mixinProperties(obj, proto) {
    for (var prop in proto) {
        if (!obj.hasOwnProperty(prop)) {
            // @ts-ignore
            obj[prop] = proto[prop];
        }
    }
    return obj;
}

/** An error emitted by Sentry SDKs and related utilities. */
var SentryError = /** @class */ (function (_super) {
    __extends(SentryError, _super);
    function SentryError(message) {
        var _newTarget = this.constructor;
        var _this = _super.call(this, message) || this;
        _this.message = message;
        // tslint:disable:no-unsafe-any
        _this.name = _newTarget.prototype.constructor.name;
        setPrototypeOf(_this, _newTarget.prototype);
        return _this;
    }
    return SentryError;
}(Error));

/**
 * Checks whether given value's type is one of a few Error or Error-like
 * {@link isError}.
 *
 * @param wat A value to be checked.
 * @returns A boolean representing the result.
 */

/**
 * Checks whether we're in the Node.js or Browser environment
 *
 * @returns Answer to given question
 */
function isNodeEnv() {
    // tslint:disable:strict-type-predicates
    return Object.prototype.toString.call(typeof process !== 'undefined' ? process : 0) === '[object process]';
}
var fallbackGlobalObject = {};
/**
 * Safely get global scope object
 *
 * @returns Global scope object
 */
function getGlobalObject() {
    return (isNodeEnv()
        ? global
        : typeof window !== 'undefined'
            ? window
            : typeof self !== 'undefined'
                ? self
                : fallbackGlobalObject);
}
/** JSDoc */
function consoleSandbox(callback) {
    var global = getGlobalObject();
    var levels = ['debug', 'info', 'warn', 'error', 'log', 'assert'];
    if (!('console' in global)) {
        return callback();
    }
    var originalConsole = global.console;
    var wrappedLevels = {};
    // Restore all wrapped console methods
    levels.forEach(function (level) {
        if (level in global.console && originalConsole[level].__sentry_original__) {
            wrappedLevels[level] = originalConsole[level];
            originalConsole[level] = originalConsole[level].__sentry_original__;
        }
    });
    // Perform callback manipulations
    var result = callback();
    // Revert restoration to wrapped state
    Object.keys(wrappedLevels).forEach(function (level) {
        originalConsole[level] = wrappedLevels[level];
    });
    return result;
}

// TODO: Implement different loggers for different environments
var global$1 = getGlobalObject();
/** Prefix for logging strings */
var PREFIX = 'Sentry Logger ';
/** JSDoc */
var Logger = /** @class */ (function () {
    /** JSDoc */
    function Logger() {
        this._enabled = false;
    }
    /** JSDoc */
    Logger.prototype.disable = function () {
        this._enabled = false;
    };
    /** JSDoc */
    Logger.prototype.enable = function () {
        this._enabled = true;
    };
    /** JSDoc */
    Logger.prototype.log = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            global$1.console.log(PREFIX + "[Log]: " + args.join(' ')); // tslint:disable-line:no-console
        });
    };
    /** JSDoc */
    Logger.prototype.warn = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            global$1.console.warn(PREFIX + "[Warn]: " + args.join(' ')); // tslint:disable-line:no-console
        });
    };
    /** JSDoc */
    Logger.prototype.error = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            global$1.console.error(PREFIX + "[Error]: " + args.join(' ')); // tslint:disable-line:no-console
        });
    };
    return Logger;
}());
// Ensure we only have a single logger instance, even if multiple versions of @sentry/utils are being used
global$1.__SENTRY__ = global$1.__SENTRY__ || {};
var logger = global$1.__SENTRY__.logger || (global$1.__SENTRY__.logger = new Logger());

// tslint:disable:no-unsafe-any

// Slightly modified (no IE8 support, ES6) and transcribed to TypeScript

/** SyncPromise internal states */
var States;
(function (States) {
    /** Pending */
    States["PENDING"] = "PENDING";
    /** Resolved / OK */
    States["RESOLVED"] = "RESOLVED";
    /** Rejected / Error */
    States["REJECTED"] = "REJECTED";
})(States || (States = {}));

/* tslint:disable:only-arrow-functions no-unsafe-any */
var global$2 = getGlobalObject();

// See https://github.com/angular/angular.js/blob/v1.4.7/src/minErr.js
var angularPattern = /^\[((?:[$a-zA-Z0-9]+:)?(?:[$a-zA-Z0-9]+))\] (.*?)\n?(\S+)$/;
/**
 * AngularJS integration
 *
 * Provides an $exceptionHandler for AngularJS
 */
var Angular = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Angular(options) {
        if (options === void 0) { options = {}; }
        /**
         * @inheritDoc
         */
        this.name = Angular.id;
        // tslint:disable-next-line: no-unsafe-any
        this._angular = options.angular || getGlobalObject().angular;
    }
    /**
     * @inheritDoc
     */
    Angular.prototype.setupOnce = function (_, getCurrentHub) {
        var _this = this;
        if (!this._angular) {
            logger.error('AngularIntegration is missing an Angular instance');
            return;
        }
        this._getCurrentHub = getCurrentHub;
        // tslint:disable: no-unsafe-any
        this._angular.module(Angular.moduleName, []).config([
            '$provide',
            function ($provide) {
                $provide.decorator('$exceptionHandler', ['$delegate', _this._$exceptionHandlerDecorator.bind(_this)]);
            },
        ]);
        // tslint:enable: no-unsafe-any
    };
    /**
     * Angular's exceptionHandler for Sentry integration
     */
    // tslint:disable-next-line: no-unsafe-any
    Angular.prototype._$exceptionHandlerDecorator = function ($delegate) {
        var _this = this;
        return function (exception, cause) {
            var hub = _this._getCurrentHub && _this._getCurrentHub();
            if (hub && hub.getIntegration(Angular)) {
                hub.withScope(function (scope) {
                    if (cause) {
                        scope.setExtra('cause', cause);
                    }
                    scope.addEventProcessor(function (event) {
                        var ex = event.exception && event.exception.values && event.exception.values[0];
                        if (ex) {
                            var matches = angularPattern.exec(ex.value || '');
                            if (matches) {
                                // This type now becomes something like: $rootScope:inprog
                                ex.type = matches[1];
                                ex.value = matches[2];
                                event.message = ex.type + ": " + ex.value;
                                // auto set a new tag specifically for the angular error url
                                event.extra = __assign({}, event.extra, { angularDocs: matches[3].substr(0, 250) });
                            }
                        }
                        return event;
                    });
                    hub.captureException(exception);
                });
            }
            // tslint:disable-next-line: no-unsafe-any
            $delegate(exception, cause);
        };
    };
    /**
     * @inheritDoc
     */
    Angular.id = 'AngularJS';
    /**
     * moduleName used in Angular's DI resolution algorithm
     */
    Angular.moduleName = 'ngSentry';
    return Angular;
}());

exports.Angular = Angular;


  __window.Sentry = __window.Sentry || {};
  __window.Sentry.Integrations = __window.Sentry.Integrations || {};
  for (var key in exports) {
    if (Object.prototype.hasOwnProperty.call(exports, key)) {
      __window.Sentry.Integrations[key] = exports[key];
    }
  }
  
}(window));
//# sourceMappingURL=angular.js.map
