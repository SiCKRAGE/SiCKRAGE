import * as tslib_1 from "tslib";
import { Status } from '@sentry/types';
import { logger, parseRetryAfterHeader, SyncPromise } from '@sentry/utils';
import { BaseTransport } from './base';
/** `XHR` based transport */
var XHRTransport = /** @class */ (function (_super) {
    tslib_1.__extends(XHRTransport, _super);
    function XHRTransport() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        /** Locks transport after receiving 429 response */
        _this._disabledUntil = new Date(Date.now());
        return _this;
    }
    /**
     * @inheritDoc
     */
    XHRTransport.prototype.sendEvent = function (event) {
        var _this = this;
        if (new Date(Date.now()) < this._disabledUntil) {
            return Promise.reject({
                event: event,
                reason: "Transport locked till " + this._disabledUntil + " due to too many requests.",
                status: 429,
            });
        }
        return this._buffer.add(new SyncPromise(function (resolve, reject) {
            var request = new XMLHttpRequest();
            request.onreadystatechange = function () {
                if (request.readyState !== 4) {
                    return;
                }
                var status = Status.fromHttpCode(request.status);
                if (status === Status.Success) {
                    resolve({ status: status });
                    return;
                }
                if (status === Status.RateLimit) {
                    var now = Date.now();
                    _this._disabledUntil = new Date(now + parseRetryAfterHeader(now, request.getResponseHeader('Retry-After')));
                    logger.warn("Too many requests, backing off till: " + _this._disabledUntil);
                }
                reject(request);
            };
            request.open('POST', _this.url);
            for (var header in _this.options.headers) {
                if (_this.options.headers.hasOwnProperty(header)) {
                    request.setRequestHeader(header, _this.options.headers[header]);
                }
            }
            request.send(JSON.stringify(event));
        }));
    };
    return XHRTransport;
}(BaseTransport));
export { XHRTransport };
//# sourceMappingURL=xhr.js.map