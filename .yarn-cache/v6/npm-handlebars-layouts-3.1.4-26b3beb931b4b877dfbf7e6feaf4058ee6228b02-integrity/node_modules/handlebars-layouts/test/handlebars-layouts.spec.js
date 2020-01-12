/* eslint-env mocha */
'use strict';

var handlebarsLayouts = require('../index'),
	handlebars = require('handlebars'),
	expect = require('expect');

describe('handlebars-layouts spec', function () {
	var count, hbs;

	beforeEach(function () {
		count = 0;

		hbs = handlebars.create();

		hbs.registerPartial('foo', function (data) {
			count++;

			return data && data.foo || '';
		});
	});

	it('should generate helpers', function () {
		var helpers = handlebarsLayouts(handlebarsLayouts);

		expect(helpers.extend).toBeA(Function);
		expect(helpers.embed).toBeA(Function);
		expect(helpers.block).toBeA(Function);
		expect(helpers.content).toBeA(Function);

		expect(count).toBe(0);
	});

	describe('register', function () {
		it('should register helpers', function () {
			handlebarsLayouts.register(hbs);

			expect(hbs.helpers.extend).toBeA(Function);
			expect(hbs.helpers.embed).toBeA(Function);
			expect(hbs.helpers.block).toBeA(Function);
			expect(hbs.helpers.content).toBeA(Function);

			expect(count).toBe(0);
		});
	});

	describe('#extend', function () {
		it('should use fallback values as needed', function () {
			var helpers = handlebarsLayouts.register(hbs);

			expect(helpers.extend.call(null, 'foo')).toBe('');
			expect(helpers.extend.call({ foo: 'bar' }, 'foo')).toBe('bar');

			expect(count).toBe(2);
		});
	});

	describe('#embed', function () {
		it('should use fallback values as needed', function () {
			var helpers = handlebarsLayouts.register(hbs);

			expect(helpers.embed.call(null, 'foo')).toBe('');
			expect(helpers.embed.call({ foo: 'bar' }, 'foo')).toBe('bar');

			expect(count).toBe(2);
		});
	});

	describe('#block', function () {
		it('should use fallback values as needed', function () {
			var helpers = handlebarsLayouts.register(hbs);

			expect(helpers.block.call(null, 'foo')).toBe('');
			expect(helpers.block.call({ foo: 'bar' }, 'foo')).toBe('');

			expect(count).toBe(0);
		});
	});

	describe('#content', function () {
		it('should use fallback values as needed', function () {
			var helpers = handlebarsLayouts.register(hbs);

			expect(helpers.content.call(null, 'foo')).toBe(false);
			expect(helpers.content.call({ foo: 'bar' }, 'foo')).toBe(false);

			expect(count).toBe(0);
		});
	});
});
