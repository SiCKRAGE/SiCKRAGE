import { Integration } from '@sentry/types';
/** Wrap timer functions and event targets to catch errors and provide better meta data */
export declare class TryCatch implements Integration {
    /** JSDoc */
    private _ignoreOnError;
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /** JSDoc */
    private _wrapTimeFunction;
    /** JSDoc */
    private _wrapRAF;
    /** JSDoc */
    private _wrapEventTarget;
    /** JSDoc */
    private _wrapXHR;
    /**
     * Wrap timer functions and event targets to catch errors
     * and provide better metadata.
     */
    setupOnce(): void;
}
//# sourceMappingURL=trycatch.d.ts.map