$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-fonts');

  test('should provide no conflict', function () {
    var bfhfonts;

    bfhfonts = $.fn.bfhfonts.noConflict();
    ok(!$.fn.bfhfonts, 'bfhfonts was set back to undefined (org value)');
    $.fn.bfhfonts = bfhfonts;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhfonts, 'bfhfonts method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhfonts()[0] === el[0], 'same element returned');
  });
  
  test('should fill select with a list of fonts', function() {
    var fontsHTML = '<select class="bfh-fonts"></select>',
      fonts = $(fontsHTML).bfhfonts();

    ok(fonts.find('option').size() === 47, 'correct number of elements shown');
    ok(fonts.find('option:selected').text() === '', 'correct option selected');
    ok(fonts.val() === '', 'correct element value');
    ok(fonts.find('option[value="Arial"]').text() === 'Arial', 'valid font shown');
  });
  
  test('should fill select with a list of fonts with preselected font', function() {
    var fontsHTML = '<select class="bfh-fonts" data-font="Arial"></select>',
      fonts = $(fontsHTML).bfhfonts({font: 'Arial'});
      
    ok(fonts.find('option').size() === 47, 'correct number of elements shown');
    ok(fonts.find('option:selected').text() === 'Arial', 'correct option selected');
    ok(fonts.val() === 'Arial', 'correct element value');
    ok(fonts.find('option[value="Arial"]').text() === 'Arial', 'valid font shown');
  });
  
  test('should fill select with predefined list of fonts', function() {
    var fontsHTML = '<select class="bfh-fonts" data-available="Arial,Calibri,Helvetica"></select>',
      fonts = $(fontsHTML).bfhfonts({available: 'Arial,Calibri,Helvetica'});
      
    ok(fonts.find('option').size() === 4, 'correct number of elements shown');
    ok(fonts.find('option:selected').text() === '', 'correct option selected');
    ok(fonts.val() === '', 'correct element value');
    ok(fonts.find('option[value="Arial"]').text() === 'Arial', 'valid font shown');
  });
  
  test('should fill select with a list of fonts without a blank option', function() {
    var fontsHTML = '<select class="bfh-fonts" data-font="Arial" data-blank="false"></select>',
      fonts = $(fontsHTML).bfhfonts({font: 'Arial', blank: false});

    ok(fonts.find('option').size() === 46, 'correct number of elements shown');
    ok(fonts.find('option:selected').text() === 'Arial', 'correct option selected');
    ok(fonts.val() === 'Arial', 'correct element value');
    ok(fonts.find('option[value="Arial"]').text() === 'Arial', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts', function() {
    var fontsHTML = '<div class="bfh-selectbox bfh-fonts">' +
      '</div>',
      fonts = $(fontsHTML).bfhselectbox().bfhfonts();

    ok(fonts.find('.bfh-selectbox-options > div > ul > li').size() === 47, 'correct number of elements shown');
    ok(fonts.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(fonts.val() === '', 'correct element value');
    ok(fonts.find('.bfh-selectbox-options > div > ul > li > a[data-option="Arial"]').html() === 'Arial', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts with preselected font', function() {
    var fontsHTML = '<div class="bfh-selectbox bfh-fonts" data-font="Arial">' +
      '</div>',
      fonts = $(fontsHTML).bfhselectbox().bfhfonts({font: 'Arial'});
      
    ok(fonts.find('.bfh-selectbox-options > div > ul > li').size() === 47, 'correct number of elements shown');
    ok(fonts.find('.bfh-selectbox-option').html() === 'Arial', 'correct option selected');
    ok(fonts.val() === 'Arial', 'correct element value');
    ok(fonts.find('.bfh-selectbox-options > div > ul > li > a[data-option="Arial"]').html() === 'Arial', 'valid font shown');
  });
  
  test('should fill bfhselectbox with predefined list of fonts', function() {
    var fontsHTML = '<div class="bfh-selectbox bfh-fonts" data-available="Arial,Calibri,Helvetica">' +
      '</div>',
      fonts = $(fontsHTML).bfhselectbox().bfhfonts({available: 'Arial,Calibri,Helvetica'});
      
    ok(fonts.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(fonts.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(fonts.val() === '', 'correct element value');
    ok(fonts.find('.bfh-selectbox-options > div > ul > li > a[data-option="Arial"]').html() === 'Arial', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts without a blank option', function() {
    var fontsHTML = '<div class="bfh-selectbox bfh-fonts" data-font="Arial" data-blank="false">' +
      '</div>',
      fonts = $(fontsHTML).bfhselectbox().bfhfonts({font: 'Arial', blank: false});

    ok(fonts.find('.bfh-selectbox-options > div > ul > li').size() === 46, 'correct number of elements shown');
    ok(fonts.find('.bfh-selectbox-option').html() === 'Arial', 'correct option selected');
    ok(fonts.val() === 'Arial', 'correct element value');
    ok(fonts.find('.bfh-selectbox-options > div > ul > li > a[data-option="Arial"]').html() === 'Arial', 'valid font shown');
  });
  
  test('in bfhselectbox should have value after selecting a font', function() {
    var fontsHTML = '<div class="bfh-selectbox bfh-fonts">' +
      '</div>',
      fonts = $(fontsHTML).appendTo('#qunit-fixture').bfhselectbox().bfhfonts();
      
    fonts.find('.bfh-selectbox-options > div > ul > li > a[data-option="Arial"]').click();
    ok(fonts.find('.bfh-selectbox-option').html() === 'Arial', 'correct option selected');
    ok(fonts.val() === 'Arial', 'correct element value');
    
    fonts.remove();
  });

});