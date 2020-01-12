$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-phone');

  test('should provide no conflict', function () {
    var bfhphone;

    bfhphone = $.fn.bfhphone.noConflict();
    ok(!$.fn.bfhphone, 'bfhphone was set back to undefined (org value)');
    $.fn.bfhphone = bfhphone;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhphone, 'bfhphone method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhphone()[0] === el[0], 'same element returned');
  });
  
  test('should display formatted phone number', function() {
    var phoneHTML = '<span class="bfh-phone" data-format="+1 (ddd) ddd-dddd" data-number="5555555555"></span>',
      phone = $(phoneHTML).bfhphone({format: '+1 (ddd) ddd-dddd', number: '5555555555'});

    ok(phone.html() === '+1 (555) 555-5555', 'phone number is correctly formatted');
  });
  
  test('should display formatted phone number from a country', function() {
    var phoneHTML = '<span class="bfh-phone" data-country="US" data-number="5555555555"></span>',
      phone = $(phoneHTML).bfhphone({country: 'US', number: '5555555555'});

    ok(phone.html() === '+1 (555) 555-5555', 'phone number is correctly formatted');
  });
  
  test('should display input with formatted phone number', function() {
    var phoneHTML = '<input type="text" class="bfh-phone" data-format="+1 (ddd) ddd-dddd">',
      phone = $(phoneHTML).bfhphone({format: '+1 (ddd) ddd-dddd'});

    ok(phone.val() === '+1 ', 'phone number is correctly formatted');
  });
  
  test('should display input with formatted phone number with predefined number', function() {
    var phoneHTML = '<input type="text" class="bfh-phone" value="5555555555" data-format="+1 (ddd) ddd-dddd">',
      phone = $(phoneHTML).bfhphone({format: '+1 (ddd) ddd-dddd'});

    ok(phone.val() === '+1 (555) 555-5555', 'phone number is correctly formatted');
  });
  
  test('should display input with formatted phone number from a country', function() {
    var phoneHTML = '<input type="text" class="bfh-phone" value="5555555555" data-country="US">',
      phone = $(phoneHTML).bfhphone({country: 'US'});

    ok(phone.val() === '+1 (555) 555-5555', 'phone number is correctly formatted');
  });
  
  test('should display input with formatted phone number and work with bfhcountries', function() {
    var phoneHTML = '<div id="countries" class="bfh-selectbox bfh-countries" data-country="US">' +
      '<input type="hidden" value="">' +
      '<a class="bfh-selectbox-toggle" role="button" data-toggle="bfh-selectbox" href="#">' +
      '<span class="bfh-selectbox-option bfh-selectbox-medium" data-option=""></span>' +
      '<b class="caret"></b>' +
      '</a>' +
      '<div class="bfh-selectbox-options">' +
      '<div role="listbox">' +
      '<ul role="option">' +
      '</ul>' +
      '</div>' +
      '</div>' +
      '</div>' +
      '<input type="text" class="bfh-phone" value="5555555555" data-country="countries">',
      phone = $(phoneHTML).appendTo('#qunit-fixture'),
      first = phone.first().bfhcountries({country: 'US'}),
      last = phone.last().bfhphone({country: 'countries'});
    
    ok(last.val() === '+1 (555) 555-5555', 'phone number is correctly formatted');
    
    first.val('GB').change();
    
    ok(last.val() === '+44 (555) 5555 555', 'phone number is correctly formatted');
    
    $('#qunit-fixture').html('');
  });
  
  test('in bfhphone should have formatted number after changing value', function() {
    var phoneHTML = '<input type="text" class="bfh-phone" data-format="+1 (ddd) ddd-dddd">',
      phone = $(phoneHTML).appendTo('#qunit-fixture').bfhphone({format: '+1 (ddd) ddd-dddd'});
      
    phone.val('5555555555').keyup();
    
    ok(phone.val() === '+1 (555) 555-5555', 'phone number is correctly formatted');
    
    phone.remove();
  });
  
});