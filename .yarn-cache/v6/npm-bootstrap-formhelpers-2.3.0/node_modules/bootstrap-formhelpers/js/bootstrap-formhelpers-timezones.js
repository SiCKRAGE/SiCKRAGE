/* ==========================================================
 * bootstrap-formhelpers-timezones.js
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


  /* TIMEZONES CLASS DEFINITION
   * ====================== */

  var BFHTimezones = function (element, options) {
    this.options = $.extend({}, $.fn.bfhtimezones.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addTimezones();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapTimezones();
    }
  };

  BFHTimezones.prototype = {

    constructor: BFHTimezones,

    addTimezones: function () {
      var country,
          $country;

      country = this.options.country;

      if (country !== '') {
        $country = $(document).find('#' + country);

        if ($country.length !== 0) {
          country = $country.val();
          $country.on('change', {timezone: this}, this.changeCountry);
        }
      }

      this.loadTimezones(country);
    },

    loadTimezones: function (country) {
      var value,
          timezone;

      value = this.options.timezone;

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (timezone in BFHTimezonesList[country]) {
        if (BFHTimezonesList[country].hasOwnProperty(timezone)) {
          this.$element.append('<option value="' + timezone + '">' + BFHTimezonesList[country][timezone] + '</option>');
        }
      }

      this.$element.val(value);
    },

    changeCountry: function (e) {
      var $this,
          $timezone,
          country;

      $this = $(this);
      $timezone = e.data.timezone;
      country = $this.val();

      $timezone.loadTimezones(country);
    },

    addBootstrapTimezones: function() {
      var country,
          $country;

      country = this.options.country;

      if (country !== '') {
        $country = $(document).find('#' + country);

        if ($country.length !== 0) {
          country = $country.find('input[type="hidden"]').val();
          $country.on('change.bfhselectbox', {timezone: this}, this.changeBootstrapCountry);
        }
      }

      this.loadBootstrapTimezones(country);
    },

    loadBootstrapTimezones: function(country) {
      var $input,
          $toggle,
          $options,
          value,
          timezone;

      value = this.options.timezone;
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (timezone in BFHTimezonesList[country]) {
        if (BFHTimezonesList[country].hasOwnProperty(timezone)) {
          $options.append('<li><a tabindex="-1" href="#" data-option="' + timezone + '">' + BFHTimezonesList[country][timezone] + '</a></li>');
        }
      }

      this.$element.val(value);
    },

    changeBootstrapCountry: function (e) {
      var $this,
          $timezone,
          country;

      $this = $(this);
      $timezone = e.data.timezone;
      country = $this.val();

      $timezone.loadBootstrapTimezones(country);
    }

  };


  /* TIMEZONES PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhtimezones;

  $.fn.bfhtimezones = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhtimezones');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhtimezones', (data = new BFHTimezones(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhtimezones.Constructor = BFHTimezones;

  $.fn.bfhtimezones.defaults = {
    country: '',
    timezone: '',
    blank: true
  };


  /* TIMEZONES NO CONFLICT
   * ========================== */

  $.fn.bfhtimezones.noConflict = function () {
    $.fn.bfhtimezones = old;
    return this;
  };


  /* TIMEZONES DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-timezones, div.bfh-timezones').each(function () {
      var $timezones;

      $timezones = $(this);

      if ($timezones.hasClass('bfh-selectbox')) {
        $timezones.bfhselectbox($timezones.data());
      }
      $timezones.bfhtimezones($timezones.data());
    });
  });

}(window.jQuery);
