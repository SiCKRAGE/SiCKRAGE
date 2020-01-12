Object.defineProperty(exports, "__esModule", { value: true });
var utils_1 = require("@sentry/utils");
/** JSDoc */
var Vue = /** @class */ (function () {
    /**
     * @inheritDoc
     */
    function Vue(options) {
        if (options === void 0) { options = {}; }
        /**
         * @inheritDoc
         */
        this.name = Vue.id;
        /**
         * When set to false, Sentry will suppress reporting all props data
         * from your Vue components for privacy concerns.
         */
        this._attachProps = true;
        /**
         * When set to true, original Vue's `logError` will be called as well.
         * https://github.com/vuejs/vue/blob/c2b1cfe9ccd08835f2d99f6ce60f67b4de55187f/src/core/util/error.js#L38-L48
         */
        this._logErrors = false;
        // tslint:disable-next-line: no-unsafe-any
        this._Vue = options.Vue || utils_1.getGlobalObject().Vue;
        if (options.logErrors !== undefined) {
            this._logErrors = options.logErrors;
        }
        if (options.attachProps === false) {
            this._attachProps = false;
        }
    }
    /** JSDoc */
    Vue.prototype._formatComponentName = function (vm) {
        // tslint:disable:no-unsafe-any
        if (vm.$root === vm) {
            return 'root instance';
        }
        var name = vm._isVue ? vm.$options.name || vm.$options._componentTag : vm.name;
        return ((name ? "component <" + name + ">" : 'anonymous component') +
            (vm._isVue && vm.$options.__file ? " at " + vm.$options.__file : ''));
    };
    /**
     * @inheritDoc
     */
    Vue.prototype.setupOnce = function (_, getCurrentHub) {
        // tslint:disable:no-unsafe-any
        var _this = this;
        if (!this._Vue || !this._Vue.config) {
            utils_1.logger.error('VueIntegration is missing a Vue instance');
            return;
        }
        var oldOnError = this._Vue.config.errorHandler;
        this._Vue.config.errorHandler = function (error, vm, info) {
            var metadata = {};
            if (utils_1.isPlainObject(vm)) {
                metadata.componentName = _this._formatComponentName(vm);
                if (_this._attachProps) {
                    metadata.propsData = vm.$options.propsData;
                }
            }
            if (info !== void 0) {
                metadata.lifecycleHook = info;
            }
            if (getCurrentHub().getIntegration(Vue)) {
                // This timeout makes sure that any breadcrumbs are recorded before sending it off the sentry
                setTimeout(function () {
                    getCurrentHub().withScope(function (scope) {
                        scope.setContext('vue', metadata);
                        getCurrentHub().captureException(error);
                    });
                });
            }
            if (typeof oldOnError === 'function') {
                oldOnError.call(_this._Vue, error, vm, info);
            }
            if (_this._logErrors) {
                _this._Vue.util.warn("Error in " + info + ": \"" + error.toString() + "\"", vm);
                // tslint:disable-next-line:no-console
                console.error(error);
            }
        };
    };
    /**
     * @inheritDoc
     */
    Vue.id = 'Vue';
    return Vue;
}());
exports.Vue = Vue;
//# sourceMappingURL=vue.js.map