import { Event } from '@sentry/types';
/** JSDoc */
export declare function eventFromUnknownInput(exception: unknown, syntheticException?: Error, options?: {
    rejection?: boolean;
    attachStacktrace?: boolean;
}): Event;
/** JSDoc */
export declare function eventFromString(input: string, syntheticException?: Error, options?: {
    attachStacktrace?: boolean;
}): Event;
//# sourceMappingURL=eventbuilder.d.ts.map