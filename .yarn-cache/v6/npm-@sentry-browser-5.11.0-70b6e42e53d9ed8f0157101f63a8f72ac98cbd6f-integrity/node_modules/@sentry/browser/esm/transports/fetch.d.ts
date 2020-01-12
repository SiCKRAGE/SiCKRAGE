import { Event, Response } from '@sentry/types';
import { BaseTransport } from './base';
/** `fetch` based transport */
export declare class FetchTransport extends BaseTransport {
    /** Locks transport after receiving 429 response */
    private _disabledUntil;
    /**
     * @inheritDoc
     */
    sendEvent(event: Event): PromiseLike<Response>;
}
//# sourceMappingURL=fetch.d.ts.map