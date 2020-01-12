import { EventProcessor, Hub, Integration } from '@sentry/types';
/** Deduplication filter */
export declare class Dedupe implements Integration {
    /**
     * @inheritDoc
     */
    private _previousEvent?;
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
    setupOnce(addGlobalEventProcessor: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
    /** JSDoc */
    private _shouldDropEvent;
    /** JSDoc */
    private _isSameMessageEvent;
    /** JSDoc */
    private _getFramesFromEvent;
    /** JSDoc */
    private _isSameStacktrace;
    /** JSDoc */
    private _getExceptionFromEvent;
    /** JSDoc */
    private _isSameExceptionEvent;
    /** JSDoc */
    private _isSameFingerprint;
}
