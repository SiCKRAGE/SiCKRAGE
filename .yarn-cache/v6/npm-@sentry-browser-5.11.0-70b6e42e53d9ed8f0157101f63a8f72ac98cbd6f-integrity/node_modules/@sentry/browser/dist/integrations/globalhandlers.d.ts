import { Integration } from '@sentry/types';
/** JSDoc */
interface GlobalHandlersIntegrations {
    onerror: boolean;
    onunhandledrejection: boolean;
}
/** Global handlers */
export declare class GlobalHandlers implements Integration {
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
    /** JSDoc */
    private readonly _global;
    /** JSDoc */
    private _oldOnErrorHandler;
    /** JSDoc */
    private _oldOnUnhandledRejectionHandler;
    /** JSDoc */
    private _onErrorHandlerInstalled;
    /** JSDoc */
    private _onUnhandledRejectionHandlerInstalled;
    /** JSDoc */
    constructor(options?: GlobalHandlersIntegrations);
    /**
     * @inheritDoc
     */
    setupOnce(): void;
    /** JSDoc */
    private _installGlobalOnErrorHandler;
    /** JSDoc */
    private _installGlobalOnUnhandledRejectionHandler;
    /**
     * This function creates a stack from an old, error-less onerror handler.
     */
    private _eventFromIncompleteOnError;
    /**
     * This function creates an Event from an TraceKitStackTrace that has part of it missing.
     */
    private _eventFromIncompleteRejection;
    /** JSDoc */
    private _enhanceEventWithInitialFrame;
}
export {};
//# sourceMappingURL=globalhandlers.d.ts.map