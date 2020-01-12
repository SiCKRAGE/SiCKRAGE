import { Integration } from '@sentry/types';
/** JSDoc */
interface InboundFiltersOptions {
    blacklistUrls?: Array<string | RegExp>;
    ignoreErrors?: Array<string | RegExp>;
    ignoreInternal?: boolean;
    whitelistUrls?: Array<string | RegExp>;
}
/** Inbound filters configurable by the user */
export declare class InboundFilters implements Integration {
    private readonly _options;
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    constructor(_options?: InboundFiltersOptions);
    /**
     * @inheritDoc
     */
    setupOnce(): void;
    /** JSDoc */
    private _shouldDropEvent;
    /** JSDoc */
    private _isSentryError;
    /** JSDoc */
    private _isIgnoredError;
    /** JSDoc */
    private _isBlacklistedUrl;
    /** JSDoc */
    private _isWhitelistedUrl;
    /** JSDoc */
    private _mergeOptions;
    /** JSDoc */
    private _getPossibleEventMessages;
    /** JSDoc */
    private _getEventFilterUrl;
}
export {};
//# sourceMappingURL=inboundfilters.d.ts.map