module.exports = function sentryLoader(content, map, meta) {
  const { releasePromise } = this.query;
  const callback = this.async();
  releasePromise.then(version => {
    const sentryRelease = `(typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : typeof self !== 'undefined' ? self : {}).SENTRY_RELEASE={id:"${version}"};`;
    callback(null, sentryRelease, map, meta);
  });
};
