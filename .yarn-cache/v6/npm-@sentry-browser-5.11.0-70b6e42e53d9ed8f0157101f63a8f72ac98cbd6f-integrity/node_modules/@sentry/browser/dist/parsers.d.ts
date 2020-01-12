import { Event, Exception, StackFrame } from '@sentry/types';
import { StackFrame as TraceKitStackFrame, StackTrace as TraceKitStackTrace } from './tracekit';
/**
 * This function creates an exception from an TraceKitStackTrace
 * @param stacktrace TraceKitStackTrace that will be converted to an exception
 * @hidden
 */
export declare function exceptionFromStacktrace(stacktrace: TraceKitStackTrace): Exception;
/**
 * @hidden
 */
export declare function eventFromPlainObject(exception: {}, syntheticException?: Error, rejection?: boolean): Event;
/**
 * @hidden
 */
export declare function eventFromStacktrace(stacktrace: TraceKitStackTrace): Event;
/**
 * @hidden
 */
export declare function prepareFramesForEvent(stack: TraceKitStackFrame[]): StackFrame[];
//# sourceMappingURL=parsers.d.ts.map