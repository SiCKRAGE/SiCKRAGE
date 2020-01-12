Object.defineProperty(exports, "__esModule", { value: true });
var tslib_1 = require("tslib");
var core_1 = require("@sentry/core");
var utils_1 = require("@sentry/utils");
var backend_1 = require("./backend");
var version_1 = require("./version");
/**
 * The Sentry Browser SDK Client.
 *
 * @see BrowserOptions for documentation on configuration options.
 * @see SentryClient for usage documentation.
 */
var BrowserClient = /** @class */ (function (_super) {
    tslib_1.__extends(BrowserClient, _super);
    /**
     * Creates a new Browser SDK instance.
     *
     * @param options Configuration options for this SDK.
     */
    function BrowserClient(options) {
        if (options === void 0) { options = {}; }
        return _super.call(this, backend_1.BrowserBackend, options) || this;
    }
    /**
     * @inheritDoc
     */
    BrowserClient.prototype._prepareEvent = function (event, scope, hint) {
        event.platform = event.platform || 'javascript';
        event.sdk = tslib_1.__assign({}, event.sdk, { name: version_1.SDK_NAME, packages: tslib_1.__spread(((event.sdk && event.sdk.packages) || []), [
                {
                    name: 'npm:@sentry/browser',
                    version: version_1.SDK_VERSION,
                },
            ]), version: version_1.SDK_VERSION });
        return _super.prototype._prepareEvent.call(this, event, scope, hint);
    };
    /**
     * Show a report dialog to the user to send feedback to a specific event.
     *
     * @param options Set individual options for the dialog
     */
    BrowserClient.prototype.showReportDialog = function (options) {
        if (options === void 0) { options = {}; }
        // doesn't work without a document (React Native)
        var document = utils_1.getGlobalObject().document;
        if (!document) {
            return;
        }
        if (!this._isEnabled()) {
            utils_1.logger.error('Trying to call showReportDialog with Sentry Client is disabled');
            return;
        }
        var dsn = options.dsn || this.getDsn();
        if (!options.eventId) {
            utils_1.logger.error('Missing `eventId` option in showReportDialog call');
            return;
        }
        if (!dsn) {
            utils_1.logger.error('Missing `Dsn` option in showReportDialog call');
            return;
        }
        var script = document.createElement('script');
        script.async = true;
        script.src = new core_1.API(dsn).getReportDialogEndpoint(options);
        if (options.onLoad) {
            script.onload = options.onLoad;
        }
        (document.head || document.body).appendChild(script);
    };
    return BrowserClient;
}(core_1.BaseClient));
exports.BrowserClient = BrowserClient;
//# sourceMappingURL=client.js.map