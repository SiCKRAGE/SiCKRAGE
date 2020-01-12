/** Add node transaction to the event */
var Transaction = /** @class */ (function () {
    function Transaction() {
        /**
         * @inheritDoc
         */
        this.name = Transaction.id;
    }
    /**
     * @inheritDoc
     */
    Transaction.prototype.setupOnce = function (addGlobalEventProcessor, getCurrentHub) {
        addGlobalEventProcessor(function (event) {
            var self = getCurrentHub().getIntegration(Transaction);
            if (self) {
                return self.process(event);
            }
            return event;
        });
    };
    /**
     * @inheritDoc
     */
    Transaction.prototype.process = function (event) {
        var frames = this._getFramesFromEvent(event);
        // use for loop so we don't have to reverse whole frames array
        for (var i = frames.length - 1; i >= 0; i--) {
            var frame = frames[i];
            if (frame.in_app === true) {
                event.transaction = this._getTransaction(frame);
                break;
            }
        }
        return event;
    };
    /** JSDoc */
    Transaction.prototype._getFramesFromEvent = function (event) {
        var exception = event.exception && event.exception.values && event.exception.values[0];
        return (exception && exception.stacktrace && exception.stacktrace.frames) || [];
    };
    /** JSDoc */
    Transaction.prototype._getTransaction = function (frame) {
        return frame.module || frame.function ? (frame.module || '?') + "/" + (frame.function || '?') : '<unknown>';
    };
    /**
     * @inheritDoc
     */
    Transaction.id = 'Transaction';
    return Transaction;
}());
export { Transaction };
//# sourceMappingURL=transaction.js.map