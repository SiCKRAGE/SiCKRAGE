import { addExceptionMechanism, addExceptionTypeValue, isDOMError, isDOMException, isError, isErrorEvent, isEvent, isPlainObject, } from '@sentry/utils';
import { eventFromPlainObject, eventFromStacktrace, prepareFramesForEvent } from './parsers';
import { computeStackTrace } from './tracekit';
/** JSDoc */
export function eventFromUnknownInput(exception, syntheticException, options) {
    if (options === void 0) { options = {}; }
    var event;
    if (isErrorEvent(exception) && exception.error) {
        // If it is an ErrorEvent with `error` property, extract it to get actual Error
        var errorEvent = exception;
        exception = errorEvent.error; // tslint:disable-line:no-parameter-reassignment
        event = eventFromStacktrace(computeStackTrace(exception));
        return event;
    }
    if (isDOMError(exception) || isDOMException(exception)) {
        // If it is a DOMError or DOMException (which are legacy APIs, but still supported in some browsers)
        // then we just extract the name and message, as they don't provide anything else
        // https://developer.mozilla.org/en-US/docs/Web/API/DOMError
        // https://developer.mozilla.org/en-US/docs/Web/API/DOMException
        var domException = exception;
        var name_1 = domException.name || (isDOMError(domException) ? 'DOMError' : 'DOMException');
        var message = domException.message ? name_1 + ": " + domException.message : name_1;
        event = eventFromString(message, syntheticException, options);
        addExceptionTypeValue(event, message);
        return event;
    }
    if (isError(exception)) {
        // we have a real Error object, do nothing
        event = eventFromStacktrace(computeStackTrace(exception));
        return event;
    }
    if (isPlainObject(exception) || isEvent(exception)) {
        // If it is plain Object or Event, serialize it manually and extract options
        // This will allow us to group events based on top-level keys
        // which is much better than creating new group when any key/value change
        var objectException = exception;
        event = eventFromPlainObject(objectException, syntheticException, options.rejection);
        addExceptionMechanism(event, {
            synthetic: true,
        });
        return event;
    }
    // If none of previous checks were valid, then it means that it's not:
    // - an instance of DOMError
    // - an instance of DOMException
    // - an instance of Event
    // - an instance of Error
    // - a valid ErrorEvent (one with an error property)
    // - a plain Object
    //
    // So bail out and capture it as a simple message:
    event = eventFromString(exception, syntheticException, options);
    addExceptionTypeValue(event, "" + exception, undefined);
    addExceptionMechanism(event, {
        synthetic: true,
    });
    return event;
}
// this._options.attachStacktrace
/** JSDoc */
export function eventFromString(input, syntheticException, options) {
    if (options === void 0) { options = {}; }
    var event = {
        message: input,
    };
    if (options.attachStacktrace && syntheticException) {
        var stacktrace = computeStackTrace(syntheticException);
        var frames_1 = prepareFramesForEvent(stacktrace.stack);
        event.stacktrace = {
            frames: frames_1,
        };
    }
    return event;
}
//# sourceMappingURL=eventbuilder.js.map