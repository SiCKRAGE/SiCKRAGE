import { EventProcessor, Hub, Integration } from '@sentry/types';
/** JSDoc */
export declare class Ember implements Integration {
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
    private readonly _Ember;
    /**
     * @inheritDoc
     */
    constructor(options?: {
        Ember?: any;
    });
    /**
     * @inheritDoc
     */
    setupOnce(_: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
}
