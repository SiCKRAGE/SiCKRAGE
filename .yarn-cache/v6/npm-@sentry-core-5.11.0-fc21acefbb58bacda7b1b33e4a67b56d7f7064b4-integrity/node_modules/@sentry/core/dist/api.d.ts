import { DsnLike } from '@sentry/types';
import { Dsn } from '@sentry/utils';
/** Helper class to provide urls to different Sentry endpoints. */
export declare class API {
    dsn: DsnLike;
    /** The internally used Dsn object. */
    private readonly _dsnObject;
    /** Create a new instance of API */
    constructor(dsn: DsnLike);
    /** Returns the Dsn object. */
    getDsn(): Dsn;
    /** Returns a string with auth headers in the url to the store endpoint. */
    getStoreEndpoint(): string;
    /** Returns the store endpoint with auth added in url encoded. */
    getStoreEndpointWithUrlEncodedAuth(): string;
    /** Returns the base path of the url including the port. */
    private _getBaseUrl;
    /** Returns only the path component for the store endpoint. */
    getStoreEndpointPath(): string;
    /** Returns an object that can be used in request headers. */
    getRequestHeaders(clientName: string, clientVersion: string): {
        [key: string]: string;
    };
    /** Returns the url to the report dialog endpoint. */
    getReportDialogEndpoint(dialogOptions?: {
        [key: string]: any;
        user?: {
            name?: string;
            email?: string;
        };
    }): string;
}
//# sourceMappingURL=api.d.ts.map