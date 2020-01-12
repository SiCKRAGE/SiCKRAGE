import { Event, EventProcessor, Hub, Integration, StackFrame } from '@sentry/types';
declare type StackFrameIteratee = (frame: StackFrame) => StackFrame;
/** Rewrite event frames paths */
export declare class RewriteFrames implements Integration {
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
    private readonly _root?;
    /**
     * @inheritDoc
     */
    private readonly _iteratee;
    /**
     * @inheritDoc
     */
    constructor(options?: {
        root?: string;
        iteratee?: StackFrameIteratee;
    });
    /**
     * @inheritDoc
     */
    setupOnce(addGlobalEventProcessor: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
    /** JSDoc */
    process(event: Event): Event;
    /** JSDoc */
    private _processExceptionsEvent;
    /** JSDoc */
    private _processStacktraceEvent;
    /** JSDoc */
    private _processStacktrace;
}
export {};
