/* ==========================================================
 * bootstrap-formhelpers-currencies.js
 * https://github.com/vlamanna/BootstrapFormHelpers
 * ==========================================================
 * Copyright 2013 Vincent Lamanna
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


  /* COUNTRIES CLASS DEFINITION
   * ====================== */

  var BFHCurrencies = function (element, options) {
    this.options = $.extend({}, $.fn.bfhcurrencies.defaults, options);
    this.$element = $(element);

    if (this.$element.is('select')) {
      this.addCurrencies();
    }

    if (this.$element.hasClass('bfh-selectbox')) {
      this.addBootstrapCurrencies();
    }

    if (this.$element.is('span')) {
      this.displayCurrency();
    }
  };

  BFHCurrencies.prototype = {

    constructor: BFHCurrencies,

    getCurrencies: function () {
      var currency,
          currencies;

      if (this.options.available) {
        currencies = [];

        this.options.available = this.options.available.split(',');

        for (currency in BFHCurrenciesList) {
          if (BFHCurrenciesList.hasOwnProperty(currency)) {
            if ($.inArray(currency, this.options.available) >= 0) {
              currencies[currency] = BFHCurrenciesList[currency];
            }
          }
        }

        return currencies;
      } else {
        return BFHCurrenciesList;
      }
    },

    addCurrencies: function () {
      var value,
          currency,
          currencies;

      value = this.options.currency;
      currencies = this.getCurrencies();

      this.$element.html('');

      if (this.options.blank === true) {
        this.$element.append('<option value=""></option>');
      }

      for (currency in currencies) {
        if (currencies.hasOwnProperty(currency)) {
          this.$element.append('<option value="' + currency + '">' + currencies[currency].label + '</option>');
        }
      }

      this.$element.val(value);
    },


    addBootstrapCurrencies: function() {
      var $input,
          $toggle,
          $options,
          value,
          currency,
          currencies,
          flag;

      value = this.options.currency;
      $input = this.$element.find('input[type="hidden"]');
      $toggle = this.$element.find('.bfh-selectbox-option');
      $options = this.$element.find('[role=option]');
      currencies = this.getCurrencies();

      $options.html('');

      if (this.options.blank === true) {
        $options.append('<li><a tabindex="-1" href="#" data-option=""></a></li>');
      }

      for (currency in currencies) {
        if (currencies.hasOwnProperty(currency)) {
          if (this.options.flags === true) {
            if (currencies[currency].currencyflag) {
              flag = currencies[currency].currencyflag;
            } else {
              flag = currency.substr(0,2);
            }
            $options.append('<li><a tabindex="-1" href="#" data-option="' + currency +  '"><i class="glyphicon bfh-flag-' + flag + '"></i>' + currencies[currency].label + '</a></li>');
          } else {
            $options.append('<li><a tabindex="-1" href="#" data-option="' + currency + '">' + currencies[currency].label + '</a></li>');
          }
        }
      }

      this.$element.val(value);
    },

    displayCurrency: function () {
      var value,
          flag;

      value = this.options.currency;

      if (this.options.flags === true) {
        if (BFHCurrenciesList[value].currencyflag) {
          flag = BFHCurrenciesList[value].currencyflag;
        } else {
          flag = value.substr(0,2);
        }
        this.$element.html('<i class="glyphicon bfh-flag-' + flag + '"></i> ' + BFHCurrenciesList[value].label);
      } else {
        this.$element.html(BFHCurrenciesList[value].label);
      }
    }

  };


  /* CURRENCY PLUGIN DEFINITION
   * ======================= */

  var old = $.fn.bfhcurrencies;

  $.fn.bfhcurrencies = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhcurrencies');
      options = typeof option === 'object' && option;

      if (!data) {
        $this.data('bfhcurrencies', (data = new BFHCurrencies(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhcurrencies.Constructor = BFHCurrencies;

  $.fn.bfhcurrencies.defaults = {
    currency: '',
    available: '',
    flags: false,
    blank: true
  };


  /* CURRENCY NO CONFLICT
   * ========================== */

  $.fn.bfhcurrencies.noConflict = function () {
    $.fn.bfhcurrencies = old;
    return this;
  };


  /* CURRENCY DATA-API
   * ============== */

  $(document).ready( function () {
    $('form select.bfh-currencies, span.bfh-currencies, div.bfh-currencies').each(function () {
      var $currencies;

      $currencies = $(this);

      if ($currencies.hasClass('bfh-selectbox')) {
        $currencies.bfhselectbox($currencies.data());
      }
      $currencies.bfhcurrencies($currencies.data());
    });
  });


}(window.jQuery);
