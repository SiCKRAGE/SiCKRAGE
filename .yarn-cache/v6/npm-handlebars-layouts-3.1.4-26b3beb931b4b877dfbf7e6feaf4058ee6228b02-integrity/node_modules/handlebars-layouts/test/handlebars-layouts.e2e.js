/* eslint-env mocha */
'use strict';

var handlebarsLayouts = require('../index'),
	handlebars = require('handlebars'),
	expect = require('expect'),
	fs = require('fs'),
	path = require('path'),
	through = require('through2'),
	vinylFs = require('vinyl-fs'),

	config = {
		partials: path.join(__dirname, 'fixtures/partials/'),
		fixtures: path.join(__dirname, 'fixtures/templates/'),
		expected: path.join(__dirname, 'expected/templates/'),
		actual: path.join(__dirname, 'actual/templates/')
	};

describe('handlebars-layouts e2e', function () {
	var hbs;

	function read() {
		return fs.readFileSync(path.join.apply(path, arguments), 'utf8');
	}

	function testWithFile(filename, data, done) {
		var fixture = config.fixtures + filename,
			expected = config.expected + filename;

		function compileFile(file, enc, cb) {
			var template;

			try {
				template = hbs.compile(String(file.contents));
				file.contents = new Buffer(template(data));
				this.push(file);
				cb();
			}
			catch (err) {
				cb(err);
			}
		}

		function expectFile(file) {
			expect(String(file.contents)).toBe(read(expected));
			done();
		}

		function expectError(err) {
			expect(err.message).toContain('derp');
			done();
		}

		vinylFs
			.src(fixture)
			.pipe(through.obj(compileFile))
			// .pipe(vinylFs.dest(config.actual))
			.on('data', expectFile)
			.on('error', expectError);
	}

	beforeEach(function () {
		hbs = handlebars.create();
		handlebarsLayouts.register(hbs);

		// Register partials
		hbs.registerPartial({
			'deep-a': read(config.partials, 'deep-a.hbs'),
			'deep-b': read(config.partials, 'deep-b.hbs'),
			'deep-c': read(config.partials, 'deep-c.hbs'),
			'parent-context': read(config.partials, 'parent-context.hbs'),
			context: read(config.partials, 'context.hbs'),
			layout2col: read(config.partials, 'layout2col.hbs'),
			layout: read(config.partials, 'layout.hbs'),
			media: read(config.partials, 'media.hbs'),
			user: read(config.partials, 'user.hbs')
		});
	});

	it('should extend layouts', function (done) {
		var data = require('./fixtures/data/users.json');

		testWithFile('extend.html', data, done);
	});

	it('should deeply extend layouts', function (done) {
		testWithFile('deep-extend.html', {}, done);
	});

	it('should embed layouts', function (done) {
		var data = require('./fixtures/data/users.json');

		testWithFile('embed.html', data, done);
	});

	it('should preserve context', function (done) {
		testWithFile('context.html', {root: 'root'}, done);
	});

	it('should append content', function (done) {
		testWithFile('append.html', { title: 'append' }, done);
	});

	it('should prepend content', function (done) {
		testWithFile('prepend.html', { title: 'prepend' }, done);
	});

	it('should replace content', function (done) {
		testWithFile('replace.html', { title: 'replace' }, done);
	});

	it('should ignore bogus content', function (done) {
		testWithFile('bogus.html', { title: 'bogus' }, done);
	});

	it('should pass through hash values', function (done) {
		var data = require('./fixtures/data/users.json');

		testWithFile('hash.html', data, done);
	});

	it('should pass through non-object values', function (done) {
		var data = Object.create(null);

		data.key = 'value';

		testWithFile('non-object.html', data, done);
	});

	it('should throw an error if partial is not registered', function (done) {
		testWithFile('error.html', {}, done);
	});
});
