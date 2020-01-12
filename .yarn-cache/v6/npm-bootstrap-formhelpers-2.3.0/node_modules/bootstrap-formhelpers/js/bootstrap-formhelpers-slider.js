/* ==========================================================
 * bootstrap-formhelpers-slider.js
 * https://github.com/vlamanna/BootstrapFormHelpers
 * ==========================================================
 * Copyright 2012 Vincent Lamanna
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

+function ($) {

  'use strict';


  /* BFHSLIDER CLASS DEFINITION
   * ========================= */

  var BFHSlider = function (element, options) {
        this.options = $.extend({}, $.fn.bfhslider.defaults, options);
        this.$element = $(element);
        
        this.initSlider();
      };

  BFHSlider.prototype = {

    constructor: BFHSlider,

    initSlider: function() {
      if (this.options.value === '') {
        this.options.value = this.options.min;
      }
      
      this.$element.html(
        '<input type="hidden" name="' + this.options.name + '" value="">' +
        '<div class="bfh-slider-handle"><div class="bfh-slider-value"></div></div>'
      );
      
      this.$element.find('input[type="hidden"]').val(this.options.value);
      this.updateHandle(this.options.value);
      
      this.$element
        .on('mousedown.bfhslider.data-api', BFHSlider.prototype.mouseDown);
    },
    
    updateHandle: function(val) {
      var positionX,
          width,
          left,
          span;
          
      span = this.options.max - this.options.min;
      width = this.$element.width();
      left = this.$element.position().left;
      
      positionX = Math.round((val - this.options.min) * (width - 20) / span + left);
      
      this.$element.find('.bfh-slider-handle').css('left', positionX + 'px');
      this.$element.find('.bfh-slider-value').text(val);
    },
    
    updateVal: function(positionX) {
      var width,
          left,
          right,
          val,
          span;
      
      span = this.options.max - this.options.min;
      width = this.$element.width();
      left = this.$element.offset().left;
      right = left + width;
      
      if (positionX < left) {
        positionX = left;
      }
      
      if (positionX + 20 > right) {
        positionX = right;
      }
      
      val = (positionX - left) / width;
      val = Math.ceil(val * span + this.options.min);
      
      if (val === this.$element.val()) {
        return true;
      }
      
      this.$element.val(val);
      
      this.$element.trigger('change.bfhslider');
    },
    
    mouseDown: function() {
      var $this;
      
      $this = $(this);
      
      if ($this.is('.disabled') || $this.attr('disabled') !== undefined) {
        return true;
      }
      
      $(document)
        .on('mousemove.bfhslider.data-api', {slider: $this}, BFHSlider.prototype.mouseMove)
        .one('mouseup.bfhslider.data-api touchend.bfhslider.data-api', {slider: $this}, BFHSlider.prototype.mouseUp);
    },
    
    mouseMove: function(e) {
      var $this;
      
      $this = e.data.slider;
      
      $this.data('bfhslider').updateVal(e.pageX);
    },
    
    mouseUp: function(e) {
      var $this;
      
      $this = e.data.slider;
      
      $this.data('bfhslider').updateVal(e.pageX);
      
      $(document).off('mousemove.bfhslider.data-api touchmove.bfhslider.data-api');
    }
  };


  /* SLIDER PLUGIN DEFINITION
   * ========================== */

  var old = $.fn.bfhslider;

  $.fn.bfhslider = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhslider');
      options = typeof option === 'object' && option;
      this.type = 'bfhslider';

      if (!data) {
        $this.data('bfhslider', (data = new BFHSlider(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhslider.Constructor = BFHSlider;

  $.fn.bfhslider.defaults = {
    name: '',
    value: '',
    min: 0,
    max: 100
  };


  /* SLIDER NO CONFLICT
   * ========================== */

  $.fn.bfhslider.noConflict = function () {
    $.fn.bfhslider = old;
    return this;
  };


  /* SLIDER VALHOOKS
   * ========================== */

  var origHook;
  if ($.valHooks.div){
    origHook = $.valHooks.div;
  }
  $.valHooks.div = {
    get: function(el) {
      if ($(el).hasClass('bfh-slider')) {
        return $(el).find('input[type="hidden"]').val();
      } else if (origHook) {
        return origHook.get(el);
      }
    },
    set: function(el, val) {
      if ($(el).hasClass('bfh-slider')) {
        $(el).find('input[type="hidden"]').val(val);
        $(el).data('bfhslider').updateHandle(val);
      } else if (origHook) {
        return origHook.set(el,val);
      }
    }
  };


  /* SLIDER DATA-API
   * ============== */

  $(document).ready( function () {
    $('div.bfh-slider').each(function () {
      var $slider;

      $slider = $(this);

      $slider.bfhslider($slider.data());
    });
  });

}(window.jQuery);
