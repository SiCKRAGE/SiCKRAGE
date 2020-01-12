Object.defineProperty(exports, "__esModule", { value: true });
var utils_1 = require("@sentry/utils");
/** JSDoc */
var Ember = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Ember(options) {
        if (options === void 0) { options = {}; }
        /**
         * @inheritDoc
         */
        this.name = Ember.id;
        // tslint:disable-next-line: no-unsafe-any
        this._Ember = options.Ember || utils_1.getGlobalObject().Ember;
    }
    /**
     * @inheritDoc
     */
    Ember.prototype.setupOnce = function (_, getCurrentHub) {
        // tslint:disable:no-unsafe-any
        var _this = this;
        if (!this._Ember) {
            utils_1.logger.error('EmberIntegration is missing an Ember instance');
            return;
        }
        var oldOnError = this._Ember.onerror;
        this._Ember.onerror = function (error) {
            if (getCurrentHub().getIntegration(Ember)) {
                getCurrentHub().captureException(error, { originalException: error });
            }
            if (typeof oldOnError === 'function') {
                oldOnError.call(_this._Ember, error);
            }
            else if (_this._Ember.testing) {
                throw error;
            }
        };
        this._Ember.RSVP.on('error', function (reason) {
            if (getCurrentHub().getIntegration(Ember)) {
                getCurrentHub().withScope(function (scope) {
                    if (utils_1.isInstanceOf(reason, Error)) {
                        scope.setExtra('context', 'Unhandled Promise error detected');
                        getCurrentHub().captureException(reason, { originalException: reason });
                    }
                    else {
                        scope.setExtra('reason', reason);
                        getCurrentHub().captureMessage('Unhandled Promise error detected');
                    }
                });
            }
        });
    };
    /**
     * @inheritDoc
     */
    Ember.id = 'Ember';
    return Ember;
}());
exports.Ember = Ember;
//# sourceMappingURL=ember.js.map