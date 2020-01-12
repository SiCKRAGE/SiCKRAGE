import { Integrations as CoreIntegrations } from '@sentry/core';
import { BrowserOptions } from './backend';
import { ReportDialogOptions } from './client';
import { Breadcrumbs, GlobalHandlers, LinkedErrors, TryCatch, UserAgent } from './integrations';
export declare const defaultIntegrations: (CoreIntegrations.FunctionToString | CoreIntegrations.InboundFilters | GlobalHandlers | TryCatch | Breadcrumbs | LinkedErrors | UserAgent)[];
/**
 * The Sentry Browser SDK Client.
 *
 * To use this SDK, call the {@link init} function as early as possible when
 * loading the web page. To set context information or send manual events, use
 * the provided methods.
 *
 * @example
 *
 * ```
 *
 * import { init } from '@sentry/browser';
 *
 * init({
 *   dsn: '__DSN__',
 *   // ...
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { configureScope } from '@sentry/browser';
 * configureScope((scope: Scope) => {
 *   scope.setExtra({ battery: 0.7 });
 *   scope.setTag({ user_mode: 'admin' });
 *   scope.setUser({ id: '4711' });
 * });
 * ```
 *
 * @example
 * ```
 *
 * import { addBreadcrumb } from '@sentry/browser';
 * addBreadcrumb({
 *   message: 'My Breadcrumb',
 *   // ...
 * });
 * ```
 *
 * @example
 *
 * ```
 *
 * import * as Sentry from '@sentry/browser';
 * Sentry.captureMessage('Hello, world!');
 * Sentry.captureException(new Error('Good bye'));
 * Sentry.captureEvent({
 *   message: 'Manual',
 *   stacktrace: [
 *     // ...
 *   ],
 * });
 * ```
 *
 * @see {@link BrowserOptions} for documentation on configuration options.
 */
export declare function init(options?: BrowserOptions): void;
/**
 * Present the user with a report dialog.
 *
 * @param options Everything is optional, we try to fetch all info need from the global scope.
 */
export declare function showReportDialog(options?: ReportDialogOptions): void;
/**
 * This is the getter for lastEventId.
 *
 * @returns The last event id of a captured event.
 */
export declare function lastEventId(): string | undefined;
/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
export declare function forceLoad(): void;
/**
 * This function is here to be API compatible with the loader.
 * @hidden
 */
export declare function onLoad(callback: () => void): void;
/**
 * A promise that resolves when all current events have been sent.
 * If you provide a timeout and the queue takes longer to drain the promise returns false.
 *
 * @param timeout Maximum time in ms the client should wait.
 */
export declare function flush(timeout?: number): PromiseLike<boolean>;
/**
 * A promise that resolves when all current events have been sent.
 * If you provide a timeout and the queue takes longer to drain the promise returns false.
 *
 * @param timeout Maximum time in ms the client should wait.
 */
export declare function close(timeout?: number): PromiseLike<boolean>;
/**
 * Wrap code within a try/catch block so the SDK is able to capture errors.
 *
 * @param fn A function to wrap.
 *
 * @returns The result of wrapped function call.
 */
export declare function wrap(fn: Function): any;
//# sourceMappingURL=sdk.d.ts.map