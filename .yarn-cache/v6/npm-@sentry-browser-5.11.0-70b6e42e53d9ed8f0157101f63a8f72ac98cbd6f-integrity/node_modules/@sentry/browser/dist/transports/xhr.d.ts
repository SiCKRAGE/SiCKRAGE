import { Event, Response } from '@sentry/types';
import { BaseTransport } from './base';
/** `XHR` based transport */
export declare class XHRTransport extends BaseTransport {
    /** Locks transport after receiving 429 response */
    private _disabledUntil;
    /**
     * @inheritDoc
     */
    sendEvent(event: Event): PromiseLike<Response>;
}
//# sourceMappingURL=xhr.d.ts.map