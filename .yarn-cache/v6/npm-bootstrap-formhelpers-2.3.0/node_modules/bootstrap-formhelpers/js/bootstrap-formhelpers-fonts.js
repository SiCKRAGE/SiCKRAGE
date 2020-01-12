/* ==========================================================
 * bootstrap-formhelpers-fonts.js
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


  /* FONTS CLASS DEFINITION
   * ====================== */

  var BFHFonts = function (element, options) {
    this.options = $.extend({}, $.fn.bfhfonts.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addFonts();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapFonts();
    }
  };

  BFHFonts.prototype = {

    constructor: BFHFonts,

    getFonts: function() {
      var font,
          fonts;

      if (this.options.available) {
        fonts = [];

        this.options.available = this.options.available.split(',');

        for (font in BFHFontsList) {
          if (BFHFontsList.hasOwnProperty(font)) {
            if ($.inArray(font, this.options.available) >= 0) {
              fonts[font] = BFHFontsList[font];
            }
          }
        }

        return fonts;
      } else {
        return BFHFontsList;
      }
    },

    addFonts: function () {
      var value,
          font,
          fonts;

      value = this.options.font;
      fonts = this.getFonts();

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (font in fonts) {
        if (fonts.hasOwnProperty(font)) {
          this.$element.append('<option value="' + font + '">' + font + '</option>');
        }
      }

      this.$element.val(value);
    },

    addBootstrapFonts: function() {
      var $input,
          $toggle,
          $options,
          value,
          font,
          fonts;

      value = this.options.font;
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');
      fonts = this.getFonts();

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (font in fonts) {
        if (fonts.hasOwnProperty(font)) {
          $options.append('<li><a tabindex="-1" href="#" style=\'font-family: ' + fonts[font] + '\' data-option="' + font + '">' + font + '</a></li>');
        }
      }

      this.$element.val(value);
    }

  };


  /* FONTS PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhfonts;

  $.fn.bfhfonts = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhfonts');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhfonts', (data = new BFHFonts(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhfonts.Constructor = BFHFonts;

  $.fn.bfhfonts.defaults = {
    font: '',
    available: '',
    blank: true
  };


  /* FONTS NO CONFLICT
   * ========================== */

  $.fn.bfhfonts.noConflict = function () {
    $.fn.bfhfonts = old;
    return this;
  };


  /* FONTS DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-fonts, span.bfh-fonts, div.bfh-fonts').each(function () {
      var $fonts;

      $fonts = $(this);

      if ($fonts.hasClass('bfh-selectbox')) {
        $fonts.bfhselectbox($fonts.data());
      }
      $fonts.bfhfonts($fonts.data());
    });
  });

}(window.jQuery);
