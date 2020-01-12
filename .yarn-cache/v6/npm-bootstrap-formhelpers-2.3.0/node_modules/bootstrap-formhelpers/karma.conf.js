module.exports = function(config) {
  config.set({
    basePath: '',
    autoWatch: true,
    frameworks: ['qunit'],
    files: [
      'js/tests/vendor/js/jquery-1.10.2.js',
      'js/tests/fixture.js',
      'js/tests/vendor/js/bootstrap-3.0.0.min.js',
      'js/lang/en_US/*.js',
      'js/*.js',
      'js/tests/unit/*.js'
    ],
    browsers: ['PhantomJS'],

    reporters: ['progress', 'coverage'],
    preprocessors: { 'js/*.js': ['coverage'] },

    singleRun: true,
    
    coverageReporter: {
      type: "lcov",
      dir: "coverage/"
    }
  });
};