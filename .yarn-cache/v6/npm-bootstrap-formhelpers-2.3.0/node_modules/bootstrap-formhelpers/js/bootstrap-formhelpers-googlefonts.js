/* ==========================================================
 * bootstrap-formhelpers-googlefonts.js
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


  /* GOOGLE FONTS CLASS DEFINITION
   * ====================== */

  var BFHGoogleFonts = function (element, options) {
    this.options = $.extend({}, $.fn.bfhgooglefonts.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addFonts();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapFonts();
    }
  };

  BFHGoogleFonts.prototype = {

    constructor: BFHGoogleFonts,

    getFonts: function() {
      var font,
          fonts;

      fonts = [];

      if (this.options.subset) {
        for (font in BFHGoogleFontsList.items) {
          if (BFHGoogleFontsList.items.hasOwnProperty(font)) {
            if ($.inArray(this.options.subset, BFHGoogleFontsList.items[font].subsets) >= 0) {
              fonts[BFHGoogleFontsList.items[font].family] = {
                'info': BFHGoogleFontsList.items[font],
                'index': parseInt(font, 10)
              };
            }
          }
        }
      } else if (this.options.available) {
        this.options.available = this.options.available.split(',');

        for (font in BFHGoogleFontsList.items) {
          if (BFHGoogleFontsList.items.hasOwnProperty(font)) {
            if ($.inArray(BFHGoogleFontsList.items[font].family, this.options.available) >= 0) {
              fonts[BFHGoogleFontsList.items[font].family] = {
                'info': BFHGoogleFontsList.items[font],
                'index': parseInt(font, 10)
              };
            }
          }
        }
      } else {
        for (font in BFHGoogleFontsList.items) {
          if (BFHGoogleFontsList.items.hasOwnProperty(font)) {
            fonts[BFHGoogleFontsList.items[font].family] = {
              'info': BFHGoogleFontsList.items[font],
              'index': parseInt(font, 10)
            };
          }
        }
      }

      return fonts;
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
          this.$element.append('<option value="' + fonts[font].info.family + '">' + fonts[font].info.family + '</option>');
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
        $options.append('<li><a tabindex="-1" href="#" data-option="" style="background-image: none;"></a></li>');
      }

      for (font in fonts) {
        if (fonts.hasOwnProperty(font)) {
          $options.append('<li><a tabindex="-1" href="#" style="background-position: 0 -' + ((fonts[font].index * 30) - 2) + 'px;" data-option="' + fonts[font].info.family + '">' + fonts[font].info.family + '</a></li>');
        }
      }

      this.$element.val(value);
    }

  };


  /* GOOGLE FONTS PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhgooglefonts;

  $.fn.bfhgooglefonts = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhgooglefonts');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhgooglefonts', (data = new BFHGoogleFonts(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhgooglefonts.Constructor = BFHGoogleFonts;

  $.fn.bfhgooglefonts.defaults = {
    font: '',
    available: '',
    subset: '',
    blank: true
  };


  /* GOOGLE FONTS NO CONFLICT
   * ========================== */

  $.fn.bfhgooglefonts.noConflict = function () {
    $.fn.bfhgooglefonts = old;
    return this;
  };


  /* GOOGLE FONTS DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-googlefonts, span.bfh-googlefonts, div.bfh-googlefonts').each(function () {
      var $googleFonts;

      $googleFonts = $(this);

      if ($googleFonts.hasClass('bfh-selectbox')) {
        $googleFonts.bfhselectbox($googleFonts.data());
      }
      $googleFonts.bfhgooglefonts($googleFonts.data());
    });
  });

}(window.jQuery);
