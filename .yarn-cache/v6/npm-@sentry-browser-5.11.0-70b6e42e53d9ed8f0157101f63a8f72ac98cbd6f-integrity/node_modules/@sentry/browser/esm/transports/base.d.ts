import { Event, Response, Transport, TransportOptions } from '@sentry/types';
import { PromiseBuffer } from '@sentry/utils';
/** Base Transport class implementation */
export declare abstract class BaseTransport implements Transport {
    options: TransportOptions;
    /**
     * @inheritDoc
     */
    url: string;
    /** A simple buffer holding all requests. */
    protected readonly _buffer: PromiseBuffer<Response>;
    constructor(options: TransportOptions);
    /**
     * @inheritDoc
     */
    sendEvent(_: Event): PromiseLike<Response>;
    /**
     * @inheritDoc
     */
    close(timeout?: number): PromiseLike<boolean>;
}
//# sourceMappingURL=base.d.ts.map