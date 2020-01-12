import { Breadcrumb, BreadcrumbHint, Client, Event, EventHint, Hub as HubInterface, Integration, IntegrationClass, Severity, Span, SpanContext, User } from '@sentry/types';
import { Carrier, Layer } from './interfaces';
import { Scope } from './scope';
declare module 'domain' {
    let active: Domain;
    /**
     * Extension for domain interface
     */
    interface Domain {
        __SENTRY__?: Carrier;
    }
}
/**
 * API compatibility version of this hub.
 *
 * WARNING: This number should only be incresed when the global interface
 * changes a and new methods are introduced.
 *
 * @hidden
 */
export declare const API_VERSION = 3;
/**
 * @inheritDoc
 */
export declare class Hub implements HubInterface {
    private readonly _version;
    /** Is a {@link Layer}[] containing the client and scope */
    private readonly _stack;
    /** Contains the last event id of a captured event.  */
    private _lastEventId?;
    /**
     * Creates a new instance of the hub, will push one {@link Layer} into the
     * internal stack on creation.
     *
     * @param client bound to the hub.
     * @param scope bound to the hub.
     * @param version number, higher number means higher priority.
     */
    constructor(client?: Client, scope?: Scope, _version?: number);
    /**
     * Internal helper function to call a method on the top client if it exists.
     *
     * @param method The method to call on the client.
     * @param args Arguments to pass to the client function.
     */
    private _invokeClient;
    /**
     * @inheritDoc
     */
    isOlderThan(version: number): boolean;
    /**
     * @inheritDoc
     */
    bindClient(client?: Client): void;
    /**
     * @inheritDoc
     */
    pushScope(): Scope;
    /**
     * @inheritDoc
     */
    popScope(): boolean;
    /**
     * @inheritDoc
     */
    withScope(callback: (scope: Scope) => void): void;
    /**
     * @inheritDoc
     */
    getClient<C extends Client>(): C | undefined;
    /** Returns the scope of the top stack. */
    getScope(): Scope | undefined;
    /** Returns the scope stack for domains or the process. */
    getStack(): Layer[];
    /** Returns the topmost scope layer in the order domain > local > process. */
    getStackTop(): Layer;
    /**
     * @inheritDoc
     */
    captureException(exception: any, hint?: EventHint): string;
    /**
     * @inheritDoc
     */
    captureMessage(message: string, level?: Severity, hint?: EventHint): string;
    /**
     * @inheritDoc
     */
    captureEvent(event: Event, hint?: EventHint): string;
    /**
     * @inheritDoc
     */
    lastEventId(): string | undefined;
    /**
     * @inheritDoc
     */
    addBreadcrumb(breadcrumb: Breadcrumb, hint?: BreadcrumbHint): void;
    /**
     * @inheritDoc
     */
    setUser(user: User | null): void;
    /**
     * @inheritDoc
     */
    setTags(tags: {
        [key: string]: string;
    }): void;
    /**
     * @inheritDoc
     */
    setExtras(extras: {
        [key: string]: any;
    }): void;
    /**
     * @inheritDoc
     */
    setTag(key: string, value: string): void;
    /**
     * @inheritDoc
     */
    setExtra(key: string, extra: any): void;
    /**
     * @inheritDoc
     */
    setContext(name: string, context: {
        [key: string]: any;
    } | null): void;
    /**
     * @inheritDoc
     */
    configureScope(callback: (scope: Scope) => void): void;
    /**
     * @inheritDoc
     */
    run(callback: (hub: Hub) => void): void;
    /**
     * @inheritDoc
     */
    getIntegration<T extends Integration>(integration: IntegrationClass<T>): T | null;
    /**
     * @inheritDoc
     */
    startSpan(spanOrSpanContext?: Span | SpanContext, forceNoChild?: boolean): Span;
    /**
     * @inheritDoc
     */
    traceHeaders(): {
        [key: string]: string;
    };
    /**
     * Calls global extension method and binding current instance to the function call
     */
    private _callExtensionMethod;
}
/** Returns the global shim registry. */
export declare function getMainCarrier(): Carrier;
/**
 * Replaces the current main hub with the passed one on the global object
 *
 * @returns The old replaced hub
 */
export declare function makeMain(hub: Hub): Hub;
/**
 * Returns the default hub instance.
 *
 * If a hub is already registered in the global carrier but this module
 * contains a more recent version, it replaces the registered version.
 * Otherwise, the currently registered hub will be returned.
 */
export declare function getCurrentHub(): Hub;
/**
 * This will create a new {@link Hub} and add to the passed object on
 * __SENTRY__.hub.
 * @param carrier object
 * @hidden
 */
export declare function getHubFromCarrier(carrier: Carrier): Hub;
/**
 * This will set passed {@link Hub} on the passed object's __SENTRY__.hub attribute
 * @param carrier object
 * @param hub Hub
 */
export declare function setHubOnCarrier(carrier: Carrier, hub: Hub): boolean;
//# sourceMappingURL=hub.d.ts.map