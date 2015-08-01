/*jslint devel: true, bitwise: true, regexp: true, browser: true, confusion: true, unparam: true, eqeq: true, white: true, nomen: true, plusplus: true, maxerr: 50, indent: 4 */
/*globals jQuery */

/*!
 * Coverflow
 *
 * Copyright (c) 2013-2014 Martijn W. van der Lee
 * Licensed under the MIT.
 */

/* Lightweight and flexible coverflow effect using CSS3 transforms.
 * For modern browsers with some amount of graceful degradation.
 * Optional support for jQuery.interpolate() plugin.
 * Optional support for .reflect() plugins.
 *
 * Requires jQuery 1.7+ and jQueryUI 1.9+.
 * Recommended jQuery 1.8+ and jQueryUI 1.9+.
 */

;(function($, undefined) {
	"use strict";

	var sign	= function(number) {
					return number < 0 ? -1 : 1;
				},
		scl		= function(number, fromMin, fromMax, toMin, toMax) {
					return ((number - fromMin) * (toMax - toMin) / (fromMax - fromMin)) + toMin;
				};

	$.widget("vanderlee.coverflow", {
		options: {
			animateComplete:	undefined,
			animateStep:		undefined,
			density:			1,
			duration:			'normal',
			easing:				undefined,
			index:				0,
			innerAngle:			-75,
			innerCss:			undefined,
			innerOffset:		100 / 3,
			innerScale:			0.75,
			outerAngle:			-30,
			outerCss:			undefined,
			outerScale:			0.25,
			selectedCss:		undefined,
			visible:			'density',		// 'density', 'all', NNN (exact)
			width:				undefined,

			change:				undefined,		// Whenever index is changed
			confirm:			undefined,		// Whenever clicking on the current item
			select:				undefined		// Whenever index is set (also on init)
		},

		_window_handler_resize:		null,
		_window_handler_keydown:	null,

		_create: function() {
			var that = this,
				covers = that._getCovers(),
				images = covers.filter('img').add('img', covers).filter(function() {
					return !(this.complete || this.height > 0);
				}),
				maxHeight = covers.height(),
				height;

			// Internal event prefix
			that.widgetEventPrefix	= 'vanderlee-coverflow';

			that.hovering			= false;
			that.pagesize			= 1;
			that.currentIndex		= that.options.index;
			
			// Fix height
			that.element.height(maxHeight);
			images.load(function() {
				height = that._getCovers().height();
				if (height > maxHeight) {
					maxHeight = height;
					that.element.height(maxHeight);
				}
			});

			// Hide all covers and set position to absolute
			covers.hide();

			// Enable click-jump
			that.element.on('mousedown tap', '> *', function(event) {
				var index = that._getCovers().index(this);
				if (index === that.currentIndex) {
					that._callback('confirm', event);
				} else {
					that._setIndex(index, true);
				}
			});

			// Mousewheel
			that.element.on('mousewheel', function(event, delta) {
				event.preventDefault();
				that._setIndex(that.options.index - delta, true);
			});

			// Swipe
			if ($.isFunction(that.element.swipe)) {
				that.element.swipe({
					swipe: function(event, direction, distance, duration, fingerCount) {
						var count = Math.round((direction === 'left' ? 1 : -1) * 1.25 * that.pagesize * distance / that.element.width());
						that._setIndex(that.options.index + count, true);
					}
				});
			}

			// Keyboard
			that.element.hover(
				function() { that.hovering = true; }
			,	function() { that.hovering = false; }
			);

			// Refresh on resize
			that._window_handler_resize = function() {
				that.refresh();
			};
			
			that._window_handler_keydown = function(event) {
				if (that.hovering) {
					switch (event.which) {
						case 36:	// home
							event.preventDefault();
							that._setIndex(0, true);
							break;

						case 35:	// end
							event.preventDefault();
							that._setIndex(that._getCovers().length - 1, true);
							break;

						case 38:	// up
						case 37:	// left
							event.preventDefault();
							that._setIndex(that.options.index - 1, true);
							break;

						case 40:	// down
						case 39:	// right
							event.preventDefault();
							that._setIndex(that.options.index + 1, true);
							break;

						case 33:	// page up (towards home)
							event.preventDefault();
							that._setIndex(that.options.index - that.pagesize, true);
							break;

						case 34:	// page down (towards end)
							event.preventDefault();
							that._setIndex(that.options.index + that.pagesize, true);
							break;
					}
				}
			};

			$(window).on('resize', that._window_handler_resize);
			$(window).on('keydown', that._window_handler_keydown);

			// Initialize
			that._setIndex(that.options.index, false, true);

			return that;
		},


		/**
		 * Destroy this object
		 * @returns {undefined}
		 */
		_destroy: function() {
			$(window).off('resize', this._window_handler_resize);
			$(window).off('keydown', this._window_handler_keydown);
			this.element.height('');
		},

		/**
		 * Returns the currently selected cover
		 * @returns {jQuery} jQuery object
		 */
		cover: function() {
			return $(this._getCovers()[this.options.index]);
		},

		/**
		 *
		 * @returns {unresolved}
		 */
		_getCovers: function() {
			return $('> *', this.element);
		},

		_setIndex: function(index, animate, initial) {
			var that = this,
				covers = that._getCovers();

			index = Math.max(0, Math.min(index, covers.length - 1));

			if (index !== that.options.index) {
				this.refresh();		// pre-correct for reflection/mods

				if (animate === true || that.options.duration === 0) {
					that.options.index	= Math.round(index);
					
					var duration	= typeof that.options.duration === "number"
									? that.options.duration
									: jQuery.fx.speeds[that.options.duration] || jQuery.fx.speeds._default;
					
					this.refresh(duration, that.options.index);
				} else {
					that.options.index = Math.round(index);
					that.refresh(0);
				}
			} else if (initial === true) {
				that.refresh();
				that._callback('select');
			}
		},

		_callback: function(callback, event) {
			this._trigger(callback, event, [this._getCovers().get(this.currentIndex), this.currentIndex]);
		},

		index: function(index) {
			if (index === undefined) {
				return this.options.index;
			}

			while (index < 0) {
				index += this._getCovers().length;
			}

			this._setIndex(index, true);
		},
		
		_frame: function(frame) {
			frame = frame.toFixed(6);		
				
			var that		= this,
				covers		= that._getCovers(),
				count		= covers.length,
				parentWidth	= that.element.innerWidth(),
				coverWidth	= that.options.width || covers.first().outerWidth(),
				visible		= that.options.visible === 'density'	? Math.round(parentWidth * that.options.density / coverWidth)
							: $.isNumeric(that.options.visible)		? that.options.visible
							: count,
				parentLeft	= that.element.position().left - ((1 - that.options.outerScale) * coverWidth * 0.5),
				space		= (parentWidth - (that.options.outerScale * coverWidth)) * 0.5;
		
			that.pagesize	= visible;
			
			covers.removeClass('current').each(function(index, cover) {
				var $cover		= $(cover),
					position	= index - frame,
					offset		= Math.min(Math.max(-1., position / visible), 1),
					isMiddle	= position == 0,
					zIndex		= count - Math.abs(Math.round(position)),
					isVisible	= Math.abs(position) <= visible,
					sin			= Math.sin(offset * Math.PI * 0.5),
					cos			= Math.cos(offset * Math.PI * 0.5),
					left		= sign(sin) * scl(Math.abs(sin), 0, 1, that.options.innerOffset * that.options.density, space),
					scale		= isVisible ? scl(Math.abs(cos), 1, 0, that.options.innerScale, that.options.outerScale) : 0,
					angle		= sign(sin) * scl(Math.abs(sin), 0, 1, that.options.innerAngle, that.options.outerAngle),
					css			= isMiddle ? that.options.selectedCss || {}
								: ( $.interpolate && that.options.outerCss && !$.isEmptyObject(that.options.outerCss) ? (
									isVisible ? $.interpolate(that.options.innerCss || {}, that.options.outerCss, Math.abs(sin))
											  : that.options.outerCss
									) : {}
								),
					transform;
							
				// bad behaviour for being in the middle
				if (Math.abs(position) < 1) {
					angle	= 0 - (0 - angle) * Math.abs(position);
					scale	= 1 - (1 - scale) * Math.abs(position);
					left	= 0 - (0 - left) * Math.abs(position);
				}
				
				//@todo Test CSS for middle behaviour (or does $.interpolate handle it?)

				transform = 'scale(' + scale + ',' + scale + ') perspective(' + (parentWidth * 0.5) + 'px) rotateY(' + angle + 'deg)';
				
				$cover[isMiddle ? 'addClass' : 'removeClass']('current');
				$cover[isVisible ? 'show' : 'hide']();				
						
				$cover.css($.extend(css, {
					'left':					parentLeft + space + left,
					'z-index':				zIndex,
					'-webkit-transform':	transform,
					'-ms-transform':		transform,
					'transform':			transform
				}));
				
				// Optional callback
				that._trigger('animateStep', null, [cover, offset, isVisible, isMiddle, sin, cos]);
				
				if (frame == that.options.index) {
					// Optional callback
					that._trigger('animateComplete', null, [cover, offset, isVisible, isMiddle, sin, cos]);					
				}
			});
		},

		refresh: function(duration, index) {
			var that = this,
				previous = null,
				covers = that._getCovers(),
				covercount = covers.length;
		
			covers.css('position', 'absolute');
					
			that.element.stop().animate({
				'__coverflow_frame':	index  || that.options.index
			}, {
				'easing':	that.options.easing,
				'duration': duration || 0,
				'step':		function(now, fx) {					
					that._frame(now);					
					
					that.currentIndex = Math.max(0, Math.min(Math.round(now), covercount - 1));
					if (previous !== that.currentIndex) {
						previous = that.currentIndex;
						that._callback('change');						
						that._callback('select');
					}					
				},
				'complete':		function() {
					that.currentIndex	= that.options.index;					
					that._callback('change');
					that._callback('select');
				}
			});
		}
	});
}(jQuery));