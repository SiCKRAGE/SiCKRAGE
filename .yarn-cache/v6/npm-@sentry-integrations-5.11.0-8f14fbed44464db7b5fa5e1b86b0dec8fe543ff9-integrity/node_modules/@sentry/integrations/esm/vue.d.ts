import { EventProcessor, Hub, Integration } from '@sentry/types';
/** JSDoc */
export declare class Vue implements Integration {
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
    private readonly _Vue;
    /**
     * When set to false, Sentry will suppress reporting all props data
     * from your Vue components for privacy concerns.
     */
    private readonly _attachProps;
    /**
     * When set to true, original Vue's `logError` will be called as well.
     * https://github.com/vuejs/vue/blob/c2b1cfe9ccd08835f2d99f6ce60f67b4de55187f/src/core/util/error.js#L38-L48
     */
    private readonly _logErrors;
    /**
     * @inheritDoc
     */
    constructor(options?: {
        Vue?: any;
        attachProps?: boolean;
        logErrors?: boolean;
    });
    /** JSDoc */
    private _formatComponentName;
    /**
     * @inheritDoc
     */
    setupOnce(_: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
}
