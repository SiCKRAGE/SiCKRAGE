/* jshint node: true */

module.exports = function(grunt) {
  'use strict';

  // Project configuration.
  grunt.initConfig({

    // Metadata.
    pkg: grunt.file.readJSON('package.json'),
    banner: '/**\n' +
              '* <%= pkg.name %>.js v<%= pkg.version %> by @vincentlamanna\n' +
              '* Copyright <%= grunt.template.today("yyyy") %> <%= pkg.author %>\n' +
              '* <%= _.pluck(pkg.licenses, "url").join(", ") %>\n' +
              '*/\n',
    jqueryCheck: 'if (!jQuery) { throw new Error(\"Bootstrap Form Helpers requires jQuery\"); }\n\n',

    // Task configuration.
    clean: {
      dist: ['dist']
    },

    jshint: {
      options: {
        jshintrc: 'js/.jshintrc'
      },
      gruntfile: {
        src: 'Gruntfile.js'
      },
      src: {
        src: [
          'js/lang/*/*.js',
          'js/*.js'
        ]
      },
      test: {
        src: [
          'js/tests/unit/*.js'
        ]
      }
    },

    concat: {
      options: {
        banner: '<%= banner %><%= jqueryCheck %>',
        stripBanners: false
      },
      bootstrapformhelpers: {
        src: [
          'js/lang/en_US/*.js',
          'js/*.js'
        ],
        dest: 'dist/js/<%= pkg.name %>.js'
      }
    },

    uglify: {
      options: {
        banner: '<%= banner %>'
      },
      bootstrapformhelpers: {
        src: ['<%= concat.bootstrapformhelpers.dest %>'],
        dest: 'dist/js/<%= pkg.name %>.min.js'
      }
    },
    
    recess: {
      options: {
        compile: true,
        banner: '<%= banner %>'
      },
      bootstrap: {
        src: ['less/bootstrap-formhelpers.less'],
        dest: 'dist/css/<%= pkg.name %>.css'
      },
      min: {
        options: {
          compress: true
        },
        src: ['less/bootstrap-formhelpers.less'],
        dest: 'dist/css/<%= pkg.name %>.min.css'
      }
    },
    
    copy: {
      img: {
        expand: true,
        src: ['img/*'],
        dest: 'dist/'
      }
    },
    
    karma: {
      test: {
        configFile: 'karma.conf.js'
      }
    },
    
    coveralls: {
      options: {
        coverage_dir: 'coverage'
      }
    },

    watch: {
      src: {
        files: '<%= jshint.src.src %>',
        tasks: ['jshint:src', 'qunit']
      },
      test: {
        files: '<%= jshint.test.src %>',
        tasks: ['jshint:test', 'qunit']
      },
      recess: {
        files: 'less/*.less',
        tasks: ['recess']
      }
    }
  });


  // These plugins provide necessary tasks.
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-qunit');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-recess');
  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-karma-coveralls');
  
  var testSubtasks = ['dist-css', 'jshint', 'karma'];
  // Only push to coveralls under Travis
  if (process.env.TRAVIS) {
    if ((process.env.TRAVIS_REPO_SLUG === 'vlamanna/BootstrapFormHelpers' && process.env.TRAVIS_PULL_REQUEST === 'false')) {
      testSubtasks.push('coveralls');
    }
  }
  grunt.registerTask('test', testSubtasks);

  // JS distribution task.
  grunt.registerTask('dist-js', ['concat', 'uglify']);

  // CSS distribution task.
  grunt.registerTask('dist-css', ['recess']);
  
  // Img distribution task.
  grunt.registerTask('dist-img', ['copy']);
  
  // Full distribution task.
  grunt.registerTask('dist', ['clean', 'dist-css', 'dist-img', 'dist-js']);

  // Default task.
  grunt.registerTask('default', ['test', 'dist']);
};