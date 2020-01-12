/* ==========================================================
 * bootstrap-formhelpers-languages.js
 * https://github.com/vlamanna/BootstrapFormHelpers
 * ==========================================================
 * Copyright 2012 Vincent Lamanna
 * Contribution 2013 Tomasz Kuter
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


  /* LANGUAGES CLASS DEFINITION
   * ====================== */

  var BFHLanguages = function (element, options) {
    this.options = $.extend({}, $.fn.bfhlanguages.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addLanguages();
    }

    if (this.$element.is('span')) {
      this.displayLanguage();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapLanguages();
    }
  };

  BFHLanguages.prototype = {

    constructor: BFHLanguages,

    getLanguages: function () {
      var split,
          language,
          languages;

      if (this.options.available) {
        languages = [];

        this.options.available = this.options.available.split(',');

        for (language in this.options.available) {
          if (this.options.available.hasOwnProperty(language)) {
            if (this.options.available[language].indexOf('_') !== -1) {
              split = this.options.available[language].split('_');
              languages[split[0]] = {name: BFHLanguagesList[split[0]], country: split[1]};
            } else {
              languages[this.options.available[language]] = BFHLanguagesList[this.options.available[language]];
            }
          }
        }

        return languages;
      } else {
        return BFHLanguagesList;
      }
    },

    addLanguages: function () {
      var split,
          value,
          languages,
          language;

      value = this.options.language;
      languages = this.getLanguages();

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (language in languages) {
        if (languages.hasOwnProperty(language)) {
          if (languages[language].hasOwnProperty('name')) {
            this.$element.append('<option value="' + language + '_' + languages[language].country + '">' + languages[language].name.toProperCase() + ' (' + BFHCountriesList[languages[language].country] + ')</option>');
          } else {
            this.$element.append('<option value="' + language + '">' + languages[language].toProperCase() + '</option>');
          }
        }
      }

      this.$element.val(value);
    },

    addBootstrapLanguages: function() {
      var $input,
          $toggle,
          $options,
          value,
          languages,
          language,
          split;

      value = this.options.language;
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');
      languages = this.getLanguages();

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (language in languages) {
        if (languages.hasOwnProperty(language)) {
          if (languages[language].hasOwnProperty('name')) {
            if (this.options.flags === true) {
              $options.append('<li><a tabindex="-1" href="#" data-option="' + language + '_' + languages[language].country + '"><i class="glyphicon bfh-flag-' + languages[language].country + '"></i>' + languages[language].name.toProperCase() + '</a></li>');
            } else {
              $options.append('<li><a tabindex="-1" href="#" data-option="' + language + '_' + languages[language].country + '">' + languages[language].name.toProperCase() + ' (' + BFHCountriesList[languages[language].country] + ')</a></li>');
            }
          } else {
            $options.append('<li><a tabindex="-1" href="#" data-option="' + language + '">' + languages[language] + '</a></li>');
          }
        }
      }

      this.$element.val(value);
    },

    displayLanguage: function () {
      var value;

      value = this.options.language;

      if (value.indexOf('_') !== -1) {
        value = value.split('_');
        if (this.options.flags === true) {
          this.$element.html('<i class="glyphicon bfh-flag-' + value[1] + '"></i> ' + BFHLanguagesList[value[0]].toProperCase());
        } else {
          this.$element.html(BFHLanguagesList[value[0]].toProperCase() + ' (' + BFHCountriesList[value[1]] + ')');
        }
      } else {
        this.$element.html(BFHLanguagesList[value].toProperCase());
      }
    }

  };


  /* LANGUAGES PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhlanguages;

  $.fn.bfhlanguages = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhlanguages');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhlanguages', (data = new BFHLanguages(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhlanguages.Constructor = BFHLanguages;

  $.fn.bfhlanguages.defaults = {
    language: '',
    available: '',
    flags: false,
    blank: true
  };


  /* LANGUAGES NO CONFLICT
   * ========================== */

  $.fn.bfhlanguages.noConflict = function () {
    $.fn.bfhlanguages = old;
    return this;
  };


  /* LANGUAGES DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-languages, span.bfh-languages, div.bfh-languages').each(function () {
      var $languages;

      $languages = $(this);

      if ($languages.hasClass('bfh-selectbox')) {
        $languages.bfhselectbox($languages.data());
      }
      $languages.bfhlanguages($languages.data());
    });
  });


  /* LANGUAGES HELPERS
   * ============== */

  String.prototype.toProperCase = function () {
    return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
  };

}(window.jQuery);
