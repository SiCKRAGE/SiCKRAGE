Object.defineProperty(exports, "__esModule", { value: true });
/**
 * Consumes the promise and logs the error when it rejects.
 * @param promise A promise to forget.
 */
function forget(promise) {
    promise.then(null, function (e) {
        // TODO: Use a better logging mechanism
        console.error(e);
    });
}
exports.forget = forget;
//# sourceMappingURL=async.js.map