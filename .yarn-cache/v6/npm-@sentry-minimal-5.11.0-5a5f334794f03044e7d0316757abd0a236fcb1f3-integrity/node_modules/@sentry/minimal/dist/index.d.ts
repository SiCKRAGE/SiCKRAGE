import { Scope } from '@sentry/hub';
import { Breadcrumb, Event, Severity, User } from '@sentry/types';
/**
 * Captures an exception event and sends it to Sentry.
 *
 * @param exception An exception-like object.
 * @returns The generated eventId.
 */
export declare function captureException(exception: any): string;
/**
 * Captures a message event and sends it to Sentry.
 *
 * @param message The message to send to Sentry.
 * @param level Define the level of the message.
 * @returns The generated eventId.
 */
export declare function captureMessage(message: string, level?: Severity): string;
/**
 * Captures a manually created event and sends it to Sentry.
 *
 * @param event The event to send to Sentry.
 * @returns The generated eventId.
 */
export declare function captureEvent(event: Event): string;
/**
 * Callback to set context information onto the scope.
 * @param callback Callback function that receives Scope.
 */
export declare function configureScope(callback: (scope: Scope) => void): void;
/**
 * Records a new breadcrumb which will be attached to future events.
 *
 * Breadcrumbs will be added to subsequent events to provide more context on
 * user's actions prior to an error or crash.
 *
 * @param breadcrumb The breadcrumb to record.
 */
export declare function addBreadcrumb(breadcrumb: Breadcrumb): void;
/**
 * Sets context data with the given name.
 * @param name of the context
 * @param context Any kind of data. This data will be normailzed.
 */
export declare function setContext(name: string, context: {
    [key: string]: any;
} | null): void;
/**
 * Set an object that will be merged sent as extra data with the event.
 * @param extras Extras object to merge into current context.
 */
export declare function setExtras(extras: {
    [key: string]: any;
}): void;
/**
 * Set an object that will be merged sent as tags data with the event.
 * @param tags Tags context object to merge into current context.
 */
export declare function setTags(tags: {
    [key: string]: string;
}): void;
/**
 * Set key:value that will be sent as extra data with the event.
 * @param key String of extra
 * @param extra Any kind of data. This data will be normailzed.
 */
export declare function setExtra(key: string, extra: any): void;
/**
 * Set key:value that will be sent as tags data with the event.
 * @param key String key of tag
 * @param value String value of tag
 */
export declare function setTag(key: string, value: string): void;
/**
 * Updates user context information for future events.
 *
 * @param user User context object to be set in the current context. Pass `null` to unset the user.
 */
export declare function setUser(user: User | null): void;
/**
 * Creates a new scope with and executes the given operation within.
 * The scope is automatically removed once the operation
 * finishes or throws.
 *
 * This is essentially a convenience function for:
 *
 *     pushScope();
 *     callback();
 *     popScope();
 *
 * @param callback that will be enclosed into push/popScope.
 */
export declare function withScope(callback: (scope: Scope) => void): void;
/**
 * Calls a function on the latest client. Use this with caution, it's meant as
 * in "internal" helper so we don't need to expose every possible function in
 * the shim. It is not guaranteed that the client actually implements the
 * function.
 *
 * @param method The method to call on the client/client.
 * @param args Arguments to pass to the client/fontend.
 * @hidden
 */
export declare function _callOnClient(method: string, ...args: any[]): void;
//# sourceMappingURL=index.d.ts.map