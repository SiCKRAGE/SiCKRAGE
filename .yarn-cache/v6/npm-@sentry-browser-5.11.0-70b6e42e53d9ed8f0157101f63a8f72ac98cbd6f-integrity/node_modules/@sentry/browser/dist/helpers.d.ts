import { Mechanism, WrappedFunction } from '@sentry/types';
/**
 * @hidden
 */
export declare function shouldIgnoreOnError(): boolean;
/**
 * @hidden
 */
export declare function ignoreNextOnError(): void;
/**
 * Instruments the given function and sends an event to Sentry every time the
 * function throws an exception.
 *
 * @param fn A function to wrap.
 * @returns The wrapped function.
 * @hidden
 */
export declare function wrap(fn: WrappedFunction, options?: {
    mechanism?: Mechanism;
}, before?: WrappedFunction): any;
//# sourceMappingURL=helpers.d.ts.map