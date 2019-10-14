module.exports = function (grunt) {
    const shell = require('shelljs');
    const webpackConfig = require('./webpack.config');

    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        webpack: {
            options: {
                stats: !process.env.NODE_ENV || process.env.NODE_ENV === 'development'
            },
            prod: webpackConfig,
            dev: webpackConfig
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

            // Git Commands
            'git': {
                cmd: function (cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                }
            },
            'git_push': {
                cmd: function (remote, branch, tags) {
                    let pushCmd = 'git push ' + remote + ' ' + branch;
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
                maxBuffer: 500 * 1024,
                callback: function (err, stdout) {
                    const commits = stdout.trim()
                        .replace(/`/gm, '').replace(/^\([\w\d\s,.\-+_/>]+\)\s/gm, '');  // removes ` and tag information
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                }
            },
            'git_tag': {
                cmd: function (version) {
                    return 'git tag ' + version + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            }
        }
    });

    grunt.registerTask('upload_trans', 'Upload translations', function () {
        grunt.log.writeln('Extracting and uploading translations to Crowdin...'.magenta);

        const tasks = [
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

        const tasks = [
            'exec:crowdin_download_translations',
            'exec:babel_compile'
        ];

        if (process.env.CROWDIN_API_KEY) {
            grunt.task.run(tasks);
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, aborting task.'.bold);
        }
    });

    grunt.registerTask('sync_trans', 'Sync translations with Crowdin', function () {
        grunt.log.writeln('Syncing translations with Crowdin...'.magenta);

        const tasks = [
            'upload_trans',
            'download_trans'
        ];

        if (process.env.CROWDIN_API_KEY) {
            grunt.task.run(tasks);
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, aborting task.'.bold);
        }
    });

    grunt.registerTask('bump_version', function (new_version) {
        const vFile = 'sickrage/version.txt';
        grunt.file.write(vFile, new_version)
    });

    grunt.registerTask('pre-release', function () {
        grunt.task.run(['exec:git:checkout:develop']);

        const vFile = 'sickrage/version.txt';
        const version = grunt.file.read(vFile);
        const versionParts = version.split('.');
        const vArray = {
            vMajor: versionParts[0],
            vMinor: versionParts[1],
            vPatch: versionParts[2],
            vPre: versionParts[3] || 0
        };

        if (vArray.vPre === 0) {
            vArray.vPatch = parseFloat(vArray.vPatch) + 1;
        }

        if (vArray.vPre !== 0) {
            vArray.vPre = vArray.vPre.split('dev')[1];
            vArray.vPre = parseFloat(vArray.vPre) + 1;
        } else {
            vArray.vPre = parseFloat(vArray.vPre) + 1;
        }

        const newVersion = vArray.vMajor + '.' + vArray.vMinor + '.' + vArray.vPatch + '.dev' + vArray.vPre;

        const tasks = [
            'changelog',
            'webpack:dev',
            //'sync_trans',
            'bump_version:' + newVersion,
            'exec:git_commit:Pre-Release v' + newVersion,
            'exec:git_last_tag', 'exec:git_list_changes', 'exec:git_tag:' + newVersion,
            'exec:git_push:origin:develop:tags',
        ];

        grunt.task.run(tasks);
    });

    grunt.registerTask('release', function () {
        grunt.task.run(['exec:git:checkout:develop']);

        const vFile = 'sickrage/version.txt';
        const version = grunt.file.read(vFile);
        const versionParts = version.split('.');
        const vArray = {
            vMajor: versionParts[0],
            vMinor: versionParts[1],
            vPatch: versionParts[2],
            vPre: versionParts[3] || 0
        };

        if (vArray.vPre === 0) {
            vArray.vPatch = parseFloat(vArray.vPatch) + 1;
        }

        if (vArray.vPre !== 0) {
            vArray.vPre = vArray.vPre.split('dev')[1];
            vArray.vPre = parseFloat(vArray.vPre) + 1;
        } else {
            vArray.vPre = parseFloat(vArray.vPre) + 1;
        }

        const newVersion = vArray.vMajor + '.' + vArray.vMinor + '.' + vArray.vPatch;

        const tasks = [
            'exec:git:checkout:-b release-v' + newVersion + ':develop',
            'changelog',
            'webpack:prod',
            //'sync_trans',
            'bump_version:' + newVersion,
            'exec:git_commit:Release v' + newVersion,
            'exec:git:checkout:master',
            'exec:git:merge:release-v' + newVersion,
            'exec:git_last_tag', 'exec:git_list_changes', 'exec:git_tag:' + newVersion,
            'exec:git_push:origin:master:tags',
            'exec:git:checkout:develop',
            'exec:git:merge:release-v' + newVersion,
            'exec:git_push:origin:develop',
            'exec:git:branch:-d release-v' + newVersion,
        ];

        grunt.task.run(tasks);
    });
};