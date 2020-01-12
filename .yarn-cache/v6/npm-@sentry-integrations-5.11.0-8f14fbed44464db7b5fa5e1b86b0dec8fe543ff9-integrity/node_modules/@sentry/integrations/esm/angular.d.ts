import { EventProcessor, Hub, Integration } from '@sentry/types';
/**
 * AngularJS integration
 *
 * Provides an $exceptionHandler for AngularJS
 */
export declare class Angular implements Integration {
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /**
     * moduleName used in Angular's DI resolution algorithm
     */
    static moduleName: string;
    /**
     * Angular's instance
     */
    private readonly _angular;
    /**
     * Returns current hub.
     */
    private _getCurrentHub?;
    /**
     * @inheritDoc
     */
    constructor(options?: {
        angular?: any;
    });
    /**
     * @inheritDoc
     */
    setupOnce(_: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
    /**
     * Angular's exceptionHandler for Sentry integration
     */
    private _$exceptionHandlerDecorator;
}
