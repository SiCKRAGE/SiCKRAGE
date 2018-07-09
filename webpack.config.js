const path = require('path');
const webpack = require('webpack');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const OptimizeCSSAssetsPlugin = require("optimize-css-assets-webpack-plugin");

module.exports = {
    entry: './src/app.js',
    output: {
        path: path.resolve(__dirname, 'sickrage/core/webserver/static/js'),
        filename: 'core.min.js'
    },
    module: {
        rules: [
            {
                test: /\.s?css$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    "css-loader",
                    "sass-loader"
                ]
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "eslint-loader"
            },
            {
                test: /\.js$/,
                exclude: [
                    /node_modules/,
                    /spec/
                ],
                loader: "babel-loader",
                options: {
                    presets: ['env']
                }
            },
            {
                test: /\.(woff|woff2|eot|ttf|svg)$/,
                use: [{
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: '../fonts/'
                    }
                }]
            },
            {
                test: /\.(jpe?g|png|gif)$/i,
                loader: "file-loader",
                query: {
                    name: '[name].[ext]',
                    outputPath: '../images/'
                }
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery'
        }),
        new CleanWebpackPlugin(['sickrage/core/webserver/static/css/*.*', 'sickrage/core/webserver/static/js/*.*']),
        new MiniCssExtractPlugin({
            filename: "../css/core.min.css",
            chunkFilename: "[id].css"
        }),
        new OptimizeCSSAssetsPlugin()
    ]
};