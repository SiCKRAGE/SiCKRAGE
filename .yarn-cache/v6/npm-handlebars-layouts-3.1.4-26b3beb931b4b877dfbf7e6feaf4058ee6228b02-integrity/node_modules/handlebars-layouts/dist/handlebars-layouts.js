(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.handlebarsLayouts = f()}})(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

var hasOwn = Object.prototype.hasOwnProperty;

function noop() {
	return '';
}

function getStack(context) {
	return context.$$layoutStack || (
		context.$$layoutStack = []
	);
}

function applyStack(context) {
	var stack = getStack(context);

	while (stack.length) {
		stack.shift()(context);
	}
}

function getActions(context) {
	return context.$$layoutActions || (
		context.$$layoutActions = {}
	);
}

function getActionsByName(context, name) {
	var actions = getActions(context);

	return actions[name] || (
		actions[name] = []
	);
}

function applyAction(val, action) {
	var context = this;

	function fn() {
		return action.fn(context, action.options);
	}

	switch (action.mode) {
		case 'append': {
			return val + fn();
		}

		case 'prepend': {
			return fn() + val;
		}

		case 'replace': {
			return fn();
		}

		default: {
			return val;
		}
	}
}

function mixin(target) {
	var arg, key,
		len = arguments.length,
		i = 1;

	for (; i < len; i++) {
		arg = arguments[i];

		if (!arg) {
			continue;
		}

		for (key in arg) {
			// istanbul ignore else
			if (hasOwn.call(arg, key)) {
				target[key] = arg[key];
			}
		}
	}

	return target;
}

/**
 * Generates an object of layout helpers.
 *
 * @type {Function}
 * @param {Object} handlebars Handlebars instance.
 * @return {Object} Object of helpers.
 */
function layouts(handlebars) {
	var helpers = {
		/**
		 * @method extend
		 * @param {String} name
		 * @param {?Object} customContext
		 * @param {Object} options
		 * @param {Function(Object)} options.fn
		 * @param {Object} options.hash
		 * @return {String} Rendered partial.
		 */
		extend: function (name, customContext, options) {
			// Make `customContext` optional
			if (arguments.length < 3) {
				options = customContext;
				customContext = null;
			}

			options = options || {};

			var fn = options.fn || noop,
				context = mixin({}, this, customContext, options.hash),
				data = handlebars.createFrame(options.data),
				template = handlebars.partials[name];

			// Partial template required
			if (template == null) {
				throw new Error('Missing partial: \'' + name + '\'');
			}

			// Compile partial, if needed
			if (typeof template !== 'function') {
				template = handlebars.compile(template);
			}

			// Add overrides to stack
			getStack(context).push(fn);

			// Render partial
			return template(context, { data: data });
		},

		/**
		 * @method embed
		 * @param {String} name
		 * @param {?Object} customContext
		 * @param {Object} options
		 * @param {Function(Object)} options.fn
		 * @param {Object} options.hash
		 * @return {String} Rendered partial.
		 */
		embed: function () {
			var context = mixin({}, this || {});

			// Reset context
			context.$$layoutStack = null;
			context.$$layoutActions = null;

			// Extend
			return helpers.extend.apply(context, arguments);
		},

		/**
		 * @method block
		 * @param {String} name
		 * @param {Object} options
		 * @param {Function(Object)} options.fn
		 * @return {String} Modified block content.
		 */
		block: function (name, options) {
			options = options || {};

			var fn = options.fn || noop,
				data = handlebars.createFrame(options.data),
				context = this || {};

			applyStack(context);

			return getActionsByName(context, name).reduce(
				applyAction.bind(context),
				fn(context, { data: data })
			);
		},

		/**
		 * @method content
		 * @param {String} name
		 * @param {Object} options
		 * @param {Function(Object)} options.fn
		 * @param {Object} options.hash
		 * @param {String} options.hash.mode
		 * @return {String} Always empty.
		 */
		content: function (name, options) {
			options = options || {};

			var fn = options.fn,
				data = handlebars.createFrame(options.data),
				hash = options.hash || {},
				mode = hash.mode || 'replace',
				context = this || {};

			applyStack(context);

			// Getter
			if (!fn) {
				return name in getActions(context);
			}

			// Setter
			getActionsByName(context, name).push({
				options: { data: data },
				mode: mode.toLowerCase(),
				fn: fn
			});
		}
	};

	return helpers;
}

/**
 * Registers layout helpers on a Handlebars instance.
 *
 * @method register
 * @param {Object} handlebars Handlebars instance.
 * @return {Object} Object of helpers.
 * @static
 */
layouts.register = function (handlebars) {
	var helpers = layouts(handlebars);

	handlebars.registerHelper(helpers);

	return helpers;
};

module.exports = layouts;

},{}]},{},[1])(1)
});