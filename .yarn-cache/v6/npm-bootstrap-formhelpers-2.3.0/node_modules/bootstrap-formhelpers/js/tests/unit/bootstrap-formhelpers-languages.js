$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-languages');

  test('should provide no conflict', function () {
    var bfhlanguages;

    bfhlanguages = $.fn.bfhlanguages.noConflict();
    ok(!$.fn.bfhlanguages, 'bfhlanguages was set back to undefined (org value)');
    $.fn.bfhlanguages = bfhlanguages;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhlanguages, 'bfhlanguages method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhlanguages()[0] === el[0], 'same element returned');
  });
  
  test('should display language name', function() {
    var languagesHTML = '<span class="bfh-languages" data-language="en"></span>',
      languages = $(languagesHTML).bfhlanguages({language: 'en'});

    ok(languages.html() === 'English', 'language name displayed');
  });
  
  test('should display language name with country name', function() {
    var languagesHTML = '<span class="bfh-languages" data-language="en_US"></span>',
      languages = $(languagesHTML).bfhlanguages({language: 'en_US'});

    ok(languages.html() === 'English (United States)', 'language name displayed with country name');
  });
  
  test('should display language name with flag', function() {
    var languagesHTML = '<span class="bfh-languages" data-language="en_US" data-flags="true"></span>',
      languages = $(languagesHTML).bfhlanguages({language: 'en_US', flags: true});

    ok(languages.html() === '<i class="glyphicon bfh-flag-US"></i> English', 'language name displayed with flag');
  });
  
  test('should fill select with a list of languages', function() {
    var languagesHTML = '<select class="bfh-languages"></select>',
      languages = $(languagesHTML).bfhlanguages();

    ok(languages.find('option').size() === 184, 'correct number of elements shown');
    ok(languages.find('option:selected').text() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('option[value="en"]').text() === 'English', 'valid language shown');
  });
  
  test('should fill select with a list of languages with preselected language', function() {
    var languagesHTML = '<select class="bfh-languages" data-language="en"></select>',
      languages = $(languagesHTML).bfhlanguages({language: 'en'});
      
    ok(languages.find('option').size() === 184, 'correct number of elements shown');
    ok(languages.find('option:selected').text() === 'English', 'correct option selected');
    ok(languages.val() === 'en', 'correct element value');
    ok(languages.find('option[value="en"]').text() === 'English', 'valid language shown');
  });
  
  test('should fill select with predefined list of languages', function() {
    var languagesHTML = '<select class="bfh-languages" data-available="en,fr,es"></select>',
      languages = $(languagesHTML).bfhlanguages({available: 'en,fr,es'});
      
    ok(languages.find('option').size() === 4, 'correct number of elements shown');
    ok(languages.find('option:selected').text() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('option[value="en"]').text() === 'English', 'valid language shown');
  });
  
  test('should fill select with predefined list of languages and countries', function() {
    var languagesHTML = '<select class="bfh-languages" data-available="en_US,fr_CA,es_MX"></select>',
      languages = $(languagesHTML).bfhlanguages({available: 'en_US,fr_CA,es_MX'});
      
    ok(languages.find('option').size() === 4, 'correct number of elements shown');
    ok(languages.find('option:selected').text() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('option[value="en_US"]').text() === 'English (United States)', 'valid language shown');
  });
  
  test('should fill select with a list of languages without a blank option', function() {
    var languagesHTML = '<select class="bfh-languages" data-language="en" data-blank="false"></select>',
      languages = $(languagesHTML).bfhlanguages({language: 'en', blank: false});

    ok(languages.find('option').size() === 183, 'correct number of elements shown');
    ok(languages.find('option:selected').text() === 'English', 'correct option selected');
    ok(languages.val() === 'en', 'correct element value');
    ok(languages.find('option[value="en"]').text() === 'English', 'valid language shown');
  });
  
  test('should fill bfhselectbox with a list of languages', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages();

    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 184, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en"]').html() === 'English', 'valid language shown');
  });
  
  test('should fill bfhselectbox with a list of languages with preselected language', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-language="en">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages({language: 'en'});
      
    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 184, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === 'English', 'correct option selected');
    ok(languages.val() === 'en', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en"]').html() === 'English', 'valid language shown');
  });
  
  test('should fill bfhselectbox with predefined list of languages', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-available="en,fr,es">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages({available: 'en,fr,es'});
      
    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en"]').html() === 'English', 'valid language shown');
  });
  
  test('should fill bfhselectbox with predefined list of languages with country', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-available="en_US,fr_CA,es_MX">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages({available: 'en_US,fr_CA,es_MX'});

    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === '', 'correct option selected');
    ok(languages.val() === '', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en_US"]').html() === 'English (United States)', 'valid language shown');
  });
  
  test('should fill bfhselectbox with predefined list of languages with flags', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-language="en_US" data-available="en_US,fr_CA,es_MX" data-flags="true">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages({language: 'en_US', available: 'en_US,fr_CA,es_MX', flags: true});

    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 4, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === '<i class="glyphicon bfh-flag-US"></i>English', 'correct option selected');
    ok(languages.val() === 'en_US', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en_US"]').html() === '<i class="glyphicon bfh-flag-US"></i>English', 'valid language shown');
  });
  
  test('should fill bfhselectbox with a list of languages without a blank option', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-language="en" data-blank="false">' +
      '</div>',
      languages = $(languagesHTML).bfhselectbox().bfhlanguages({language: 'en', blank: false});

    ok(languages.find('.bfh-selectbox-options > div > ul > li').size() === 183, 'correct number of elements shown');
    ok(languages.find('.bfh-selectbox-option').html() === 'English', 'correct option selected');
    ok(languages.val() === 'en', 'correct element value');
    ok(languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en"]').html() === 'English', 'valid language shown');
  });
  
  test('in bfhselectbox should have value after selecting a language', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages">' +
      '</div>',
      languages = $(languagesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhlanguages();
      
    languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en"]').click();
    ok(languages.find('.bfh-selectbox-option').html() === 'English', 'correct option selected');
    ok(languages.val() === 'en', 'correct element value');
    
    languages.remove();
  });
  
  test('in bfhselectbox should have value after selecting a language with country', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-available="en_US,fr_CA,es_MX">' +
      '</div>',
      languages = $(languagesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhlanguages({available: 'en_US,fr_CA,es_MX'});
      
    languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en_US"]').click();
    ok(languages.find('.bfh-selectbox-option').html() === 'English (United States)', 'correct option selected');
    ok(languages.val() === 'en_US', 'correct element value');
    
    languages.remove();
  });
  
  test('in bfhselectbox should have value after selecting a language with flags', function() {
    var languagesHTML = '<div class="bfh-selectbox bfh-languages" data-available="en_US,fr_CA,es_MX" data-flags="true">' +
      '</div>',
      languages = $(languagesHTML).appendTo('#qunit-fixture').bfhselectbox().bfhlanguages({available: 'en_US,fr_CA,es_MX', flags: true});
      
    languages.find('.bfh-selectbox-options > div > ul > li > a[data-option="en_US"]').click();
    ok(languages.find('.bfh-selectbox-option').html() === '<i class="glyphicon bfh-flag-US"></i>English', 'correct option selected');
    ok(languages.val() === 'en_US', 'correct element value');
    
    languages.remove();
  });

});