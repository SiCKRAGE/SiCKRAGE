/**
 * Consumes the promise and logs the error when it rejects.
 * @param promise A promise to forget.
 */
export function forget(promise) {
    promise.then(null, function (e) {
        // TODO: Use a better logging mechanism
        console.error(e);
    });
}
//# sourceMappingURL=async.js.map