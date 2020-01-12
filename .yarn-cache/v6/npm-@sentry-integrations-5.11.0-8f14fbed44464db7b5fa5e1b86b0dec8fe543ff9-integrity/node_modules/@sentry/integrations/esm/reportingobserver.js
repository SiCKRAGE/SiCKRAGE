import * as tslib_1 from "tslib";
import { getGlobalObject, supportsReportingObserver } from '@sentry/utils';
/** JSDoc */
var ReportTypes;
(function (ReportTypes) {
    /** JSDoc */
    ReportTypes["Crash"] = "crash";
    /** JSDoc */
    ReportTypes["Deprecation"] = "deprecation";
    /** JSDoc */
    ReportTypes["Intervention"] = "intervention";
})(ReportTypes || (ReportTypes = {}));
/** Reporting API integration - https://w3c.github.io/reporting/ */
var ReportingObserver = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function ReportingObserver(_options) {
        if (_options === void 0) { _options = {
            types: [ReportTypes.Crash, ReportTypes.Deprecation, ReportTypes.Intervention],
        }; }
        this._options = _options;
        /**
         * @inheritDoc
         */
        this.name = ReportingObserver.id;
    }
    /**
     * @inheritDoc
     */
    ReportingObserver.prototype.setupOnce = function (_, getCurrentHub) {
        // tslint:disable:no-unsafe-any
        if (!supportsReportingObserver()) {
            return;
        }
        this._getCurrentHub = getCurrentHub;
        var observer = new (getGlobalObject()).ReportingObserver(this.handler.bind(this), {
            buffered: true,
            types: this._options.types,
        });
        observer.observe();
    };
    /**
     * @inheritDoc
     */
    ReportingObserver.prototype.handler = function (reports) {
        var e_1, _a;
        var hub = this._getCurrentHub && this._getCurrentHub();
        if (!hub || !hub.getIntegration(ReportingObserver)) {
            return;
        }
        var _loop_1 = function (report) {
            hub.withScope(function (scope) {
                scope.setExtra('url', report.url);
                var label = "ReportingObserver [" + report.type + "]";
                var details = 'No details available';
                if (report.body) {
                    // Object.keys doesn't work on ReportBody, as all properties are inheirted
                    var plainBody = {};
                    // tslint:disable-next-line:forin
                    for (var prop in report.body) {
                        plainBody[prop] = report.body[prop];
                    }
                    scope.setExtra('body', plainBody);
                    if (report.type === ReportTypes.Crash) {
                        var body = report.body;
                        // A fancy way to create a message out of crashId OR reason OR both OR fallback
                        details = [body.crashId || '', body.reason || ''].join(' ').trim() || details;
                    }
                    else {
                        var body = report.body;
                        details = body.message || details;
                    }
                }
                hub.captureMessage(label + ": " + details);
            });
        };
        try {
            for (var reports_1 = tslib_1.__values(reports), reports_1_1 = reports_1.next(); !reports_1_1.done; reports_1_1 = reports_1.next()) {
                var report = reports_1_1.value;
                _loop_1(report);
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (reports_1_1 && !reports_1_1.done && (_a = reports_1.return)) _a.call(reports_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
    };
    /**
     * @inheritDoc
     */
    ReportingObserver.id = 'ReportingObserver';
    return ReportingObserver;
}());
export { ReportingObserver };
//# sourceMappingURL=reportingobserver.js.map