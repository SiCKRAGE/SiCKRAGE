import * as tslib_1 from "tslib";
import { getGlobalObject, logger } from '@sentry/utils';
// See https://github.com/angular/angular.js/blob/v1.4.7/src/minErr.js
var angularPattern = /^\[((?:[$a-zA-Z0-9]+:)?(?:[$a-zA-Z0-9]+))\] (.*?)\n?(\S+)$/;
/**
 * AngularJS integration
 *
 * Provides an $exceptionHandler for AngularJS
 */
var Angular = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Angular(options) {
        if (options === void 0) { options = {}; }
        /**
         * @inheritDoc
         */
        this.name = Angular.id;
        // tslint:disable-next-line: no-unsafe-any
        this._angular = options.angular || getGlobalObject().angular;
    }
    /**
     * @inheritDoc
     */
    Angular.prototype.setupOnce = function (_, getCurrentHub) {
        var _this = this;
        if (!this._angular) {
            logger.error('AngularIntegration is missing an Angular instance');
            return;
        }
        this._getCurrentHub = getCurrentHub;
        // tslint:disable: no-unsafe-any
        this._angular.module(Angular.moduleName, []).config([
            '$provide',
            function ($provide) {
                $provide.decorator('$exceptionHandler', ['$delegate', _this._$exceptionHandlerDecorator.bind(_this)]);
            },
        ]);
        // tslint:enable: no-unsafe-any
    };
    /**
     * Angular's exceptionHandler for Sentry integration
     */
    // tslint:disable-next-line: no-unsafe-any
    Angular.prototype._$exceptionHandlerDecorator = function ($delegate) {
        var _this = this;
        return function (exception, cause) {
            var hub = _this._getCurrentHub && _this._getCurrentHub();
            if (hub && hub.getIntegration(Angular)) {
                hub.withScope(function (scope) {
                    if (cause) {
                        scope.setExtra('cause', cause);
                    }
                    scope.addEventProcessor(function (event) {
                        var ex = event.exception && event.exception.values && event.exception.values[0];
                        if (ex) {
                            var matches = angularPattern.exec(ex.value || '');
                            if (matches) {
                                // This type now becomes something like: $rootScope:inprog
                                ex.type = matches[1];
                                ex.value = matches[2];
                                event.message = ex.type + ": " + ex.value;
                                // auto set a new tag specifically for the angular error url
                                event.extra = tslib_1.__assign({}, event.extra, { angularDocs: matches[3].substr(0, 250) });
                            }
                        }
                        return event;
                    });
                    hub.captureException(exception);
                });
            }
            // tslint:disable-next-line: no-unsafe-any
            $delegate(exception, cause);
        };
    };
    /**
     * @inheritDoc
     */
    Angular.id = 'AngularJS';
    /**
     * moduleName used in Angular's DI resolution algorithm
     */
    Angular.moduleName = 'ngSentry';
    return Angular;
}());
export { Angular };
//# sourceMappingURL=angular.js.map