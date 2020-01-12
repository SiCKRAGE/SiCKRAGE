$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-timepicker');

  test('should provide no conflict', function () {
    var bfhtimepicker;

    bfhtimepicker = $.fn.bfhtimepicker.noConflict();
    ok(!$.fn.bfhtimepicker, 'bfhtimepicker was set back to undefined (org value)');
    $.fn.bfhtimepicker = bfhtimepicker;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhtimepicker, 'bfhtimepicker method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhtimepicker()[0] === el[0], 'same element returned');
  });
  
  test('should not open timepicker if target is disabled', function () {
    var timepickerHTML = '<div class="bfh-timepicker" disabled="disabled">' +
      '</div>',
      timepicker = $(timepickerHTML).bfhtimepicker();
      
    timepicker.find('[data-toggle="bfh-timepicker"]').click();

    ok(!timepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should not open timepicker if target is disabled', function () {
    var timepickerHTML = '<div class="bfh-timepicker disabled">' +
      '</div>',
      timepicker = $(timepickerHTML).bfhtimepicker();
      
    timepicker.find('[data-toggle="bfh-timepicker"]').click();

    ok(!timepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add class open to timepicker if clicked', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).bfhtimepicker();
      
    timepicker.find('[data-toggle="bfh-timepicker"]').click();

    ok(timepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add and remove class open to timepicker if toggled', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture');
      
    timepicker.bfhtimepicker('toggle');
    ok(timepicker.hasClass('open'), 'open class added on toggle');
    
    timepicker.bfhtimepicker('toggle');
    ok(!timepicker.hasClass('open'), 'open class removed on toggle');
    
    timepicker.remove();
  });
  
  test('should remove open class if body clicked', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker();
        
    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    
    ok(timepicker.hasClass('open'), 'open class added on click');
    $('body').click();
    ok(!timepicker.hasClass('open'), 'open class removed');
    
    timepicker.remove();
  });
  
  test('should remove open class if body clicked, with multiple timepickers', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>' +
      '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture'),
      first = timepicker.first().bfhtimepicker(),
      last = timepicker.last().bfhtimepicker();
      
    ok(timepicker.length === 2, 'Should be two timepickers');
      
    first.find('[data-toggle="bfh-timepicker"]').click();
    ok(first.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    last.find('[data-toggle="bfh-timepicker"]').click();
    ok(last.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    $('#qunit-fixture').html('');
  });
  
  test('should have name after init', function () {
    var timepickerHTML = '<div class="bfh-timepicker" data-name="timepicker1">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({name: 'timepicker1'});
      
    ok(timepicker.find('.bfh-timepicker-toggle > input[type=text]').attr('name') === 'timepicker1', 'name is timepicker1');
    timepicker.remove();
  });
  
  test('should have value after init', function () {
    var timepickerHTML = '<div class="bfh-timepicker" data-time="10:05">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({time: '10:05'});
    
    ok(timepicker.val() === '10:05', 'value is 10:05');
    ok(timepicker.find('.bfh-timepicker-toggle > input[type=text]').val() === '10:05', 'value is 10:05');
    timepicker.remove();
  });
  
  test('should display previous hour', function() {
    var timepickerHTML = '<div class="bfh-timepicker" data-time="00:10">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({time: '00:10'});
    
    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    timepicker.find('.hour .dec').mousedown().mouseup();
    
    ok(timepicker.find('.hour input[type=text]').val() === '23', 'previous hour displayed');
    ok(timepicker.val() === '23:10', 'previous hour displayed');
    timepicker.remove();
  });
  
  test('should display next hour', function() {
    var timepickerHTML = '<div class="bfh-timepicker" data-time="23:10">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({time: '23:10'});
    
    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    timepicker.find('.hour .inc').mousedown().mouseup();
    
    ok(timepicker.find('.hour input[type=text]').val() === '00', 'next hour displayed');
    ok(timepicker.val() === '00:10', 'next hour displayed');
    timepicker.remove();
  });
  
  test('should display previous minute', function() {
    var timepickerHTML = '<div class="bfh-timepicker" data-time="05:00">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({time: '05:00'});
    
    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    timepicker.find('.minute .dec').mousedown().mouseup();
    
    ok(timepicker.find('.minute input[type=text]').val() === '59', 'previous minute displayed');
    ok(timepicker.val() === '05:59', 'previous minute displayed');
    timepicker.remove();
  });
  
  test('should display next minute', function() {
    var timepickerHTML = '<div class="bfh-timepicker" data-time="05:59">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker({time: '05:59'});
    
    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    timepicker.find('.minute .inc').mousedown().mouseup();
    
    ok(timepicker.find('.minute input[type=text]').val() === '00', 'next minute displayed');
    ok(timepicker.val() === '05:00', 'next minute displayed');
    timepicker.remove();
  });
  
  test('should fire show and hide event', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker();
        
    stop();

    timepicker
      .bind('show.bfhtimepicker', function () {
        ok(true, 'show was called');
      })
      .bind('hide.bfhtimepicker', function () {
        ok(true, 'hide was called');
        start();
      });

    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    $(document.body).click();
    
    timepicker.remove();
  });
  
  test('should fire shown and hidden event', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker();
        
    stop();

    timepicker
      .bind('shown.bfhtimepicker', function () {
        ok(true, 'shown was called');
      })
      .bind('hidden.bfhtimepicker', function () {
        ok(true, 'hidden was called');
        start();
      });

    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    $(document.body).click();
    
    timepicker.remove();
  });
  
  test('should fire change event', function () {
    var timepickerHTML = '<div class="bfh-timepicker">' +
      '</div>',
      timepicker = $(timepickerHTML).appendTo('#qunit-fixture').bfhtimepicker();
        
    stop();

    timepicker
      .bind('change.bfhtimepicker', function () {
        ok(true, 'change was called');
        start();
      });

    timepicker.find('[data-toggle="bfh-timepicker"]').click();
    timepicker.find('.minute .inc').mousedown().mouseup();
    
    timepicker.remove();
  });
  
});