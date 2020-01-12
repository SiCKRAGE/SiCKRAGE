Object.defineProperty(exports, "__esModule", { value: true });
var core_1 = require("@sentry/core");
var utils_1 = require("@sentry/utils");
var client_1 = require("./client");
var helpers_1 = require("./helpers");
var integrations_1 = require("./integrations");
exports.defaultIntegrations = [
    new core_1.Integrations.InboundFilters(),
    new core_1.Integrations.FunctionToString(),
    new integrations_1.TryCatch(),
    new integrations_1.Breadcrumbs(),
    new integrations_1.GlobalHandlers(),
    new integrations_1.LinkedErrors(),
    new integrations_1.UserAgent(),
];
/**
 * The Sentry Browser SDK Client.
 *
 * To use this SDK, call the {@link init} function as early as possible when
 * loading the web page. To set context information or send manual events, use
 * the provided methods.
 *
 * @example
 *
 * ```
 *
 * import { init } from '@sentry/browser';
 *
 * init({
 *   dsn: '__DSN__',
 *   // ...
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { configureScope } from '@sentry/browser';
 * configureScope((scope: Scope) => {
 *   scope.setExtra({ battery: 0.7 });
 *   scope.setTag({ user_mode: 'admin' });
 *   scope.setUser({ id: '4711' });
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { addBreadcrumb } from '@sentry/browser';
 * addBreadcrumb({
 *   message: 'My Breadcrumb',
 *   // ...
 * });
 * ```
 *
 * @example
 *
 * ```
 *
 * import * as Sentry from '@sentry/browser';
 * Sentry.captureMessage('Hello, world!');
 * Sentry.captureException(new Error('Good bye'));
 * Sentry.captureEvent({
 *   message: 'Manual',
 *   stacktrace: [
 *     // ...
 *   ],
 * });
 * ```
 *
 * @see {@link BrowserOptions} for documentation on configuration options.
 */
function init(options) {
    if (options === void 0) { options = {}; }
    if (options.defaultIntegrations === undefined) {
        options.defaultIntegrations = exports.defaultIntegrations;
    }
    if (options.release === undefined) {
        var window_1 = utils_1.getGlobalObject();
        // This supports the variable that sentry-webpack-plugin injects
        if (window_1.SENTRY_RELEASE && window_1.SENTRY_RELEASE.id) {
            options.release = window_1.SENTRY_RELEASE.id;
        }
    }
    core_1.initAndBind(client_1.BrowserClient, options);
}
exports.init = init;
/**
 * Present the user with a report dialog.
 *
 * @param options Everything is optional, we try to fetch all info need from the global scope.
 */
function showReportDialog(options) {
    if (options === void 0) { options = {}; }
    if (!options.eventId) {
        options.eventId = core_1.getCurrentHub().lastEventId();
    }
    var client = core_1.getCurrentHub().getClient();
    if (client) {
        client.showReportDialog(options);
    }
}
exports.showReportDialog = showReportDialog;
/**
 * This is the getter for lastEventId.
 *
 * @returns The last event id of a captured event.
 */
function lastEventId() {
    return core_1.getCurrentHub().lastEventId();
}
exports.lastEventId = lastEventId;
/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
function forceLoad() {
    // Noop
}
exports.forceLoad = forceLoad;
/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
function onLoad(callback) {
    callback();
}
exports.onLoad = onLoad;
/**
 * A promise that resolves when all current events have been sent.
 * If you provide a timeout and the queue takes longer to drain the promise returns false.
 *
 * @param timeout Maximum time in ms the client should wait.
 */
function flush(timeout) {
    var client = core_1.getCurrentHub().getClient();
    if (client) {
        return client.flush(timeout);
    }
    return utils_1.SyncPromise.reject(false);
}
exports.flush = flush;
/**
 * A promise that resolves when all current events have been sent.
 * If you provide a timeout and the queue takes longer to drain the promise returns false.
 *
 * @param timeout Maximum time in ms the client should wait.
 */
function close(timeout) {
    var client = core_1.getCurrentHub().getClient();
    if (client) {
        return client.close(timeout);
    }
    return utils_1.SyncPromise.reject(false);
}
exports.close = close;
/**
 * Wrap code within a try/catch block so the SDK is able to capture errors.
 *
 * @param fn A function to wrap.
 *
 * @returns The result of wrapped function call.
 */
function wrap(fn) {
    return helpers_1.wrap(fn)(); // tslint:disable-line:no-unsafe-any
}
exports.wrap = wrap;
//# sourceMappingURL=sdk.js.map