$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-timezones');
  
  test('should provide no conflict', function () {
    var bfhtimezones;

    bfhtimezones = $.fn.bfhtimezones.noConflict();
    ok(!$.fn.bfhtimezones, 'bfhtimezones was set back to undefined (org value)');
    $.fn.bfhtimezones = bfhtimezones;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhtimezones, 'bfhtimezones method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhtimezones()[0] === el[0], 'same element returned');
  });
  
  test('should fill select with a list of timezones', function() {
    var timezonesHTML = '<select class="bfh-timezones" data-country="US"></select>',
      timezones = $(timezonesHTML).bfhtimezones({country: 'US'});

    ok(timezones.find('option').size() === 31, 'correct number of elements shown');
    ok(timezones.find('option:selected').text() === '', 'correct option selected');
    ok(timezones.val() === '', 'correct element value');
    ok(timezones.find('option[value="America/New_York"]').text() === 'New York', 'valid timezone shown');
  });
  
  test('should fill select with a list of timezones with preselected timezone', function() {
    var timezonesHTML = '<select class="bfh-timezones" data-country="US" data-timezone="America/New_York"></select>',
      timezones = $(timezonesHTML).bfhtimezones({country: 'US', timezone: 'America/New_York'});

    ok(timezones.find('option').size() === 31, 'correct number of elements shown');
    ok(timezones.find('option:selected').text() === 'New York', 'correct option selected');
    ok(timezones.val() === 'America/New_York', 'correct element value');
    ok(timezones.find('option[value="America/New_York"]').text() === 'New York', 'valid timezone shown');
  });
  
  test('should fill select with a list of timezones without a blank option', function() {
    var timezonesHTML = '<select class="bfh-timezones" data-country="US" data-timezone="America/New_York" data-blank="false"></select>',
      timezones = $(timezonesHTML).bfhtimezones({country: 'US', timezone: 'America/New_York', blank: false});

    ok(timezones.find('option').size() === 30, 'correct number of elements shown');
    ok(timezones.find('option:selected').text() === 'New York', 'correct option selected');
    ok(timezones.val() === 'America/New_York', 'correct element value');
    ok(timezones.find('option[value="America/New_York"]').text() === 'New York', 'valid timezone shown');
  });
  
  test('should fill select with a list of timezones and work with bfhcountries', function() {
    var timezonesHTML = '<select id="countries" class="bfh-countries" data-country="US"></select>' +
      '<select class="bfh-timezones" data-country="countries"></select>',
      timezones = $(timezonesHTML).appendTo('#qunit-fixture'),
      first = timezones.first().bfhcountries({country: 'US'}),
      last = timezones.last().bfhtimezones({country: 'countries'});
      
    ok(last.find('option').size() === 31, 'correct number of elements shown');
    ok(last.find('option:selected').text() === '', 'correct option selected');
    ok(last.val() === '', 'correct element value');
    ok(last.find('option[value="America/New_York"]').text() === 'New York', 'valid timezone shown');
    
    first.val('CA').change();
    
    ok(last.find('option').size() === 29, 'correct number of elements shown');
    ok(last.find('option:selected').text() === '', 'correct option selected');
    ok(last.val() === '', 'correct element value');
    ok(last.find('option[value="America/Toronto"]').text() === 'Toronto', 'valid timezone shown');
    
    $('#qunit-fixture').html('');
  });
  
  test('should fill bfhselectbox with a list of timezones', function() {
    var timezonesHTML = '<div class="bfh-selectbox bfh-timezones" data-country="US">' +
      '</div>',
      timezones = $(timezonesHTML).bfhselectbox().bfhtimezones({country: 'US'});

    ok(timezones.find('.bfh-selectbox-options > div > ul > li').size() === 31, 'correct number of elements shown');
    ok(timezones.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(timezones.val() === '', 'correct element value');
    ok(timezones.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/New_York"]').html() === 'New York', 'valid timezone shown');
  });
  
  test('should fill bfhselectbox with a list of timezones with preselected timezone', function() {
    var timezonesHTML = '<div class="bfh-selectbox bfh-timezones" data-country="US" data-timezone="America/New_York">' +
      '</div>',
      timezones = $(timezonesHTML).bfhselectbox().bfhtimezones({country: 'US', timezone: 'America/New_York'});

    ok(timezones.find('.bfh-selectbox-options > div > ul > li').size() === 31, 'correct number of elements shown');
    ok(timezones.find('.bfh-selectbox-option').html() === 'New York', 'correct option selected');
    ok(timezones.val() === 'America/New_York', 'correct element value');
    ok(timezones.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/New_York"]').html() === 'New York', 'valid timezone shown');
  });
  
  test('should fill bfhselectbox with a list of timezones without a blank option', function() {
    var timezonesHTML = '<div class="bfh-selectbox bfh-timezones" data-country="US" data-timezone="America/New_York" data-blank="false">' +
      '</div>',
      timezones = $(timezonesHTML).bfhselectbox().bfhtimezones({country: 'US', timezone: 'America/New_York', blank: false});

    ok(timezones.find('.bfh-selectbox-options > div > ul > li').size() === 30, 'correct number of elements shown');
    ok(timezones.find('.bfh-selectbox-option').html() === 'New York', 'correct option selected');
    ok(timezones.val() === 'America/New_York', 'correct element value');
    ok(timezones.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/New_York"]').html() === 'New York', 'valid timezone shown');
  });
  
  test('should fill bfhselectbox with a list of timezones and work with bfhcountries', function() {
    var timezonesHTML = '<div id="countries" class="bfh-selectbox bfh-countries" data-country="US">' +
      '</div>' +
      '<div class="bfh-selectbox bfh-timezones" data-country="countries"' +
      '</div>',
      timezones = $(timezonesHTML).appendTo('#qunit-fixture'),
      first = timezones.first().bfhselectbox().bfhcountries({country: 'US'}),
      last = timezones.last().bfhselectbox().bfhtimezones({country: 'countries'});
    
    ok(last.find('.bfh-selectbox-options > div > ul > li').size() === 31, 'correct number of elements shown');
    ok(last.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(last.val() === '', 'correct element value');
    ok(last.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/New_York"]').html() === 'New York', 'valid timezone shown');
    
    first.val('CA').change();
    
    ok(last.find('.bfh-selectbox-options > div > ul > li').size() === 29, 'correct number of elements shown');
    ok(last.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(last.val() === '', 'correct element value');
    ok(last.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/Toronto"]').html() === 'Toronto', 'valid timezone shown');
    
    $('#qunit-fixture').html('');
  });
  
  test('in bfhselectbox should have value after selecting a timezone', function() {
    var timezonesHTML = '<div class="bfh-selectbox bfh-timezones" data-country="US">' +
      '</div>',
      timezones = $(timezonesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhtimezones({country: 'US'});
      
    timezones.find('.bfh-selectbox-options > div > ul > li > a[data-option="America/New_York"]').click();
    ok(timezones.find('.bfh-selectbox-option').html() === 'New York', 'correct option selected');
    ok(timezones.val() === 'America/New_York', 'correct element value');
    
    timezones.remove();
  });
  
});