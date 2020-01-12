/* ==========================================================
 * bootstrap-formhelpers-fontsizes.js
 * https://github.com/vlamanna/BootstrapFormHelpers
 * ==========================================================
 * Copyright 2012 Vincent Lamanna
 * contributed by Aaron Collegeman, Squidoo, 2012
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


  /* FONTSIZES CLASS DEFINITION
   * ====================== */

  var BFHFontSizes = function (element, options) {
    this.options = $.extend({}, $.fn.bfhfontsizes.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addFontSizes();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapFontSizes();
    }
  };

  BFHFontSizes.prototype = {

    constructor: BFHFontSizes,

    getFontsizes: function() {
      var fontsize,
          fontsizes;

      if (this.options.available) {
        fontsizes = [];

        this.options.available = this.options.available.split(',');

        for (fontsize in BFHFontSizesList) {
          if (BFHFontSizesList.hasOwnProperty(fontsize)) {
            if ($.inArray(fontsize, this.options.available) >= 0) {
              fontsizes[fontsize] = BFHFontSizesList[fontsize];
            }
          }
        }

        return fontsizes;
      } else {
        return BFHFontSizesList;
      }
    },

    addFontSizes: function () {
      var value,
          fontsize,
          fontsizes;

      value = this.options.fontsize;
      fontsizes = this.getFontsizes();

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (fontsize in fontsizes) {
        if (fontsizes.hasOwnProperty(fontsize)) {
          this.$element.append('<option value="' + fontsize + '">' + fontsizes[fontsize] + '</option>');
        }
      }

      this.$element.val(value);
    },

    addBootstrapFontSizes: function() {
      var $input,
          $toggle,
          $options,
          value,
          fontsize,
          fontsizes;

      value = this.options.fontsize;
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');
      fontsizes = this.getFontsizes();

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (fontsize in fontsizes) {
        if (fontsizes.hasOwnProperty(fontsize)) {
          $options.append('<li><a tabindex="-1" href="#" data-option="' + fontsize + '">' + fontsizes[fontsize] + '</a></li>');
        }
      }

      this.$element.val(value);
    }

  };


  /* FONTSIZES PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhfontsizes;

  $.fn.bfhfontsizes = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhfontsizes');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhfontsizes', (data = new BFHFontSizes(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhfontsizes.Constructor = BFHFontSizes;

  $.fn.bfhfontsizes.defaults = {
    fontsize: '',
    available: '',
    blank: true
  };


  /* FONTSIZES NO CONFLICT
   * ========================== */

  $.fn.bfhfontsizes.noConflict = function () {
    $.fn.bfhfontsizes = old;
    return this;
  };


  /* FONTSIZES DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-fontsizes, span.bfh-fontsizes, div.bfh-fontsizes').each(function () {
      var $fontSizes;

      $fontSizes = $(this);

      if ($fontSizes.hasClass('bfh-selectbox')) {
        $fontSizes.bfhselectbox($fontSizes.data());
      }
      $fontSizes.bfhfontsizes($fontSizes.data());
    });
  });

}(window.jQuery);
