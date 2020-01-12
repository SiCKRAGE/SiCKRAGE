/**
 * Bridget tests
 */

/* jshint browser: true, undef: true, unused: true */
/* globals jQueryBridget: false, QUnit: false */

( function( window, $ ) {

'use strict';

// -------------------------- tests -------------------------- //

  $.bridget( 'niceGreeter', window.NiceGreeter );

  QUnit.test( 'niceGreeter on dummy element', function( assert ) {
    assert.ok( $.fn.niceGreeter, 'plugin added to jQuery namespace, $.fn.niceGreeter' );
    var $div = $('<div />');
    assert.ok( $div.niceGreeter, '.niceGreeter method is there' );
    $div.niceGreeter();
    assert.equal( typeof $div.data('niceGreeter'), 'object', 'instance accessible in .data()' );
  });

  QUnit.test( 'niceGreeter', function( assert ) {
    var $ex1 = $('#ex1');
    $ex1.niceGreeter();
    var greeter = $ex1.data('niceGreeter');
    assert.equal( typeof $ex1.data('niceGreeter'), 'object', 'instance accessible in .data()' );
    assert.equal( $ex1.text(), 'hello world', 'default settings' );
    // method with argument
    $ex1.niceGreeter( 'sayHi', 'pretty boy' );
    assert.equal( $ex1.text(), 'hello pretty boy', 'sayHi method with argument' );
    // option setter
    var ret = $ex1.niceGreeter( 'option', { greeting: 'bonjour' });
    assert.equal( ret, $ex1, 'return value of method is jQuery object' );
    ret.niceGreeter();
    assert.equal( greeter.options.greeting, 'bonjour', 'greeter.options.greeting = bonjour' );
    assert.equal( $ex1.text(), 'bonjour world', 'option setter' );
    // method
    $ex1.niceGreeter({ loudGreeting: 'well hi there' });
    $ex1.niceGreeter('shout');
    assert.equal( $ex1.text(), 'WELL HI THERE WORLD', 'shout method with argument' );
    // private method _whisper
    $ex1.niceGreeter( '_whisper', 'sweet nothings' );
    assert.notEqual( $ex1.text(), 'sweet nothings', 'private method _whisper is private' );

    // set second instance
    var $ex2 = $('#ex2').niceGreeter({
      greeting: 'aloha',
      recipient: 'uncle'
    });
    var greeter2 = $ex2.data('niceGreeter');
    var $examples = $('.example');
    // method on multiple instances
    $examples.niceGreeter( 'option', {
      loudGreeting: 'yaaarg'
    });
    assert.equal( greeter.options.loudGreeting, 'yaaarg', 'first greeter method worked' );
    assert.equal( greeter2.options.loudGreeting, 'yaaarg', 'second greeter method worked' );
    // getter method
    var message = $examples.niceGreeter('getMessage');
    assert.equal( message, 'bonjour world', 'getter method returns first value' );
  });


  QUnit.test( 'jQueryBridget', function( assert ) {
    jQueryBridget( 'noopPlugin', function() {} );
    assert.ok( $.fn.noopPlugin, 'jQueryBridget()' );
  });

})( window, window.jQuery );
