Object.defineProperty(exports, "__esModule", { value: true });
var tslib_1 = require("tslib");
/** This function adds duration since Sentry was initialized till the time event was sent */
var SessionTiming = /** @class */ (function () {
    function SessionTiming() {
        /**
         * @inheritDoc
         */
        this.name = SessionTiming.id;
        /** Exact time Client was initialized expressed in milliseconds since Unix Epoch. */
        this._startTime = Date.now();
    }
    /**
     * @inheritDoc
     */
    SessionTiming.prototype.setupOnce = function (addGlobalEventProcessor, getCurrentHub) {
        addGlobalEventProcessor(function (event) {
            var self = getCurrentHub().getIntegration(SessionTiming);
            if (self) {
                return self.process(event);
            }
            return event;
        });
    };
    /**
     * @inheritDoc
     */
    SessionTiming.prototype.process = function (event) {
        var _a;
        var now = Date.now();
        return tslib_1.__assign({}, event, { extra: tslib_1.__assign({}, event.extra, (_a = {}, _a['session:start'] = this._startTime, _a['session:duration'] = now - this._startTime, _a['session:end'] = now, _a)) });
    };
    /**
     * @inheritDoc
     */
    SessionTiming.id = 'SessionTiming';
    return SessionTiming;
}());
exports.SessionTiming = SessionTiming;
//# sourceMappingURL=sessiontiming.js.map