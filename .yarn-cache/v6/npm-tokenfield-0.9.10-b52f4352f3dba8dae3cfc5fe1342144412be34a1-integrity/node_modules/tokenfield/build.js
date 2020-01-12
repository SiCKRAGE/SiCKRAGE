var fs = require('fs');
var path = require('path');
var sass = require('node-sass');
var webpack = require('webpack');

var targets = [
  {
    target: 'web',
    output: {
      path: __dirname + '/dist',
      filename: 'tokenfield.min.js',
      libraryTarget: 'var',
      library: 'Tokenfield'
    },
    plugins: [
      new webpack.optimize.UglifyJsPlugin({minimize: true})
    ]
  },
  {
    target: 'web',
    output: {
      path: __dirname + '/dist',
      filename: 'tokenfield.web.js',
      libraryTarget: 'var',
      library: 'Tokenfield'
    }
  },
  {
    target: 'node',
    output: {
      path: __dirname + '/dist',
      filename: 'tokenfield.js',
      libraryTarget: 'commonjs2'
    }
  }
];

var baseConfig = {
  entry: './index',
  module: {
    loaders: [
      {
        test: /\.js$/,
        include: path.join(__dirname, 'lib'),
        loaders: ['babel-loader', 'eslint-loader']
      }
    ]
  }
};

sass.render({
  sourceMap: true,
  file: 'lib/scss/tokenfield.scss',
  outFile: __dirname + '/dist/tokenfield.css'
}, function(err, result) {
  if (err) {
    console.log(err);
    return 1;
  }

  fs.writeFile(__dirname + '/dist/tokenfield.css', result.css, function(err) {
    if (err) {
      console.log(err);
      return 1;
    }

    fs.writeFile(__dirname + '/dist/tokenfield.css.map', result.map, function(err) {
      if (err) {
        console.log(err);
        return 1;
      }
      console.log('SASS compiled to CSS');
    });
  });
});

targets.forEach(function(target) {
  var config = Object.assign({}, baseConfig, target);

  webpack(config).run(function(err, stats) {
    console.log('Generating minified bundle for production use via Webpack...');

    if (err) {
      console.log(err);
      return 1;
    }

    var jsonStats = stats.toJson();

    if (jsonStats.hasErrors) return jsonStats.errors.map(function(error) { return console.log(error); });

    if (jsonStats.hasWarnings) {
      console.log('Webpack generated the following warnings: ');
      jsonStats.warnings.map(function(warning) { return console.log(warning); });
    }

    console.log('Webpack stats: ' + stats.toString());

    //if we got this far, the build succeeded.
    console.log('Package has been compiled into /dist.');
    return 0;
  });
});
