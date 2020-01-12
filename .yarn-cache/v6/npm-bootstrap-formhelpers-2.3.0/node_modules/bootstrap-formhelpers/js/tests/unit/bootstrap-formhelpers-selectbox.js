$(function () {

  'use strict';
  
  module('bootstrap-formhelpers-select');

  test('should provide no conflict', function () {
    var bfhselectbox;

    bfhselectbox = $.fn.bfhselectbox.noConflict();
    ok(!$.fn.bfhselectbox, 'bfhselectbox was set back to undefined (org value)');
    $.fn.bfhselectbox = bfhselectbox;
  });

  test('should be defined on jquery object', function () {
    ok($(document.body).bfhselectbox, 'bfhselectbox method is defined');
  });

  test('should return element', function () {
    var el;
    
    el = $('<div />');
    ok(el.bfhselectbox()[0] === el[0], 'same element returned');
  });
  
  test('should not open select box if target is disabled', function () {
    var selectboxHTML = '<div class="bfh-selectbox" disabled="disabled">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).bfhselectbox();
      
    selectbox.find('[data-toggle="bfh-selectbox"]').click();

    ok(!selectbox.hasClass('open'), 'open class added on click');
  });
  
  test('should not open select box if target is disabled', function () {
    var selectboxHTML = '<div class="bfh-selectbox disabled">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).bfhselectbox();
      
    selectbox.find('[data-toggle="bfh-selectbox"]').click();

    ok(!selectbox.hasClass('open'), 'open class added on click');
  });
  
  test('should add class open to options if clicked', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).bfhselectbox();
      
    selectbox.find('[data-toggle="bfh-selectbox"]').click();
      
    ok(selectbox.hasClass('open'), 'open class added on click');
  });
  
  test('should add and remove class open to options if toggled', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture');
      
    selectbox.bfhselectbox('toggle');
    ok(selectbox.hasClass('open'), 'open class added on toggle');
    
    selectbox.bfhselectbox('toggle');
    ok(!selectbox.hasClass('open'), 'open class removed on toggle');
    
    selectbox.remove();
  });
  
  test('should remove open class if body clicked', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
        
    selectbox.find('[data-toggle="bfh-selectbox"]').click();
      
    ok(selectbox.hasClass('open'), 'open class added on click');
    $('body').click();
    ok(!selectbox.hasClass('open'), 'open class removed');
    selectbox.remove();
  });
  
  test('should display correct number of options', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).bfhselectbox();
    
    ok(selectbox.find('li > a').length === 4, 'correct number of options');
  });
  
  test('should remove open class if option selected', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
      
    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    
    ok(selectbox.hasClass('open'), 'open class added on click');
    selectbox.find('[data-option="1"]').click();
    ok(!selectbox.hasClass('open'), 'open class removed');
    selectbox.remove();
  });
  
  test('should remove open class if body clicked, with multiple select boxes', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>' +
      '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture'),
      first = selectbox.first().bfhselectbox(),
      last = selectbox.last().bfhselectbox();
      
    ok(selectbox.length === 2, 'Should be two select boxes');
      
    first.find('[data-toggle="bfh-selectbox"]').click();
    ok(first.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    last.find('[data-toggle="bfh-selectbox"]').click();
    ok(last.hasClass('open'), 'open class added on click');
    ok($('#qunit-fixture .open').length === 1, 'only one object is open');
    $('body').click();
    ok($('#qunit-fixture .open').length === 0, 'open class removed');

    $('#qunit-fixture').html('');
  });
  
  test('should have name after init', function () {
    var selectboxHTML = '<div class="bfh-selectbox" data-name="selectbox1">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox({name: 'selectbox1'});
      
    ok(selectbox.find('input[type=hidden]').attr('name') === 'selectbox1', 'name is selectbox1');
    selectbox.remove();
  });
  
  test('should have value after init', function () {
    var selectboxHTML = '<div class="bfh-selectbox" data-value="2">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox({value: '2'});
    
    ok(selectbox.val() === '2', 'value is 2');
    ok(selectbox.find('.bfh-selectbox-option').text() === 'Option 2', 'value is 2');
    ok(selectbox.find('input[type=hidden]').val() === '2', 'value is 2');
    selectbox.remove();
  });
  
  test('should have value after selecting an option', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
    
    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    
    selectbox.find('[data-option="2"]').click();
    
    ok(selectbox.val() === '2', 'value is 2');
    ok(selectbox.find('.bfh-selectbox-option').text() === 'Option 2', 'value is 2');
    ok(selectbox.find('input[type=hidden]').val() === '2', 'value is 2');
    selectbox.remove();
  });
  
  test('should filter elements', function () {
    var selectboxHTML = '<div class="bfh-selectbox" data-filter="true">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox({filter: true});
    
    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    
    ok(selectbox.find('.bfh-selectbox-filter').length === 1, 'filter is there');
    selectbox.find('.bfh-selectbox-filter').val('Option 1').change();
    ok(selectbox.find('[role="option"] > li > a:visible').length === 1, 'options are filtered');
    selectbox.remove();
  });
  
  test('should fire show and hide event', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
        
    stop();

    selectbox
      .bind('show.bfhselectbox', function () {
        ok(true, 'show was called');
      })
      .bind('hide.bfhselectbox', function () {
        ok(true, 'hide was called');
        start();
      });

    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    $(document.body).click();
    
    selectbox.remove();
  });
  
  test('should fire shown and hidden event', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
        
    stop();

    selectbox
      .bind('shown.bfhselectbox', function () {
        ok(true, 'shown was called');
      })
      .bind('hidden.bfhselectbox', function () {
        ok(true, 'hidden was called');
        start();
      });

    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    $(document.body).click();
    
    selectbox.remove();
  });
  
  test('should fire change event', function () {
    var selectboxHTML = '<div class="bfh-selectbox">' +
      '<div data-value="1">Option 1</div>' +
      '<div data-value="2">Option 2</div>' +
      '<div data-value="3">Option 3</div>' +
      '<div data-value="4">Option 4</div>' +
      '</div>',
      selectbox = $(selectboxHTML).appendTo('#qunit-fixture').bfhselectbox();
        
    stop();

    selectbox
      .bind('change.bfhselectbox', function () {
        ok(true, 'change was called');
        start();
      });

    selectbox.find('[data-toggle="bfh-selectbox"]').click();
    selectbox.find('[data-option="1"]').click();
    
    selectbox.remove();
  });

});