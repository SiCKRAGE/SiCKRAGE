$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-currencies');

  test('should provide no conflict', function () {
    var bfhcurrencies;

    bfhcurrencies = $.fn.bfhcurrencies.noConflict();
    ok(!$.fn.bfhcurrencies, 'bfhcurrencies was set back to undefined (org value)');
    $.fn.bfhcurrencies = bfhcurrencies;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhcurrencies, 'bfhcurrencies method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhcurrencies()[0] === el[0], 'same element returned');
  });
  
  test('should display currency name', function() {
    var currenciesHTML = '<span class="bfh-currencies" data-currency="USD"></span>',
      currencies = $(currenciesHTML).bfhcurrencies({currency: 'USD'});

    ok(currencies.html() === 'United States dollar', 'currency name displayed');
  });
  
  test('should display currency name with flag', function() {
    var currenciesHTML = '<span class="bfh-currencies" data-currency="USD" data-flags="true"></span>',
      currencies = $(currenciesHTML).bfhcurrencies({currency: 'USD', flags: true});

    ok(currencies.html() === '<i class="glyphicon bfh-flag-US"></i> United States dollar', 'currency name displayed with flag');
  });
  
  test('should fill select with a list of currencies', function() {
    var currenciesHTML = '<select class="bfh-currencies"></select>',
      currencies = $(currenciesHTML).bfhcurrencies();

    ok(currencies.find('option').size() === 160, 'correct number of elements shown');
    ok(currencies.find('option:selected').text() === '', 'correct option selected');
    ok(currencies.val() === '', 'correct element value');
    ok(currencies.find('option[value="USD"]').text() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill select with a list of currencies with preselected currency', function() {
    var currenciesHTML = '<select class="bfh-currencies" data-currency="USD"></select>',
      currencies = $(currenciesHTML).bfhcurrencies({currency: 'USD'});
      
    ok(currencies.find('option').size() === 160, 'correct number of elements shown');
    ok(currencies.find('option:selected').text() === 'United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    ok(currencies.find('option[value="USD"]').text() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill select with predefined list of currencies', function() {
    var currenciesHTML = '<select class="bfh-currencies" data-available="USD,CAD,EUR"></select>',
      currencies = $(currenciesHTML).bfhcurrencies({available: 'USD,CAD,EUR'});
      
    ok(currencies.find('option').size() === 4, 'correct number of elements shown');
    ok(currencies.find('option:selected').text() === '', 'correct option selected');
    ok(currencies.val() === '', 'correct element value');
    ok(currencies.find('option[value="USD"]').text() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill select with a list of currencies without a blank option', function() {
    var currenciesHTML = '<select class="bfh-currencies" data-currency="USD" data-blank="false"></select>',
      currencies = $(currenciesHTML).bfhcurrencies({currency: 'USD', blank: false});

    ok(currencies.find('option').size() === 159, 'correct number of elements shown');
    ok(currencies.find('option:selected').text() === 'United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    ok(currencies.find('option[value="USD"]').text() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill bfhselectbox with a list of currencies', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies">' +
      '</div>',
      currencies = $(currenciesHTML).bfhselectbox().bfhcurrencies();

    ok(currencies.find('.bfh-selectbox-options > div > ul > li').size() === 160, 'correct number of elements shown');
    ok(currencies.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(currencies.val() === '', 'correct element value');
    ok(currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').html() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill bfhselectbox with a list of currencies with preselected currency', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies" data-currency="USD">' +
      '</div>',
      currencies = $(currenciesHTML).bfhselectbox().bfhcurrencies({currency: 'USD'});
      
    ok(currencies.find('.bfh-selectbox-options > div > ul > li').size() === 160, 'correct number of elements shown');
    ok(currencies.find('.bfh-selectbox-option').html() === 'United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    ok(currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').html() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill bfhselectbox with predefined list of currencies', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies" data-available="USD,CAD,EUR">' +
      '</div>',
      currencies = $(currenciesHTML).bfhselectbox().bfhcurrencies({available: 'USD,CAD,EUR'});
      
    ok(currencies.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(currencies.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(currencies.val() === '', 'correct element value');
    ok(currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').html() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill bfhselectbox with a list of currencies without a blank option', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies" data-currency="USD" data-blank="false">' +
      '</div>',
      currencies = $(currenciesHTML).bfhselectbox().bfhcurrencies({currency: 'USD', blank: false});

    ok(currencies.find('.bfh-selectbox-options > div > ul > li').size() === 159, 'correct number of elements shown');
    ok(currencies.find('.bfh-selectbox-option').html() === 'United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    ok(currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').html() === 'United States dollar', 'valid currency shown');
  });
  
  test('should fill bfhselectbox with a list of currencies with flags', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies" data-currency="USD" data-flags="true">' +
      '</div>',
      currencies = $(currenciesHTML).bfhselectbox().bfhcurrencies({currency: 'USD', flags: true});

    ok(currencies.find('.bfh-selectbox-options > div > ul > li').size() === 160, 'correct number of elements shown');
    ok(currencies.find('.bfh-selectbox-option').html() === '<i class="glyphicon bfh-flag-US"></i>United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    ok(currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').html() === '<i class="glyphicon bfh-flag-US"></i>United States dollar', 'valid currency shown');
  });
  
  test('in bfhselectbox should have value after selecting a currency', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies">' +
      '</div>',
      currencies = $(currenciesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhcurrencies();
      
    currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').click();
    ok(currencies.find('.bfh-selectbox-option').html() === 'United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    
    currencies.remove();
  });
  
  test('in bfhselectbox should have value after selecting a currency with flags', function() {
    var currenciesHTML = '<div class="bfh-selectbox bfh-currencies" data-flags="true">' +
      '</div>',
      currencies = $(currenciesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhcurrencies({flags: true});
      
    currencies.find('.bfh-selectbox-options > div > ul > li > a[data-option="USD"]').click();
    ok(currencies.find('.bfh-selectbox-option').html() === '<i class="glyphicon bfh-flag-US"></i>United States dollar', 'correct option selected');
    ok(currencies.val() === 'USD', 'correct element value');
    
    currencies.remove();
  });

});