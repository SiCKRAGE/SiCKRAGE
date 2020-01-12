import * as tslib_1 from "tslib";
import { consoleSandbox } from '@sentry/utils';
/** JSDoc */
var Debug = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Debug(options) {
        /**
         * @inheritDoc
         */
        this.name = Debug.id;
        this._options = tslib_1.__assign({ debugger: false, stringify: false }, options);
    }
    /**
     * @inheritDoc
     */
    Debug.prototype.setupOnce = function (addGlobalEventProcessor, getCurrentHub) {
        addGlobalEventProcessor(function (event, hint) {
            var self = getCurrentHub().getIntegration(Debug);
            if (self) {
                // tslint:disable:no-console
                // tslint:disable:no-debugger
                if (self._options.debugger) {
                    debugger;
                }
                consoleSandbox(function () {
                    if (self._options.stringify) {
                        console.log(JSON.stringify(event, null, 2));
                        if (hint) {
                            console.log(JSON.stringify(hint, null, 2));
                        }
                    }
                    else {
                        console.log(event);
                        if (hint) {
                            console.log(hint);
                        }
                    }
                });
            }
            return event;
        });
    };
    /**
     * @inheritDoc
     */
    Debug.id = 'Debug';
    return Debug;
}());
export { Debug };
//# sourceMappingURL=debug.js.map