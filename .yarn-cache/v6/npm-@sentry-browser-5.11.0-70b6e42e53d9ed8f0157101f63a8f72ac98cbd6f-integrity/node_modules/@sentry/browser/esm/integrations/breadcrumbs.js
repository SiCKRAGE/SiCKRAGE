import * as tslib_1 from "tslib";
import { API, getCurrentHub } from '@sentry/core';
import { Severity } from '@sentry/types';
import { addInstrumentationHandler, getEventDescription, getGlobalObject, htmlTreeAsString, logger, normalize, parseUrl, safeJoin, } from '@sentry/utils';
/**
 * Default Breadcrumbs instrumentations
 * TODO: Deprecated - with v6, this will be renamed to `Instrument`
 */
var Breadcrumbs = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Breadcrumbs(options) {
        /**
         * @inheritDoc
         */
        this.name = Breadcrumbs.id;
        this._options = tslib_1.__assign({ console: true, dom: true, fetch: true, history: true, sentry: true, xhr: true }, options);
    }
    /**
     * Creates breadcrumbs from console API calls
     */
    Breadcrumbs.prototype._consoleBreadcrumb = function (handlerData) {
        var breadcrumb = {
            category: 'console',
            data: {
                extra: {
                    arguments: normalize(handlerData.args, 3),
                },
                logger: 'console',
            },
            level: Severity.fromString(handlerData.level),
            message: safeJoin(handlerData.args, ' '),
        };
        if (handlerData.level === 'assert') {
            if (handlerData.args[0] === false) {
                breadcrumb.message = "Assertion failed: " + (safeJoin(handlerData.args.slice(1), ' ') || 'console.assert');
                breadcrumb.data.extra.arguments = normalize(handlerData.args.slice(1), 3);
            }
            else {
                // Don't capture a breadcrumb for passed assertions
                return;
            }
        }
        getCurrentHub().addBreadcrumb(breadcrumb, {
            input: handlerData.args,
            level: handlerData.level,
        });
    };
    /**
     * Creates breadcrumbs from DOM API calls
     */
    Breadcrumbs.prototype._domBreadcrumb = function (handlerData) {
        var target;
        // Accessing event.target can throw (see getsentry/raven-js#838, #768)
        try {
            target = handlerData.event.target
                ? htmlTreeAsString(handlerData.event.target)
                : htmlTreeAsString(handlerData.event);
        }
        catch (e) {
            target = '<unknown>';
        }
        if (target.length === 0) {
            return;
        }
        getCurrentHub().addBreadcrumb({
            category: "ui." + handlerData.name,
            message: target,
        }, {
            event: event,
            name: handlerData.name,
        });
    };
    /**
     * Creates breadcrumbs from XHR API calls
     */
    Breadcrumbs.prototype._xhrBreadcrumb = function (handlerData) {
        if (handlerData.endTimestamp) {
            // We only capture complete, non-sentry requests
            if (handlerData.xhr.__sentry_own_request__) {
                return;
            }
            getCurrentHub().addBreadcrumb({
                category: 'xhr',
                data: handlerData.xhr.__sentry_xhr__,
                type: 'http',
            }, {
                xhr: handlerData.xhr,
            });
            return;
        }
        // We only capture issued sentry requests
        if (handlerData.xhr.__sentry_own_request__) {
            addSentryBreadcrumb(handlerData.args[0]);
        }
    };
    /**
     * Creates breadcrumbs from fetch API calls
     */
    Breadcrumbs.prototype._fetchBreadcrumb = function (handlerData) {
        // We only capture complete fetch requests
        if (!handlerData.endTimestamp) {
            return;
        }
        var client = getCurrentHub().getClient();
        var dsn = client && client.getDsn();
        if (dsn) {
            var filterUrl = new API(dsn).getStoreEndpoint();
            // if Sentry key appears in URL, don't capture it as a request
            // but rather as our own 'sentry' type breadcrumb
            if (filterUrl &&
                handlerData.fetchData.url.indexOf(filterUrl) !== -1 &&
                handlerData.fetchData.method === 'POST' &&
                handlerData.args[1] &&
                handlerData.args[1].body) {
                addSentryBreadcrumb(handlerData.args[1].body);
                return;
            }
        }
        if (handlerData.error) {
            getCurrentHub().addBreadcrumb({
                category: 'fetch',
                data: tslib_1.__assign({}, handlerData.fetchData, { status_code: handlerData.response.status }),
                level: Severity.Error,
                type: 'http',
            }, {
                data: handlerData.error,
                input: handlerData.args,
            });
        }
        else {
            getCurrentHub().addBreadcrumb({
                category: 'fetch',
                data: tslib_1.__assign({}, handlerData.fetchData, { status_code: handlerData.response.status }),
                type: 'http',
            }, {
                input: handlerData.args,
                response: handlerData.response,
            });
        }
    };
    /**
     * Creates breadcrumbs from history API calls
     */
    Breadcrumbs.prototype._historyBreadcrumb = function (handlerData) {
        var global = getGlobalObject();
        var from = handlerData.from;
        var to = handlerData.to;
        var parsedLoc = parseUrl(global.location.href);
        var parsedFrom = parseUrl(from);
        var parsedTo = parseUrl(to);
        // Initial pushState doesn't provide `from` information
        if (!parsedFrom.path) {
            parsedFrom = parsedLoc;
        }
        // Use only the path component of the URL if the URL matches the current
        // document (almost all the time when using pushState)
        if (parsedLoc.protocol === parsedTo.protocol && parsedLoc.host === parsedTo.host) {
            // tslint:disable-next-line:no-parameter-reassignment
            to = parsedTo.relative;
        }
        if (parsedLoc.protocol === parsedFrom.protocol && parsedLoc.host === parsedFrom.host) {
            // tslint:disable-next-line:no-parameter-reassignment
            from = parsedFrom.relative;
        }
        getCurrentHub().addBreadcrumb({
            category: 'navigation',
            data: {
                from: from,
                to: to,
            },
        });
    };
    /**
     * Instrument browser built-ins w/ breadcrumb capturing
     *  - Console API
     *  - DOM API (click/typing)
     *  - XMLHttpRequest API
     *  - Fetch API
     *  - History API
     */
    Breadcrumbs.prototype.setupOnce = function () {
        var _this = this;
        if (this._options.console) {
            addInstrumentationHandler({
                callback: function () {
                    var args = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        args[_i] = arguments[_i];
                    }
                    _this._consoleBreadcrumb.apply(_this, tslib_1.__spread(args));
                },
                type: 'console',
            });
        }
        if (this._options.dom) {
            addInstrumentationHandler({
                callback: function () {
                    var args = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        args[_i] = arguments[_i];
                    }
                    _this._domBreadcrumb.apply(_this, tslib_1.__spread(args));
                },
                type: 'dom',
            });
        }
        if (this._options.xhr) {
            addInstrumentationHandler({
                callback: function () {
                    var args = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        args[_i] = arguments[_i];
                    }
                    _this._xhrBreadcrumb.apply(_this, tslib_1.__spread(args));
                },
                type: 'xhr',
            });
        }
        if (this._options.fetch) {
            addInstrumentationHandler({
                callback: function () {
                    var args = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        args[_i] = arguments[_i];
                    }
                    _this._fetchBreadcrumb.apply(_this, tslib_1.__spread(args));
                },
                type: 'fetch',
            });
        }
        if (this._options.history) {
            addInstrumentationHandler({
                callback: function () {
                    var args = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        args[_i] = arguments[_i];
                    }
                    _this._historyBreadcrumb.apply(_this, tslib_1.__spread(args));
                },
                type: 'history',
            });
        }
    };
    /**
     * @inheritDoc
     */
    Breadcrumbs.id = 'Breadcrumbs';
    return Breadcrumbs;
}());
export { Breadcrumbs };
/**
 * Create a breadcrumb of `sentry` from the events themselves
 */
function addSentryBreadcrumb(serializedData) {
    // There's always something that can go wrong with deserialization...
    try {
        var event_1 = JSON.parse(serializedData);
        getCurrentHub().addBreadcrumb({
            category: 'sentry',
            event_id: event_1.event_id,
            level: event_1.level || Severity.fromString('error'),
            message: getEventDescription(event_1),
        }, {
            event: event_1,
        });
    }
    catch (_oO) {
        logger.error('Error while adding sentry type breadcrumb');
    }
}
//# sourceMappingURL=breadcrumbs.js.map