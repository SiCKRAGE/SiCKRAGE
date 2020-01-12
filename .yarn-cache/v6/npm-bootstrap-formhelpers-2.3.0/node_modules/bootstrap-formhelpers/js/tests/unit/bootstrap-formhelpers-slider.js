$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-slider');

  test('should provide no conflict', function () {
    var bfhslider;

    bfhslider = $.fn.bfhslider.noConflict();
    ok(!$.fn.bfhslider, 'bfhslider was set back to undefined (org value)');
    $.fn.bfhslider = bfhslider;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhslider, 'bfhslider method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhslider()[0] === el[0], 'same element returned');
  });
  
  test('should have name after init', function () {
    var sliderHTML = '<div class="bfh-slider" data-name="slider1">' +
      '</div>',
      slider = $(sliderHTML).appendTo('#qunit-fixture').bfhslider({name: 'slider1'});
      
    ok(slider.find('input[type=hidden]').attr('name') === 'slider1', 'name is slider1');
    slider.remove();
  });
  
  test('should have value after init', function () {
    var sliderHTML = '<div class="bfh-slider" data-value="2">' +
      '</div>',
      slider = $(sliderHTML).appendTo('#qunit-fixture').bfhslider({value: '2'});
    
    ok(slider.val() === '2', 'value is 2');
    ok(slider.find('.bfh-slider-value').text() === '2', 'value is 2');
    ok(slider.find('input[type=hidden]').val() === '2', 'value is 2');
    slider.remove();
  });
  
  test('should have value after init with min', function () {
    var sliderHTML = '<div class="bfh-slider" data-min="2">' +
      '</div>',
      slider = $(sliderHTML).appendTo('#qunit-fixture').bfhslider({min: '2'});
    
    ok(slider.val() === '2', 'value is 2');
    ok(slider.find('.bfh-slider-value').text() === '2', 'value is 2');
    ok(slider.find('input[type=hidden]').val() === '2', 'value is 2');
    slider.remove();
  });

});