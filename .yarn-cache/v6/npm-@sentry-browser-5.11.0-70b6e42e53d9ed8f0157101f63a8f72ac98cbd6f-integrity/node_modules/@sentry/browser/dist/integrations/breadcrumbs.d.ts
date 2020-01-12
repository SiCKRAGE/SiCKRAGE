import { Integration } from '@sentry/types';
/**
 * @hidden
 */
export interface SentryWrappedXMLHttpRequest extends XMLHttpRequest {
    [key: string]: any;
    __sentry_xhr__?: {
        method?: string;
        url?: string;
        status_code?: number;
    };
}
/** JSDoc */
interface BreadcrumbIntegrations {
    console?: boolean;
    dom?: boolean;
    fetch?: boolean;
    history?: boolean;
    sentry?: boolean;
    xhr?: boolean;
}
/**
 * Default Breadcrumbs instrumentations
 * TODO: Deprecated - with v6, this will be renamed to `Instrument`
 */
export declare class Breadcrumbs implements Integration {
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
    constructor(options?: BreadcrumbIntegrations);
    /**
     * Creates breadcrumbs from console API calls
     */
    private _consoleBreadcrumb;
    /**
     * Creates breadcrumbs from DOM API calls
     */
    private _domBreadcrumb;
    /**
     * Creates breadcrumbs from XHR API calls
     */
    private _xhrBreadcrumb;
    /**
     * Creates breadcrumbs from fetch API calls
     */
    private _fetchBreadcrumb;
    /**
     * Creates breadcrumbs from history API calls
     */
    private _historyBreadcrumb;
    /**
     * Instrument browser built-ins w/ breadcrumb capturing
     *  - Console API
     *  - DOM API (click/typing)
     *  - XMLHttpRequest API
     *  - Fetch API
     *  - History API
     */
    setupOnce(): void;
}
export {};
//# sourceMappingURL=breadcrumbs.d.ts.map