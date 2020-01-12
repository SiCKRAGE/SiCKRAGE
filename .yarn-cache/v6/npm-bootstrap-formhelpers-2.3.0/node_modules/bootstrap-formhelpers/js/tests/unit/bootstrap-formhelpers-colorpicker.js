$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-colorpicker');

  test('should provide no conflict', function () {
    var bfhcolorpicker;

    bfhcolorpicker = $.fn.bfhcolorpicker.noConflict();
    ok(!$.fn.bfhcolorpicker, 'bfhcolorpicker was set back to undefined (org value)');
    $.fn.bfhcolorpicker = bfhcolorpicker;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhcolorpicker, 'bfhcolorpicker method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhcolorpicker()[0] === el[0], 'same element returned');
  });
  
  test('should not open colorpicker if target is disabled', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker" disabled="disabled">' +
      '</div>',
      colorpicker = $(colorpickerHTML).bfhcolorpicker();
      
    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();

    ok(!colorpicker.hasClass('open'), 'open class added on click');
  });
  
  test('should not open colorpicker if target is disabled', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker disabled">' +
      '</div>',
      colorpicker = $(colorpickerHTML).bfhcolorpicker();
      
    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();

    ok(!colorpicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add class open to colorpicker if clicked', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).bfhcolorpicker();
      
    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();

    ok(colorpicker.hasClass('open'), 'open class added on click');
  });
  
  test('should add and remove class open to colorpicker if toggled', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture');
      
    colorpicker.bfhcolorpicker('toggle');
    ok(colorpicker.hasClass('open'), 'open class added on toggle');
    
    colorpicker.bfhcolorpicker('toggle');
    ok(!colorpicker.hasClass('open'), 'open class removed on toggle');
    
    colorpicker.remove();
  });
  
  test('should remove open class if body clicked', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture').bfhcolorpicker();
        
    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();
    
    ok(colorpicker.hasClass('open'), 'open class added on click');
    $('body').click();
    ok(!colorpicker.hasClass('open'), 'open class removed');
    
    colorpicker.remove();
  });
  
  test('should remove open class if body clicked, with multiple colorpickers', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>' +
      '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture'),
      first = colorpicker.first().bfhcolorpicker(),
      last = colorpicker.last().bfhcolorpicker();
      
    ok(colorpicker.length === 2, 'Should be two colorpickers');
      
    first.find('[data-toggle="bfh-colorpicker"]').click();
    ok(first.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    last.find('[data-toggle="bfh-colorpicker"]').click();
    ok(last.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    $('#qunit-fixture').html('');
  });
  
  test('should have name after init', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker" data-name="colorpicker1">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture').bfhcolorpicker({name: 'colorpicker1'});
      
    ok(colorpicker.find('input[type=text]').attr('name') === 'colorpicker1', 'name is colorpicker1');
    colorpicker.remove();
  });
  
  test('should have value after init', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker" data-color="#FF0000">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture').bfhcolorpicker({color: '#FF0000'});

    ok(colorpicker.val() === '#FF0000', 'value is #FF0000');
    ok(colorpicker.find('input[type=text]').val() === '#FF0000', 'value is #FF0000');
    ok(colorpicker.find('.bfh-colorpicker-icon').css('background-color') === 'rgb(255, 0, 0)', 'value is #FF0000');
    colorpicker.remove();
  });
  
  test('should fire show and hide event', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture').bfhcolorpicker();
        
    stop();

    colorpicker
      .bind('show.bfhcolorpicker', function () {
        ok(true, 'show was called');
      })
      .bind('hide.bfhcolorpicker', function () {
        ok(true, 'hide was called');
        start();
      });

    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();
    $(document.body).click();
    
    colorpicker.remove();
  });
  
  test('should fire shown and hidden event', function () {
    var colorpickerHTML = '<div class="bfh-colorpicker">' +
      '</div>',
      colorpicker = $(colorpickerHTML).appendTo('#qunit-fixture').bfhcolorpicker();
        
    stop();

    colorpicker
      .bind('shown.bfhcolorpicker', function () {
        ok(true, 'shown was called');
      })
      .bind('hidden.bfhcolorpicker', function () {
        ok(true, 'hidden was called');
        start();
      });

    colorpicker.find('[data-toggle="bfh-colorpicker"]').click();
    $(document.body).click();
    
    colorpicker.remove();
  });
  
});