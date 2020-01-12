import { EventProcessor, Hub, Integration } from '@sentry/types';
/** JSDoc */
interface DebugOptions {
    stringify?: boolean;
    debugger?: boolean;
}
/** JSDoc */
export declare class Debug implements Integration {
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /** JSDoc */
    private readonly _options;
    /**
     * @inheritDoc
     */
    constructor(options?: DebugOptions);
    /**
     * @inheritDoc
     */
    setupOnce(addGlobalEventProcessor: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
}
export {};
