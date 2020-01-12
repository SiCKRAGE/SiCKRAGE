Object.defineProperty(exports, "__esModule", { value: true });
var utils_1 = require("@sentry/utils");
var helpers_1 = require("../helpers");
/** Wrap timer functions and event targets to catch errors and provide better meta data */
var TryCatch = /** @class */ (function () {
    function TryCatch() {
        /** JSDoc */
        this._ignoreOnError = 0;
        /**
         * @inheritDoc
         */
        this.name = TryCatch.id;
    }
    /** JSDoc */
    TryCatch.prototype._wrapTimeFunction = function (original) {
        return function () {
            var args = [];
            for (var _i = 0; _i < arguments.length; _i++) {
                args[_i] = arguments[_i];
            }
            var originalCallback = args[0];
            args[0] = helpers_1.wrap(originalCallback, {
                mechanism: {
                    data: { function: utils_1.getFunctionName(original) },
                    handled: true,
                    type: 'instrument',
                },
            });
            return original.apply(this, args);
        };
    };
    /** JSDoc */
    TryCatch.prototype._wrapRAF = function (original) {
        return function (callback) {
            return original(helpers_1.wrap(callback, {
                mechanism: {
                    data: {
                        function: 'requestAnimationFrame',
                        handler: utils_1.getFunctionName(original),
                    },
                    handled: true,
                    type: 'instrument',
                },
            }));
        };
    };
    /** JSDoc */
    TryCatch.prototype._wrapEventTarget = function (target) {
        var global = utils_1.getGlobalObject();
        var proto = global[target] && global[target].prototype;
        if (!proto || !proto.hasOwnProperty || !proto.hasOwnProperty('addEventListener')) {
            return;
        }
        utils_1.fill(proto, 'addEventListener', function (original) {
            return function (eventName, fn, options) {
                try {
                    // tslint:disable-next-line:no-unbound-method strict-type-predicates
                    if (typeof fn.handleEvent === 'function') {
                        fn.handleEvent = helpers_1.wrap(fn.handleEvent.bind(fn), {
                            mechanism: {
                                data: {
                                    function: 'handleEvent',
                                    handler: utils_1.getFunctionName(fn),
                                    target: target,
                                },
                                handled: true,
                                type: 'instrument',
                            },
                        });
                    }
                }
                catch (err) {
                    // can sometimes get 'Permission denied to access property "handle Event'
                }
                return original.call(this, eventName, helpers_1.wrap(fn, {
                    mechanism: {
                        data: {
                            function: 'addEventListener',
                            handler: utils_1.getFunctionName(fn),
                            target: target,
                        },
                        handled: true,
                        type: 'instrument',
                    },
                }), options);
            };
        });
        utils_1.fill(proto, 'removeEventListener', function (original) {
            return function (eventName, fn, options) {
                var callback = fn;
                try {
                    callback = callback && (callback.__sentry_wrapped__ || callback);
                }
                catch (e) {
                    // ignore, accessing __sentry_wrapped__ will throw in some Selenium environments
                }
                return original.call(this, eventName, callback, options);
            };
        });
    };
    /** JSDoc */
    TryCatch.prototype._wrapXHR = function (originalSend) {
        return function () {
            var _this = this;
            var args = [];
            for (var _i = 0; _i < arguments.length; _i++) {
                args[_i] = arguments[_i];
            }
            var xhr = this; // tslint:disable-line:no-this-assignment
            var xmlHttpRequestProps = ['onload', 'onerror', 'onprogress'];
            xmlHttpRequestProps.forEach(function (prop) {
                if (prop in _this && typeof _this[prop] === 'function') {
                    utils_1.fill(_this, prop, function (original) {
                        return helpers_1.wrap(original, {
                            mechanism: {
                                data: {
                                    function: prop,
                                    handler: utils_1.getFunctionName(original),
                                },
                                handled: true,
                                type: 'instrument',
                            },
                        });
                    });
                }
            });
            if ('onreadystatechange' in xhr && typeof xhr.onreadystatechange === 'function') {
                utils_1.fill(xhr, 'onreadystatechange', function (original) {
                    var wrapOptions = {
                        mechanism: {
                            data: {
                                function: 'onreadystatechange',
                                handler: utils_1.getFunctionName(original),
                            },
                            handled: true,
                            type: 'instrument',
                        },
                    };
                    // If Instrument integration has been called before TryCatch, get the name of original function
                    if (original.__sentry_original__) {
                        wrapOptions.mechanism.data.handler = utils_1.getFunctionName(original.__sentry_original__);
                    }
                    // Otherwise wrap directly
                    return helpers_1.wrap(original, wrapOptions);
                });
            }
            return originalSend.apply(this, args);
        };
    };
    /**
     * Wrap timer functions and event targets to catch errors
     * and provide better metadata.
     */
    TryCatch.prototype.setupOnce = function () {
        this._ignoreOnError = this._ignoreOnError;
        var global = utils_1.getGlobalObject();
        utils_1.fill(global, 'setTimeout', this._wrapTimeFunction.bind(this));
        utils_1.fill(global, 'setInterval', this._wrapTimeFunction.bind(this));
        utils_1.fill(global, 'requestAnimationFrame', this._wrapRAF.bind(this));
        if ('XMLHttpRequest' in global) {
            utils_1.fill(XMLHttpRequest.prototype, 'send', this._wrapXHR.bind(this));
        }
        [
            'EventTarget',
            'Window',
            'Node',
            'ApplicationCache',
            'AudioTrackList',
            'ChannelMergerNode',
            'CryptoOperation',
            'EventSource',
            'FileReader',
            'HTMLUnknownElement',
            'IDBDatabase',
            'IDBRequest',
            'IDBTransaction',
            'KeyOperation',
            'MediaController',
            'MessagePort',
            'ModalWindow',
            'Notification',
            'SVGElementInstance',
            'Screen',
            'TextTrack',
            'TextTrackCue',
            'TextTrackList',
            'WebSocket',
            'WebSocketWorker',
            'Worker',
            'XMLHttpRequest',
            'XMLHttpRequestEventTarget',
            'XMLHttpRequestUpload',
        ].forEach(this._wrapEventTarget.bind(this));
    };
    /**
     * @inheritDoc
     */
    TryCatch.id = 'TryCatch';
    return TryCatch;
}());
exports.TryCatch = TryCatch;
//# sourceMappingURL=trycatch.js.map