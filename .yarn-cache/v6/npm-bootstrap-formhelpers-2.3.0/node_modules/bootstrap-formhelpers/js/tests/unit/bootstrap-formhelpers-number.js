$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-number');

  test('should provide no conflict', function () {
    var bfhnumber;

    bfhnumber = $.fn.bfhnumber.noConflict();
    ok(!$.fn.bfhnumber, 'bfhnumber was set back to undefined (org value)');
    $.fn.bfhnumber = bfhnumber;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhnumber, 'bfhnumber method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhnumber()[0] === el[0], 'same element returned');
  });
  
  test('should show buttons', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    ok(number.parent().find('.inc').length === 1, 'increment button is shown');
    ok(number.parent().find('.dec').length === 1, 'decrement button is shown');
    
    number.remove();
  });
  
  test('should not show buttons', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-buttons="false">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({buttons: false});

    ok(number.parent().find('.inc').length === 0, 'increment button is not shown');
    ok(number.parent().find('.dec').length === 0, 'decrement button is not shown');
    
    number.remove();
  });
  
  test('should have initial value', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    ok(number.val() === '0', 'value is 0');
    
    number.remove();
  });
  
  test('should have initial value when min is set', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-min="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({min: 5});

    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should have leading zeros', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-min="5" data-max="25" data-zeros="true">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({min: 5, max: 25, zeros: true});

    ok(number.val() === '05', 'value is 05');
    
    number.remove();
  });
  
  test('should increment value on click increment button', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.inc').mousedown().mouseup();
    
    ok(number.val() === '6', 'value is 6');
    
    number.remove();
  });
  
  test('should not increment value when disabled', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number disabled" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.inc').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should not increment value when disabled', function() {
    var numberHTML = '<input disabled="disabled" type="text" class="form-control bfh-number" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.inc').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should decrement value on click decrement button', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.dec').mousedown().mouseup();
    
    ok(number.val() === '4', 'value is 4');
    
    number.remove();
  });
  
  test('should not decrement value when disabled', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number disabled" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.dec').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should not decrement value when disabled', function() {
    var numberHTML = '<input disabled="disabled" type="text" class="form-control bfh-number" value="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.dec').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should not increment value when max is reached', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" value="5" data-max="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({max: 5});

    number.parent().find('.inc').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should wrap value when max is reached', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" value="5" data-max="5" data-wrap="true">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({max: 5, wrap: true});

    number.parent().find('.inc').mousedown().mouseup();
    
    ok(number.val() === '0', 'value is 0');
    
    number.remove();
  });
  
  test('should not decrement value when min is reached', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.parent().find('.dec').mousedown().mouseup();
    ok(number.val() === '0', 'value is 0');
    
    number.remove();
  });
  
  test('should wrap value when min is reached', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-max="5" data-wrap="true">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({max: 5, wrap: true});

    number.parent().find('.dec').mousedown().mouseup();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should format value when changed', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.val('5').change();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should format value when changed', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-min="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({min: 5});

    number.val('2').change();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should format value when changed', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-max="5">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({max: 5});

    number.val('8').change();
    
    ok(number.val() === '5', 'value is 5');
    
    number.remove();
  });
  
  test('should format value when changed', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber();

    number.val('abgfbgfb').change();
    
    ok(number.val() === '0', 'value is 0');
    
    number.remove();
  });
  
  test('should format value when changed', function() {
    var numberHTML = '<input type="text" class="form-control bfh-number" data-max="25" data-zeros="true">',
      number = $(numberHTML).appendTo('#qunit-fixture').bfhnumber({max: 25, zeros: true});

    number.val('5').change();
    
    ok(number.val() === '05', 'value is 05');
    
    number.remove();
  });
  
});