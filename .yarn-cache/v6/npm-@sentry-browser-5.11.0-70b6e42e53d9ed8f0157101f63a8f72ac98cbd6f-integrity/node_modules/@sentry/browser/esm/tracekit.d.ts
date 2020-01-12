/**
 * This was originally forked from https://github.com/occ/TraceKit, but has since been
 * largely modified and is now maintained as part of Sentry JS SDK.
 */
/**
 * An object representing a single stack frame.
 * {Object} StackFrame
 * {string} url The JavaScript or HTML file URL.
 * {string} func The function name, or empty for anonymous functions (if guessing did not work).
 * {string[]?} args The arguments passed to the function, if known.
 * {number=} line The line number, if known.
 * {number=} column The column number, if known.
 * {string[]} context An array of source code lines; the middle element corresponds to the correct line#.
 */
export interface StackFrame {
    url: string;
    func: string;
    args: string[];
    line: number | null;
    column: number | null;
}
/**
 * An object representing a JavaScript stack trace.
 * {Object} StackTrace
 * {string} name The name of the thrown exception.
 * {string} message The exception error message.
 * {TraceKit.StackFrame[]} stack An array of stack frames.
 */
export interface StackTrace {
    name: string;
    message: string;
    mechanism?: string;
    stack: StackFrame[];
    failed?: boolean;
}
/** JSDoc */
export declare function computeStackTrace(ex: any): StackTrace;
//# sourceMappingURL=tracekit.d.ts.map