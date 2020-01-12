/* ==========================================================
 * bootstrap-formhelpers-states.js
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


  /* STATES CLASS DEFINITION
   * ====================== */

  var BFHStates = function (element, options) {
    this.options = $.extend({}, $.fn.bfhstates.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addStates();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapStates();
    }

    if (this.$element.is('span')) {
      this.displayState();
    }
  };

  BFHStates.prototype = {

    constructor: BFHStates,

    addStates: function () {
      var country,
          $country;

      country = this.options.country;

      if (country !== '') {
        $country = $(document).find('#' + country);

        if ($country.length !== 0) {
          country = $country.val();
          $country.on('change', {state: this}, this.changeCountry);
        }
      }

      this.loadStates(country);
    },

    loadStates: function (country) {
      var value,
          state;

      value = this.options.state;

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (state in BFHStatesList[country]) {
        if (BFHStatesList[country].hasOwnProperty(state)) {
          this.$element.append('<option value="' + BFHStatesList[country][state].code + '">' + BFHStatesList[country][state].name + '</option>');
        }
      }

      this.$element.val(value);
    },

    changeCountry: function (e) {
      var $this,
          $state,
          country;

      $this = $(this);
      $state = e.data.state;
      country = $this.val();

      $state.loadStates(country);
    },

    addBootstrapStates: function() {
      var country,
          $country;

      country = this.options.country;

      if (country !== '') {
        $country = $(document).find('#' + country);

        if ($country.length !== 0) {
          country = $country.find('input[type="hidden"]').val();
          $country.on('change.bfhselectbox', {state: this}, this.changeBootstrapCountry);
        }
      }

      this.loadBootstrapStates(country);
    },

    loadBootstrapStates: function(country) {
      var $input,
          $toggle,
          $options,
          stateCode,
          stateName,
          state;

      stateCode = this.options.state;
      stateName = '';
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (state in BFHStatesList[country]) {
        if (BFHStatesList[country].hasOwnProperty(state)) {
          $options.append('<li><a tabindex="-1" href="#" data-option="' + BFHStatesList[country][state].code + '">' + BFHStatesList[country][state].name + '</a></li>');

          if (BFHStatesList[country][state].code === stateCode) {
            stateName = BFHStatesList[country][state].name;
          }
        }
      }

      this.$element.val(stateCode);
    },

    changeBootstrapCountry: function (e) {
      var $this,
          $state,
          country;

      $this = $(this);
      $state = e.data.state;
      country = $this.val();

      $state.loadBootstrapStates(country);
    },

    displayState: function () {
      var country,
          stateCode,
          stateName,
          state;

      country = this.options.country;
      stateCode = this.options.state;
      stateName = '';

      for (state in BFHStatesList[country]) {
        if (BFHStatesList[country].hasOwnProperty(state)) {
          if (BFHStatesList[country][state].code === stateCode) {
            stateName = BFHStatesList[country][state].name;
            break;
          }
        }
      }
      this.$element.html(stateName);
    }

  };


  /* STATES PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhstates;

  $.fn.bfhstates = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhstates');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhstates', (data = new BFHStates(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhstates.Constructor = BFHStates;

  $.fn.bfhstates.defaults = {
    country: '',
    state: '',
    blank: true
  };


  /* STATES NO CONFLICT
   * ========================== */

  $.fn.bfhstates.noConflict = function () {
    $.fn.bfhstates = old;
    return this;
  };


  /* STATES DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-states, span.bfh-states, div.bfh-states').each(function () {
      var $states;

      $states = $(this);

      if ($states.hasClass('bfh-selectbox')) {
        $states.bfhselectbox($states.data());
      }
      $states.bfhstates($states.data());
    });
  });

}(window.jQuery);
