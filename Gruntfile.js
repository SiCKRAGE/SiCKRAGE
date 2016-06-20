module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        clean: {
            dist: 'dist',
            bower_components: 'bower_components',
            fonts: 'sickrage/core/webserver/gui/default/fonts/',
            images: [
                'sickrage/core/webserver/gui/default/images/ui/',
                'sickrage/core/webserver/gui/default/images/tablesorter/'
            ],
            sass: [
                '.sass-cache',
                'sickrage/core/webserver/gui/default/scss/'
            ],
            options: {
                force: true
            }
        },
        bower: {
            install: {
                options: {
                    copy: false
                }
            }
        },
        bower_concat: {
            all: {
                dest: 'dist/bower.js',
                cssDest: 'dist/bower.css',
                callback: function (mainFiles) {
                    return mainFiles.map(function (filepath) {
                        var min = filepath.replace(/\.js$/, '.min.js');
                        return grunt.file.exists(min) ? min : filepath;
                    });
                },
                mainFiles: {
                    'bootstrap': [
                        'dist/css/bootstrap.min.css',
                        'dist/js/bootstrap.min.js'
                    ],
                    'jquery-ui': [
                        'jquery-ui.min.js',
                        'themes/base/jquery-ui.min.css'
                    ],
                    'bootstrap-formhelpers': [
                        'dist/js/bootstrap-formhelpers.min.js',
                        'dist/css/bootstrap-formhelpers.min.css'
                    ],
                    'jquery.tablesorter': [
                        'dist/js/jquery.tablesorter.combined.min.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/css/theme.blue.min.css'
                    ],
                    'isotope': [
                        "dist/isotope.pkgd.min.js"
                    ],
                    'jquery-json': [
                        'dist/jquery.json.min.js'
                    ],
                    'pnotify': [
                        'dist/pnotify.js',
                        'dist/pnotify.desktop.js',
                        'dist/pnotify.nonblock.js',
                        'dist/pnotify.css'
                    ],
                    "outlayer": [
                        "item.js",
                        "outlayer.js"
                    ],
                    "qtip2": [
                        "jquery.qtip.min.js",
                        "jquery.qtip.min.css"
                    ]
                },
                bowerOptions: {
                    relative: false
                },
                dependencies: {
                    'selectboxes': 'jquery',
                    'bookmarkscroll': 'jquery'
                }
            }
        },
        googlefonts: {
            build: {
                options: {
                    fontPath: 'sickrage/core/webserver/gui/default/fonts/',
                    cssFile: 'dist/fonts.css',
                    formats: {
                        eot: true,
                        ttf: true,
                        woff: true,
                        woff2: true,
                        svg: true
                    },
                    fonts: [
                        {
                            family: 'Open Sans',
                            styles: [
                                300, '300italic',
                                400, '400italic',
                                600, '600italic',
                                700, '700italic',
                                800, '800italic'
                            ]
                        },
                        {
                            family: 'Droid Sans',
                            styles: [
                                400, 700
                            ]
                        }
                    ]
                }
            }
        },
        copy: {
            glyphicon: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/bootstrap/fonts/',
                    src: ['**/*.{eot,svg,ttf,woff,woff2}'],
                    dest: 'sickrage/core/webserver/gui/default/fonts/'
                }]
            }
        },
        imagemin: {
            options: {
                optimizationLevel: 3
            },
            jqueryui: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/jquery-ui/themes/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/gui/default/images/ui/'
                }]
            },
            tablesorter: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/jquery.tablesorter/dist/css/images/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/gui/default/images/tablesorter/'
                }]
            }
        },
        uglify: {
            options: {
                mangle: false
            },
            bower: {
                files: {
                    'sickrage/core/webserver/gui/default/js/bower.min.js': ['dist/bower.js']
                }
            },
            core: {
                files: {
                    'sickrage/core/webserver/gui/default/js/core.min.js': [
                        'sickrage/core/webserver/gui/default/js/core.js'
                    ]
                }
            }
        },
        sass: {
            core: {
                files: {
                    'sickrage/core/webserver/gui/default/scss/core.scss': 'sickrage/core/webserver/gui/default/css/core.css'
                }
            }
        },
        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1
            },
            bower: {
                files: {
                    'sickrage/core/webserver/gui/default/css/bower.min.css': ['dist/bower.css']
                }
            },
            core: {
                files: {
                    'sickrage/core/webserver/gui/default/css/core.min.css': [
                        'sickrage/core/webserver/gui/default/css/core.css',
                        'dist/fonts.css'
                    ]
                }
            }
        },
        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            all: [
                'sickrage/core/webserver/gui/default/js/**/*.js',
                '!sickrage/core/webserver/gui/default/js/**/*.min.js'
            ]
        },
        changelog: {
            sample: {
                options: {
                    fileHeader: '# Changelog',
                    dest: 'changelog.md',
                    logArguments: [
                        '--pretty=* %h - %ad: %s',
                        '--no-merges',
                        '--date=short'
                    ],
                    template: '{{> features}}',
                    featureRegex: /^(.*)$/gim,
                    partials: {
                        features: '{{#if features}}{{#each features}}{{> feature}}{{/each}}{{else}}{{> empty}}{{/if}}\n',
                        feature: '- {{this}} {{this.date}}\n'
                    }
                }
            }
        }
    });

    grunt.registerTask(
        'default', [
            'clean',
            'bower',
            'bower_concat',
            'googlefonts',
            'copy',
            'imagemin',
            'uglify',
            'sass',
            'cssmin',
            'jshint'
        ]
    );
};