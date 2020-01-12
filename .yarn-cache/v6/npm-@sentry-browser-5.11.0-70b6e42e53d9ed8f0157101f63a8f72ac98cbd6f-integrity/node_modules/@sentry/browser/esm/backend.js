import * as tslib_1 from "tslib";
import { BaseBackend } from '@sentry/core';
import { Severity } from '@sentry/types';
import { addExceptionMechanism, supportsFetch, SyncPromise } from '@sentry/utils';
import { eventFromString, eventFromUnknownInput } from './eventbuilder';
import { FetchTransport, XHRTransport } from './transports';
/**
 * The Sentry Browser SDK Backend.
 * @hidden
 */
var BrowserBackend = /** @class */ (function (_super) {
    tslib_1.__extends(BrowserBackend, _super);
    function BrowserBackend() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    /**
     * @inheritDoc
     */
    BrowserBackend.prototype._setupTransport = function () {
        if (!this._options.dsn) {
            // We return the noop transport here in case there is no Dsn.
            return _super.prototype._setupTransport.call(this);
        }
        var transportOptions = tslib_1.__assign({}, this._options.transportOptions, { dsn: this._options.dsn });
        if (this._options.transport) {
            return new this._options.transport(transportOptions);
        }
        if (supportsFetch()) {
            return new FetchTransport(transportOptions);
        }
        return new XHRTransport(transportOptions);
    };
    /**
     * @inheritDoc
     */
    BrowserBackend.prototype.eventFromException = function (exception, hint) {
        var syntheticException = (hint && hint.syntheticException) || undefined;
        var event = eventFromUnknownInput(exception, syntheticException, {
            attachStacktrace: this._options.attachStacktrace,
        });
        addExceptionMechanism(event, {
            handled: true,
            type: 'generic',
        });
        event.level = Severity.Error;
        if (hint && hint.event_id) {
            event.event_id = hint.event_id;
        }
        return SyncPromise.resolve(event);
    };
    /**
     * @inheritDoc
     */
    BrowserBackend.prototype.eventFromMessage = function (message, level, hint) {
        if (level === void 0) { level = Severity.Info; }
        var syntheticException = (hint && hint.syntheticException) || undefined;
        var event = eventFromString(message, syntheticException, {
            attachStacktrace: this._options.attachStacktrace,
        });
        event.level = level;
        if (hint && hint.event_id) {
            event.event_id = hint.event_id;
        }
        return SyncPromise.resolve(event);
    };
    return BrowserBackend;
}(BaseBackend));
export { BrowserBackend };
//# sourceMappingURL=backend.js.map