/* ==========================================================
 * bootstrap-formhelpers-colorpicker.js
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
  
  
  /* COLORPICKER CLASS DEFINITION
  * ========================= */

  var toggle = '[data-toggle=bfh-colorpicker]',
      BFHColorPicker = function (element, options) {
        this.options = $.extend({}, $.fn.bfhcolorpicker.defaults, options);
        this.$element = $(element);

        this.initPopover();
      };

  BFHColorPicker.prototype = {

    constructor: BFHColorPicker,

    initPalette: function() {
      var $canvas,
          context,
          gradient;
          
      $canvas = this.$element.find('canvas');
      context = $canvas[0].getContext('2d');
      
      gradient = context.createLinearGradient(0, 0, $canvas.width(), 0);
      
      gradient.addColorStop(0,    'rgb(255, 255, 255)');
      gradient.addColorStop(0.1,  'rgb(255,   0,   0)');
      gradient.addColorStop(0.25, 'rgb(255,   0, 255)');
      gradient.addColorStop(0.4,  'rgb(0,     0, 255)');
      gradient.addColorStop(0.55, 'rgb(0,   255, 255)');
      gradient.addColorStop(0.7,  'rgb(0,   255,   0)');
      gradient.addColorStop(0.85, 'rgb(255, 255,   0)');
      gradient.addColorStop(1,    'rgb(255,   0,   0)');
      
      context.fillStyle = gradient;
      context.fillRect(0, 0, context.canvas.width, context.canvas.height);
      
      gradient = context.createLinearGradient(0, 0, 0, $canvas.height());
      gradient.addColorStop(0,   'rgba(255, 255, 255, 1)');
      gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)');
      gradient.addColorStop(0.5, 'rgba(0,     0,   0, 0)');
      gradient.addColorStop(1,   'rgba(0,     0,   0, 1)');
      
      context.fillStyle = gradient;
      context.fillRect(0, 0, context.canvas.width, context.canvas.height);
    },
    
    initPopover: function() {
      var iconLeft,
          iconRight;

      iconLeft = '';
      iconRight = '';
      if (this.options.align === 'right') {
        iconRight = '<span class="input-group-addon"><span class="bfh-colorpicker-icon"></span></span>';
      } else {
        iconLeft = '<span class="input-group-addon"><span class="bfh-colorpicker-icon"></span></span>';
      }

      this.$element.html(
        '<div class="input-group bfh-colorpicker-toggle" data-toggle="bfh-colorpicker">' +
        iconLeft +
        '<input type="text" name="' + this.options.name + '" class="' + this.options.input + '" placeholder="' + this.options.placeholder + '" readonly>' +
        iconRight +
        '</div>' +
        '<div class="bfh-colorpicker-popover">' +
        '<canvas class="bfh-colorpicker-palette" width="384" height="256"></canvas>' +
        '</div>'
      );

      // this.$element
      //   .on('click.bfhcolorpicker.data-api touchstart.bfhcolorpicker.data-api', toggle, BFHColorPicker.prototype.toggle)
      //   .on('mousedown.bfhcolorpicker.data-api', 'canvas', BFHColorPicker.prototype.mouseDown)
      //   .on('click.bfhcolorpicker.data-api touchstart.bfhcolorpicker.data-api', '.bfh-colorpicker-popover', function() { return false; });
      
      this.$element
      .on('click.bfhcolorpicker.data-api', toggle, BFHColorPicker.prototype.toggle)
      .on('mousedown.bfhcolorpicker.data-api', 'canvas', BFHColorPicker.prototype.mouseDown)
      .on('click.bfhcolorpicker.data-api', '.bfh-colorpicker-popover', function() { return false; });

      this.initPalette();
      
      this.$element.val(this.options.color);
    },
    
    updateVal: function(positionX, positionY) {
      var $canvas,
          context,
          colorX,
          colorY,
          snappiness,
          imageData,
          newColor;
      
      snappiness = 5;
      
      $canvas = this.$element.find('canvas');
      context = $canvas[0].getContext('2d');
      
      colorX = positionX - $canvas.offset().left;
      colorY = positionY - $canvas.offset().top;
      
      colorX = Math.round(colorX / snappiness) * snappiness;
      colorY = Math.round(colorY / snappiness) * snappiness;
      
      if (colorX < 0) {
        colorX = 0;
      }
      if (colorX >= $canvas.width()) {
        colorX = $canvas.width() - 1;
      }
      
      if (colorY < 0) {
        colorY = 0;
      }
      if (colorY > $canvas.height()) {
        colorY = $canvas.height();
      }
      
      imageData = context.getImageData(colorX, colorY, 1, 1);
      newColor = rgbToHex(imageData.data[0], imageData.data[1], imageData.data[2]);
      
      if (newColor !== this.$element.val()) {
        this.$element.val(newColor);
        
        this.$element.trigger('change.bfhcolorpicker');
      }
    },
    
    mouseDown: function(e) {
      var $this,
          $parent;
      
      $this = $(this);
      $parent = getParent($this);
      
      $(document)
        .on('mousemove.bfhcolorpicker.data-api', {colorpicker: $parent}, BFHColorPicker.prototype.mouseMove)
        .one('mouseup.bfhcolorpicker.data-api', {colorpicker: $parent}, BFHColorPicker.prototype.mouseUp);
    },
    
    mouseMove: function(e) {
      var $this;
      
      $this = e.data.colorpicker;
      
      $this.data('bfhcolorpicker').updateVal(e.pageX, e.pageY);
    },
    
    mouseUp: function(e) {
      var $this;
      
      $this = e.data.colorpicker;
      
      $this.data('bfhcolorpicker').updateVal(e.pageX, e.pageY);
      
      $(document).off('mousemove.bfhcolorpicker.data-api');
      
      if ($this.data('bfhcolorpicker').options.close === true) {
        clearMenus();
      }
    },

    toggle: function (e) {
      var $this,
          $parent,
          isActive;

      $this = $(this);
      $parent = getParent($this);

      if ($parent.is('.disabled') || $parent.attr('disabled') !== undefined) {
        return true;
      }

      isActive = $parent.hasClass('open');

      clearMenus();

      if (!isActive) {
        $parent.trigger(e = $.Event('show.bfhcolorpicker'));

        if (e.isDefaultPrevented()) {
          return true;
        }

        $parent
          .toggleClass('open')
          .trigger('shown.bfhcolorpicker');

        $this.focus();
      }

      return false;
    }
  };
  
  function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }

  function rgbToHex(r, g, b) {
    return '#' + componentToHex(r) + componentToHex(g) + componentToHex(b);
  }
      
  function clearMenus() {
    var $parent;

    $(toggle).each(function (e) {
      $parent = getParent($(this));

      if (!$parent.hasClass('open')) {
        return true;
      }

      $parent.trigger(e = $.Event('hide.bfhcolorpicker'));

      if (e.isDefaultPrevented()) {
        return true;
      }

      $parent
        .removeClass('open')
        .trigger('hidden.bfhcolorpicker');
    });
  }

  function getParent($this) {
    return $this.closest('.bfh-colorpicker');
  }
  
  
  /* COLORPICKER PLUGIN DEFINITION
   * ========================== */

  var old = $.fn.bfhcolorpicker;

  $.fn.bfhcolorpicker = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhcolorpicker');
      options = typeof option === 'object' && option;
      this.type = 'bfhcolorpicker';

      if (!data) {
        $this.data('bfhcolorpicker', (data = new BFHColorPicker(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhcolorpicker.Constructor = BFHColorPicker;

  $.fn.bfhcolorpicker.defaults = {
    align: 'left',
    input: 'form-control',
    placeholder: '',
    name: '',
    color: '#000000',
    close: true
  };
  
  
  /* COLORPICKER NO CONFLICT
   * ========================== */

  $.fn.bfhcolorpicker.noConflict = function () {
    $.fn.bfhcolorpicker = old;
    return this;
  };
  
  
  /* COLORPICKER VALHOOKS
   * ========================== */

  var origHook;
  if ($.valHooks.div){
    origHook = $.valHooks.div;
  }
  $.valHooks.div = {
    get: function(el) {
      if ($(el).hasClass('bfh-colorpicker')) {
        return $(el).find('input[type="text"]').val();
      } else if (origHook) {
        return origHook.get(el);
      }
    },
    set: function(el, val) {
      if ($(el).hasClass('bfh-colorpicker')) {
        $(el).find('.bfh-colorpicker-icon').css('background-color', val);
        $(el).find('input[type="text"]').val(val);
      } else if (origHook) {
        return origHook.set(el,val);
      }
    }
  };
  
  
  /* COLORPICKER DATA-API
   * ============== */

  $(document).ready( function () {
    $('div.bfh-colorpicker').each(function () {
      var $colorpicker;

      $colorpicker = $(this);

      $colorpicker.bfhcolorpicker($colorpicker.data());
    });
  });
  
  
  /* APPLY TO STANDARD COLORPICKER ELEMENTS
   * =================================== */

  $(document)
    .on('click.bfhcolorpicker.data-api', clearMenus);

}(window.jQuery);