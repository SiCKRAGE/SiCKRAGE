module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        'string-replace': {
          inline: {
            files: {
              './': 'sickrage/locale/**/LC_MESSAGES/*.po'
            },
            options: {
              replacements: [
                {
                  pattern: /("PO-Revision-Date.*")/ig,
                  replacement: ''
                }
              ]
            }
          }
        },
        clean: {
            bower_components: 'bower_components',
            //sass: [
            //    '.sass-cache',
            //    'sickrage/core/webserver/static/scss/'
            //],
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
                    js: 'dist/js/bower.js',
                    css: 'dist/css/bower.css'
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
                        'dist/js/jquery.tablesorter.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/js/widgets/widget-stickyHeaders.min.js',
                        'dist/js/widgets/widget-reflow.min.js',
                        'dist/js/widgets/widget-filter.min.js',
                        'dist/js/widgets/widget-saveSort.min.js',
                        'dist/js/widgets/widget-storage.min.js',
                        'dist/css/theme.blue.css'
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
                    "bootstrap-tokenfield": [
                        "dist/bootstrap-tokenfield.js",
                        "dist/css/tokenfield-typeahead.css",
                        "dist/css/bootstrap-tokenfield.css"
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
                    fontPath: 'sickrage/core/webserver/static/fonts/',
                    cssFile: 'dist/css/fonts.css',
                    httpPath: '../fonts/',
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
                        },
                        {
                            family: 'Roboto',
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
                    dest: 'sickrage/core/webserver/static/fonts/'
                }]
            },
            fontawesome: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/components-font-awesome/fonts/',
                    src: ['**/*.{eot,svg,ttf,woff,woff2}'],
                    dest: 'sickrage/core/webserver/static/fonts/'
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
                    dest: 'sickrage/core/webserver/static/images/'
                }]
            },
            tablesorter: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/jquery.tablesorter/dist/css/images/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/static/images/tablesorter/'
                }]
            },
            boostrap_formhelpers: {
                files: [{
                    expand: true,
                    flatten: true,
                    cwd: 'bower_components/bootstrap-formhelpers/img/',
                    src: ['**/*.{png,jpg,gif}'],
                    dest: 'sickrage/core/webserver/static/images/bootstrap-formhelpers/'
                }]
            }
        },
        sprite: {
            icons_sickrage: {
                src: 'dist/images/icons/sickrage/*.png',
                dest: 'sickrage/core/webserver/static/images/icons-sickrage.png',
                destCss: 'dist/css/icons-sickrage.css',
                imgPath: '../images/icons-sickrage.png',
                cssTemplate: 'dist/css/icons-sickrage.css.handlebars',
                padding: 2
            }
        },
        uglify: {
            bower: {
                files: {
                    'sickrage/core/webserver/static/js/bower.min.js': ['dist/js/bower.js']
                }
            },
            core: {
                files: {
                    'sickrage/core/webserver/static/js/core.min.js': ['dist/js/core.js']
                }
            }
        },
        sass: {
            core: {
                files: {
                    'sickrage/core/webserver/static/scss/core.scss': [
                        'dist/css/core.css',
                        'dist/css/fonts.css',
                        'dist/css/icons-sickrage.css'
                    ]
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
                    'sickrage/core/webserver/static/css/bower.min.css': ['dist/css/bower.css']
                }
            },
            core: {
                files: {
                    'sickrage/core/webserver/static/css/core.min.css': [
                        'dist/css/core.css',
                        'dist/css/fonts.css',
                        'dist/css/icons-sickrage.css'
                    ]
                }
            }
        },
        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            all: ['dist/js/core.js']
        },
        po2json: {
            messages: {
                options: {
                    singleFile: true
                },
                files: [{
                    expand: true,
                    src: 'sickrage/locale/*/LC_MESSAGES/messages.po',
                    dest: '',
                    ext: ''
                }]
            }
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
        },
        exec: {
            // Translations
            'crowdin_upload_sources': {cmd: 'crowdin-cli-py upload sources'},
            'crowdin_upload_translations': {cmd: 'crowdin-cli-py upload translations'},
            'crowdin_download_translations': {cmd: 'crowdin-cli-py download'},
            'babel_extract': {cmd: 'python setup.py extract_messages'},
            'babel_update': {cmd: 'python setup.py update_catalog'},
            'babel_compile': {cmd: 'python setup.py compile_catalog'},

            // PyPi Commands
            'pypi_publish': {cmd: 'python setup.py sdist bdist_wheel upload clean'},

            // Git Commands
            'git': {
                cmd: function (cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                }
            },
            'git_push': {
                cmd: function (remote, branch, tags) {
                    var pushCmd = 'git push ' + remote + ' ' + branch;
                    if (tags) {
                        pushCmd += ' --tags';
                    }
                    return pushCmd;
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
                }
            },
            'git_commit': {
                cmd: function (message) {
                    return 'git commit -am "' + message + '"';
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
                }
            },
            'git_last_tag': {
                cmd: 'git for-each-ref refs/tags --sort=-taggerdate --count=1 --format=%(refname:short)',
                stdout: false,
                callback: function (err, stdout) {
                    stdout = stdout.trim();
                    if (/^\d{1,2}.\d{1,2}.\d+(?:.dev\d+)?$/.test(stdout)) {
                        grunt.config('last_tag', stdout);
                    } else {
                        grunt.fatal('Could not get the last tag name. We got: ' + stdout);
                    }
                }
            },
            'git_list_changes': {
                cmd: function () {
                    return 'git log --oneline --pretty=format:%s ' + grunt.config('last_tag') + '..HEAD';
                },
                stdout: false,
                callback: function (err, stdout) {
                    var commits = stdout.trim()
                        .replace(/`/gm, '').replace(/^\([\w\d\s,.\-+_/>]+\)\s/gm, '');  // removes ` and tag information
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                }
            },
            'git_tag': {
                cmd: function (sign) {
                    sign = sign !== "true" ? '' : '-s ';
                    return 'git tag ' + sign + grunt.config('new_version') + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            },
            'git_flow_bugfix_start': {
                cmd: function (version) {
                    return 'git flow bugfix start ' + version;
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
                }
            },
            'git_flow_bugfix_finish': {
                cmd: function (version, message) {
                    return 'git flow bugfix finish ' + version;
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
                }
            },
            'git_flow_release_start': {
                cmd: function (version) {
                    return 'git flow release start ' + version;
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
                }
            },
            'git_flow_release_finish': {
                cmd: function (version, message) {
                    return 'git flow release finish ' + version + ' -m "' + message + '"';
                },
                stderr: false,
                callback: function (err, stdout, stderr) {
                    grunt.log.write(stderr);
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
            'sprite',
            'sass',
            'cssmin',
            'jshint'
        ]
    );

    grunt.registerTask(
        'css', [
            'sprite',
            'sass',
            'cssmin'
        ]
    );

    grunt.registerTask('upload_trans', 'Upload translations', function () {
        grunt.log.writeln('Extracting and uploading translations to Crowdin...'.magenta);

        var tasks = [
            'exec:babel_extract',
            'exec:crowdin_upload_sources'
        ];

        if (process.env.CROWDIN_API_KEY) {
            grunt.task.run(tasks);
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, aborting task'.bold);
        }
    });

    grunt.registerTask('download_trans', 'Download translations', function () {
        grunt.log.writeln('Downloading and compiling translations from Crowdin...'.magenta);

        var tasks = [
            'exec:crowdin_download_translations',
            'string-replace',
            'exec:babel_compile',
            'po2json'
        ];

        if (process.env.CROWDIN_API_KEY) {
            grunt.task.run(tasks);
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, aborting task.'.bold);
        }
    });

    grunt.registerTask('sync_trans', 'Sync translations with Crowdin', function () {
        grunt.log.writeln('Syncing translations with Crowdin...'.magenta);

        var tasks = [
            'upload_trans',
            'download_trans'
        ];

        if (process.env.CROWDIN_API_KEY) {
            grunt.task.run(tasks);
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, aborting task.'.bold);
        }
    });

    grunt.registerTask('pre-release', function () {
        grunt.task.run(['exec:git:checkout:develop']);

        var vFile = 'sickrage/version.txt';

        var version = grunt.file.read(vFile);
        var versionParts = version.split('.');
        var vArray = {
            vMajor: versionParts[0],
            vMinor: versionParts[1],
            vPatch: versionParts[2],
            vPre: versionParts[3] || 0
        };

        if (vArray.vPre !== 0) {
            vArray.vPre = vArray.vPre.split('dev')[1];
        }

        if (vArray.vPre === 0) {
            vArray.vPatch = parseFloat(vArray.vPatch) + 1;
        }

        vArray.vPre = parseFloat(vArray.vPre) + 1;

        var newVersion = vArray.vMajor + '.' + vArray.vMinor + '.' + vArray.vPatch + '.dev' + vArray.vPre;
        grunt.config('new_version', newVersion);

        grunt.file.write(vFile, newVersion);

        grunt.log.writeln(('Packaging Pre-Release v' + newVersion).magenta);

        var tasks = [
            'default',
            'sync_trans', // sync translations with crowdin
            'exec:git_commit:Pre-Release v' + newVersion,
            'exec:git_last_tag','exec:git_list_changes','exec:git_tag',
            'exec:git_push:origin:develop:tags',
            'exec:pypi_publish'
        ];

        grunt.task.run(tasks);
    });

    grunt.registerTask('release', function () {
        grunt.task.run(['exec:git:checkout:develop']);

        var vFile = 'sickrage/version.txt';
        var version = grunt.file.read(vFile);
        var versionParts = version.split('.');
        var vArray = {
            vMajor: versionParts[0],
            vMinor: versionParts[1],
            vPatch: versionParts[2],
            vPre: versionParts[3] || 0
        };

        if (vArray.vPre === 0) {
            vArray.vPatch = parseFloat(vArray.vPatch) + 1;
        }

        var newVersion = vArray.vMajor + '.' + vArray.vMinor + '.' + vArray.vPatch;

        grunt.config('new_version', newVersion);
        grunt.file.write(vFile, newVersion);

        grunt.log.writeln(('Packaging Release v' + newVersion).magenta);

        var tasks = [
            'default',
            'sync_trans', // sync translations with crowdin
            'exec:git_commit:Release v' + newVersion,
            'exec:git_flow_release_start:' + newVersion,
            'exec:git_flow_release_finish:' + newVersion + ':Release v' + newVersion,
            'exec:git_push:origin:develop:tags',
            'exec:git_push:origin:master:tags',
            'exec:pypi_publish'
        ];

        grunt.task.run(tasks);
    });
};