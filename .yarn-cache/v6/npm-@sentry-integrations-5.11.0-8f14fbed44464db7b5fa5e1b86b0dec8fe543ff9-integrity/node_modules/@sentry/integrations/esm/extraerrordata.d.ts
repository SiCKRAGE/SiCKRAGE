import { Event, EventHint, EventProcessor, Hub, Integration } from '@sentry/types';
/** JSDoc */
interface ExtraErrorDataOptions {
    depth?: number;
}
/** Patch toString calls to return proper name for wrapped functions */
export declare class ExtraErrorData implements Integration {
    private readonly _options;
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /**
     * @inheritDoc
     */
    constructor(_options?: ExtraErrorDataOptions);
    /**
     * @inheritDoc
     */
    setupOnce(addGlobalEventProcessor: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
    /**
     * Attaches extracted information from the Error object to extra field in the Event
     */
    enhanceEventWithErrorData(event: Event, hint?: EventHint): Event;
    /**
     * Extract extra information from the Error object
     */
    private _extractErrorData;
}
export {};
