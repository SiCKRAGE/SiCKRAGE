module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        clean: {
            dist: 'dist',
            bower_components: 'bower_components',
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
                dest: {
                    js:'dist/bower.js',
                    css:'dist/bower.css'
                },
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
                    'bootstrap-formhelpers': [
                        'dist/js/bootstrap-formhelpers.min.js',
                        'dist/css/bootstrap-formhelpers.min.css'
                    ],
                    'jquery-ui': [
                        'jquery-ui.min.js',
                        'themes/base/jquery-ui.min.css'
                    ],
                    'jquery.tablesorter': [
                        'dist/js/jquery.tablesorter.combined.min.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/js/widgets/widget-stickyHeaders.min.js',
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
                    css: 'dist/fonts.css',
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
            jquery_ui: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/jquery-ui/themes/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/gui/default/images/'
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
            },
            boostrap_formhelpers: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/bootstrap-formhelpers/img/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/gui/default/images/bootstrap-formhelpers/'
                }]
            }
        },
        uglify: {
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
            release: {
                options: {
                    after: '256',
                    logArguments: [
                        '--pretty=* %h - %ad: %s',
                        '--no-merges',
                        '--date=short'
                    ],
                    fileHeader: '# Changelog',
                    featureRegex: /^(.*)$/gim,
                    partials: {
                        features: '{{#each features}}{{> feature}}{{/each}}\n',
                        feature: '- {{this}} {{this.date}}\n',
                        fixes: '{{#each fixes}}{{> fix}}{{/each}}\n',
                        fix: '- {{this}} {{this.date}}\n'

                    },
                    dest: "changelog.md"
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