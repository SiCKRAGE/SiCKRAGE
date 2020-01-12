$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-datepicker');

  test('should provide no conflict', function () {
    var bfhdatepicker;

    bfhdatepicker = $.fn.bfhdatepicker.noConflict();
    ok(!$.fn.bfhdatepicker, 'bfhdatepicker was set back to undefined (org value)');
    $.fn.bfhdatepicker = bfhdatepicker;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhdatepicker, 'bfhdatepicker method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhdatepicker()[0] === el[0], 'same element returned');
  });
  
  test('should not open datepicker if target is disabled', function () {
    var datepickerHTML = '<div class="bfh-datepicker" disabled="disabled">' +
      '</div>',
      datepicker = $(datepickerHTML).bfhdatepicker();
      
    datepicker.find('[data-toggle="bfh-datepicker"]').click();

    ok(!datepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should not open datepicker if target is disabled', function () {
    var datepickerHTML = '<div class="bfh-datepicker disabled">' +
      '</div>',
      datepicker = $(datepickerHTML).bfhdatepicker();
      
    datepicker.find('[data-toggle="bfh-datepicker"]').click();

    ok(!datepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add class open to datepicker if clicked', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).bfhdatepicker();
      
    datepicker.find('[data-toggle="bfh-datepicker"]').click();

    ok(datepicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add and remove class open to datepicker if toggled', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture');
      
    datepicker.bfhdatepicker('toggle');
    ok(datepicker.hasClass('open'), 'open class added on toggle');
    
    datepicker.bfhdatepicker('toggle');
    ok(!datepicker.hasClass('open'), 'open class removed on toggle');
    
    datepicker.remove();
  });
  
  test('should remove open class if body clicked', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker();
        
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    
    ok(datepicker.hasClass('open'), 'open class added on click');
    $('body').click();
    ok(!datepicker.hasClass('open'), 'open class removed');
    
    datepicker.remove();
  });
  
  test('should remove open class if date selected', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker();
      
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    
    ok(datepicker.hasClass('open'), 'open class added on click');
    datepicker.find('[data-day="1"]').click();
    ok(!datepicker.hasClass('open'), 'open class removed');
    datepicker.remove();
  });
  
  test('should not remove open class if date selected and close is false', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-close="false">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({close: false});
      
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    
    ok(datepicker.hasClass('open'), 'open class added on click');
    datepicker.find('[data-day="1"]').click();
    ok(datepicker.hasClass('open'), 'open class removed');
    datepicker.remove();
  });
  
  test('should remove open class if body clicked, with multiple datepickers', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>' +
      '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture'),
      first = datepicker.first().bfhdatepicker(),
      last = datepicker.last().bfhdatepicker();
      
    ok(datepicker.length === 2, 'Should be two datepickers');
      
    first.find('[data-toggle="bfh-datepicker"]').click();
    ok(first.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    last.find('[data-toggle="bfh-datepicker"]').click();
    ok(last.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    $('#qunit-fixture').html('');
  });
  
  test('should have name after init', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-name="datepicker1">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({name: 'datepicker1'});
      
    ok(datepicker.find('input[type=text]').attr('name') === 'datepicker1', 'name is datepicker1');
    datepicker.remove();
  });
  
  test('should have value after init', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="11/05/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '11/05/2013'});
    
    ok(datepicker.val() === '11/05/2013', 'value is 11/05/2013');
    ok(datepicker.find('input[type=text]').val() === '11/05/2013', 'value is 11/05/2013');
    datepicker.remove();
  });
  
  test('should have value after selecting an option', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="11/05/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '11/05/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('[data-day="1"]').click();
    
    ok(datepicker.val() === '11/01/2013', 'value is 11/01/2013');
    ok(datepicker.find('input[type=text]').val() === '11/01/2013', 'value is 11/01/2013');
    datepicker.remove();
  });
  
  test('should display right format', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="2013-11-05" data-format="y-m-d">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '2013-11-05', format: 'y-m-d'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('[data-day="1"]').click();
    
    ok(datepicker.val() === '2013-11-01', 'value has correct format');
    ok(datepicker.find('input[type=text]').val() === '2013-11-01', 'value has correct format');
    datepicker.remove();
  });
  
  test('should filter calendar based on min date', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="11/05/2013" data-min="11/04/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '11/05/2013', min: '11/04/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    ok(datepicker.find('[data-day="1"]').hasClass('off'), 'min date is disabled');
    datepicker.remove();
  });
  
  test('should filter calendar based on max date', function () {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="11/05/2013" data-max="11/06/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '11/05/2013', max: '11/06/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();

    ok(datepicker.find('[data-day="8"]').hasClass('off'), 'max date is disabled');
    datepicker.remove();
  });
  
  test('should display previous month', function() {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="01/01/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '01/01/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('.month .previous').click();
    
    ok(datepicker.find('.month span').text() === 'December', 'previous month displayed');
    datepicker.remove();
  });
  
  test('should display next month', function() {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="12/01/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '12/01/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('.month .next').click();
    
    ok(datepicker.find('.month span').text() === 'January', 'next month displayed');
    datepicker.remove();
  });
  
  test('should display previous year', function() {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="12/01/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '12/01/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('.year .previous').click();
    
    ok(datepicker.find('.year span').text() === '2012', 'previous year displayed');
    datepicker.remove();
  });
  
  test('should display next year', function() {
    var datepickerHTML = '<div class="bfh-datepicker" data-date="12/01/2013">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker({date: '12/01/2013'});
    
    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('.year .next').click();
    
    ok(datepicker.find('.year span').text() === '2014', 'next year displayed');
    datepicker.remove();
  });
  
  test('should fire show and hide event', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker();
        
    stop();

    datepicker
      .bind('show.bfhdatepicker', function () {
        ok(true, 'show was called');
      })
      .bind('hide.bfhdatepicker', function () {
        ok(true, 'hide was called');
        start();
      });

    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    $(document.body).click();
    
    datepicker.remove();
  });
  
  test('should fire shown and hidden event', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker();
        
    stop();

    datepicker
      .bind('shown.bfhdatepicker', function () {
        ok(true, 'shown was called');
      })
      .bind('hidden.bfhdatepicker', function () {
        ok(true, 'hidden was called');
        start();
      });

    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    $(document.body).click();
    
    datepicker.remove();
  });
  
  test('should fire change event', function () {
    var datepickerHTML = '<div class="bfh-datepicker">' +
      '</div>',
      datepicker = $(datepickerHTML).appendTo('#qunit-fixture').bfhdatepicker();
        
    stop();

    datepicker
      .bind('change.bfhdatepicker', function () {
        ok(true, 'change was called');
        start();
      });

    datepicker.find('[data-toggle="bfh-datepicker"]').click();
    datepicker.find('[data-day="1"]').click();
    
    datepicker.remove();
  });
  
});