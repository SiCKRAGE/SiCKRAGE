$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-fontsizes');

  test('should provide no conflict', function () {
    var bfhfontsizes;

    bfhfontsizes = $.fn.bfhfontsizes.noConflict();
    ok(!$.fn.bfhfontsizes, 'bfhfontsizes was set back to undefined (org value)');
    $.fn.bfhfontsizes = bfhfontsizes;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhfontsizes, 'bfhfontsizes method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhfontsizes()[0] === el[0], 'same element returned');
  });
  
  test('should fill select with a list of fonts', function() {
    var fontsizesHTML = '<select class="bfh-fontsizes"></select>',
      fontsizes = $(fontsizesHTML).bfhfontsizes();

    ok(fontsizes.find('option').size() === 14, 'correct number of elements shown');
    ok(fontsizes.find('option:selected').text() === '', 'correct option selected');
    ok(fontsizes.val() === '', 'correct element value');
    ok(fontsizes.find('option[value="12"]').text() === '12px', 'valid font shown');
  });
  
  test('should fill select with a list of fonts with preselected font', function() {
    var fontsizesHTML = '<select class="bfh-fontsizes" data-fontsize="12"></select>',
      fontsizes = $(fontsizesHTML).bfhfontsizes({fontsize: '12'});
      
    ok(fontsizes.find('option').size() === 14, 'correct number of elements shown');
    ok(fontsizes.find('option:selected').text() === '12px', 'correct option selected');
    ok(fontsizes.val() === '12', 'correct element value');
    ok(fontsizes.find('option[value="12"]').text() === '12px', 'valid font shown');
  });
  
  test('should fill select with predefined list of fonts', function() {
    var fontsizesHTML = '<select class="bfh-fontsizes" data-available="12,14,16"></select>',
      fontsizes = $(fontsizesHTML).bfhfontsizes({available: '12,14,16'});
      
    ok(fontsizes.find('option').size() === 4, 'correct number of elements shown');
    ok(fontsizes.find('option:selected').text() === '', 'correct option selected');
    ok(fontsizes.val() === '', 'correct element value');
    ok(fontsizes.find('option[value="12"]').text() === '12px', 'valid font shown');
  });
  
  test('should fill select with a list of fonts without a blank option', function() {
    var fontsizesHTML = '<select class="bfh-fontsizes" data-fontsize="12" data-blank="false"></select>',
      fontsizes = $(fontsizesHTML).bfhfontsizes({fontsize: '12', blank: false});

    ok(fontsizes.find('option').size() === 13, 'correct number of elements shown');
    ok(fontsizes.find('option:selected').text() === '12px', 'correct option selected');
    ok(fontsizes.val() === '12', 'correct element value');
    ok(fontsizes.find('option[value="12"]').text() === '12px', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts', function() {
    var fontsizesHTML = '<div class="bfh-selectbox bfh-fontsizes">' +
      '</div>',
      fontsizes = $(fontsizesHTML).bfhselectbox().bfhfontsizes();

    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li').size() === 14, 'correct number of elements shown');
    ok(fontsizes.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(fontsizes.val() === '', 'correct element value');
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li > a[data-option="12"]').html() === '12px', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts with preselected font', function() {
    var fontsizesHTML = '<div class="bfh-selectbox bfh-fontsizes" data-fontsize="12">' +
      '</div>',
      fontsizes = $(fontsizesHTML).bfhselectbox().bfhfontsizes({fontsize: '12'});
      
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li').size() === 14, 'correct number of elements shown');
    ok(fontsizes.find('.bfh-selectbox-option').html() === '12px', 'correct option selected');
    ok(fontsizes.val() === '12', 'correct element value');
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li > a[data-option="12"]').html() === '12px', 'valid font shown');
  });
  
  test('should fill bfhselectbox with predefined list of fonts', function() {
    var fontsizesHTML = '<div class="bfh-selectbox bfh-fontsizes" data-available="12,14,16">' +
      '</div>',
      fontsizes = $(fontsizesHTML).bfhselectbox().bfhfontsizes({available: '12,14,16'});
      
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(fontsizes.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(fontsizes.val() === '', 'correct element value');
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li > a[data-option="12"]').html() === '12px', 'valid font shown');
  });
  
  test('should fill bfhselectbox with a list of fonts without a blank option', function() {
    var fontsizesHTML = '<div class="bfh-selectbox bfh-fontsizes" data-fontsize="12" data-blank="false">' +
      '</div>',
      fontsizes = $(fontsizesHTML).bfhselectbox().bfhfontsizes({fontsize: '12', blank: false});

    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li').size() === 13, 'correct number of elements shown');
    ok(fontsizes.find('.bfh-selectbox-option').html() === '12px', 'correct option selected');
    ok(fontsizes.val() === '12', 'correct element value');
    ok(fontsizes.find('.bfh-selectbox-options > div > ul > li > a[data-option="12"]').html() === '12px', 'valid font shown');
  });
  
  test('in bfhselectbox should have value after selecting a font', function() {
    var fontsizesHTML = '<div class="bfh-selectbox bfh-fontsizes">' +
      '</div>',
      fontsizes = $(fontsizesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhfontsizes();
      
    fontsizes.find('.bfh-selectbox-options > div > ul > li > a[data-option="12"]').click();
    ok(fontsizes.find('.bfh-selectbox-option').html() === '12px', 'correct option selected');
    ok(fontsizes.val() === '12', 'correct element value');
    
    fontsizes.remove();
  });

});