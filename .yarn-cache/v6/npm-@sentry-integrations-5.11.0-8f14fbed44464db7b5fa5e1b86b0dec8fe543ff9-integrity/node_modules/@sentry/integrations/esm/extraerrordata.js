import * as tslib_1 from "tslib";
import { isError, isPlainObject, logger, normalize } from '@sentry/utils';
/** Patch toString calls to return proper name for wrapped functions */
var ExtraErrorData = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function ExtraErrorData(_options) {
        if (_options === void 0) { _options = { depth: 3 }; }
        this._options = _options;
        /**
         * @inheritDoc
         */
        this.name = ExtraErrorData.id;
    }
    /**
     * @inheritDoc
     */
    ExtraErrorData.prototype.setupOnce = function (addGlobalEventProcessor, getCurrentHub) {
        addGlobalEventProcessor(function (event, hint) {
            var self = getCurrentHub().getIntegration(ExtraErrorData);
            if (!self) {
                return event;
            }
            return self.enhanceEventWithErrorData(event, hint);
        });
    };
    /**
     * Attaches extracted information from the Error object to extra field in the Event
     */
    ExtraErrorData.prototype.enhanceEventWithErrorData = function (event, hint) {
        var _a;
        if (!hint || !hint.originalException || !isError(hint.originalException)) {
            return event;
        }
        var name = hint.originalException.name || hint.originalException.constructor.name;
        var errorData = this._extractErrorData(hint.originalException);
        if (errorData) {
            var contexts = tslib_1.__assign({}, event.contexts);
            var normalizedErrorData = normalize(errorData, this._options.depth);
            if (isPlainObject(normalizedErrorData)) {
                contexts = tslib_1.__assign({}, event.contexts, (_a = {}, _a[name] = tslib_1.__assign({}, normalizedErrorData), _a));
            }
            return tslib_1.__assign({}, event, { contexts: contexts });
        }
        return event;
    };
    /**
     * Extract extra information from the Error object
     */
    ExtraErrorData.prototype._extractErrorData = function (error) {
        var e_1, _a;
        var result = null;
        // We are trying to enhance already existing event, so no harm done if it won't succeed
        try {
            var nativeKeys_1 = ['name', 'message', 'stack', 'line', 'column', 'fileName', 'lineNumber', 'columnNumber'];
            var errorKeys = Object.getOwnPropertyNames(error).filter(function (key) { return nativeKeys_1.indexOf(key) === -1; });
            if (errorKeys.length) {
                var extraErrorInfo = {};
                try {
                    for (var errorKeys_1 = tslib_1.__values(errorKeys), errorKeys_1_1 = errorKeys_1.next(); !errorKeys_1_1.done; errorKeys_1_1 = errorKeys_1.next()) {
                        var key = errorKeys_1_1.value;
                        var value = error[key];
                        if (isError(value)) {
                            value = value.toString();
                        }
                        // tslint:disable:no-unsafe-any
                        extraErrorInfo[key] = value;
                    }
                }
                catch (e_1_1) { e_1 = { error: e_1_1 }; }
                finally {
                    try {
                        if (errorKeys_1_1 && !errorKeys_1_1.done && (_a = errorKeys_1.return)) _a.call(errorKeys_1);
                    }
                    finally { if (e_1) throw e_1.error; }
                }
                result = extraErrorInfo;
            }
        }
        catch (oO) {
            logger.error('Unable to extract extra data from the Error object:', oO);
        }
        return result;
    };
    /**
     * @inheritDoc
     */
    ExtraErrorData.id = 'ExtraErrorData';
    return ExtraErrorData;
}());
export { ExtraErrorData };
//# sourceMappingURL=extraerrordata.js.map