/* ==========================================================
 * bootstrap-formhelpers-selectbox.js
 * https://github.com/vlamanna/BootstrapFormHelpers
 * ==========================================================
 * Copyright 2012 Vincent Lamanna
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

+function ($) {

  'use strict';


  /* SELECTBOX CLASS DEFINITION
   * ========================= */

  var toggle = '[data-toggle=bfh-selectbox]',
      BFHSelectBox = function (element, options) {
        this.options = $.extend({}, $.fn.bfhselectbox.defaults, options);
        this.$element = $(element);

        this.initSelectBox();
      };

  BFHSelectBox.prototype = {

    constructor: BFHSelectBox,

    initSelectBox: function () {
      var options;

      options = '';
      this.$element.find('div').each(function() {
        options = options + '<li><a tabindex="-1" href="#" data-option="' + $(this).data('value') + '">' + $(this).html() + '</a></li>';
      });

      this.$element.html(
        '<input type="hidden" name="' + this.options.name + '" value="">' +
		'<a class="bfh-selectbox-toggle ' + this.options.input + '" role="button" data-toggle="bfh-selectbox" href="#">' +
		'<span class="bfh-selectbox-option"></span>' +
		'<span class="' + this.options.icon + ' selectbox-caret"></span>' +
		'</a>' +
		'<div class="bfh-selectbox-options">' +
		'<div role="listbox">' +
		'<ul role="option">' +
		'</ul>' +
		'</div>' +
		'</div>'
      );

      this.$element.find('[role=option]').html(options);

      if (this.options.filter === true) {
        this.$element.find('.bfh-selectbox-options').prepend('<div class="bfh-selectbox-filter-container"><input type="text" class="bfh-selectbox-filter form-control"></div>');
      }

      this.$element.val(this.options.value);

      this.$element
        .on('click.bfhselectbox.data-api touchstart.bfhselectbox.data-api', toggle, BFHSelectBox.prototype.toggle)
		.on('keydown.bfhselectbox.data-api', toggle + ', [role=option]' , BFHSelectBox.prototype.keydown)
		.on('mouseenter.bfhselectbox.data-api', '[role=option] > li > a', BFHSelectBox.prototype.mouseenter)
		.on('click.bfhselectbox.data-api', '[role=option] > li > a', BFHSelectBox.prototype.select)
		.on('click.bfhselectbox.data-api', '.bfh-selectbox-filter', function () { return false; })
		.on('propertychange.bfhselectbox.data-api change.bfhselectbox.data-api input.bfhselectbox.data-api paste.bfhselectbox.data-api', '.bfh-selectbox-filter', BFHSelectBox.prototype.filter);
    },

    toggle: function (e) {
      var $this,
          $parent,
          isActive;

      $this = $(this);
      $parent = getParent($this);

      if ($parent.is('.disabled') || $parent.attr('disabled') !== undefined) {
        return true;
      }

      isActive = $parent.hasClass('open');

      clearMenus();

      if (!isActive) {
        $parent.trigger(e = $.Event('show.bfhselectbox'));

        if (e.isDefaultPrevented()) {
          return true;
        }

        $parent
          .toggleClass('open')
          .trigger('shown.bfhselectbox')
          .find('[role=option] > li > [data-option="' + $parent.val() + '"]').focus();
      }

      return false;
    },

    filter: function() {
      var $this,
          $parent,
          $items;

      $this = $(this);
      $parent = getParent($this);

      $items = $('[role=option] li a', $parent);
      $items
        .hide()
        .filter(function() {
          return ($(this).text().toUpperCase().indexOf($this.val().toUpperCase()) !== -1);
        })
        .show();
    },

    keydown: function (e) {
      var $this,
          $items,
          $parent,
          $subItems,
          isActive,
          index,
          selectedIndex;

      if (!/(38|40|27)/.test(e.keyCode)) {
        return true;
      }

      $this = $(this);

      e.preventDefault();
      e.stopPropagation();

      $parent = getParent($this);
      isActive = $parent.hasClass('open');

      if (!isActive || (isActive && e.keyCode === 27)) {
        if (e.which === 27) {
          $parent.find(toggle).focus();
        }

        return $this.click();
      }

      $items = $('[role=option] li:not(.divider) a:visible', $parent);

      if (!$items.length) {
        return true;
      }

      $('body').off('mouseenter.bfh-selectbox.data-api', '[role=option] > li > a', BFHSelectBox.prototype.mouseenter);
      index = $items.index($items.filter(':focus'));

      if (e.keyCode === 38 && index > 0) {
        index = index - 1;
      }

      if (e.keyCode === 40 && index < $items.length - 1) {
        index = index + 1;
      }

      if (!index) {
        index = 0;
      }

      $items.eq(index).focus();
      $('body').on('mouseenter.bfh-selectbox.data-api', '[role=option] > li > a', BFHSelectBox.prototype.mouseenter);
    },

    mouseenter: function () {
      var $this;

      $this = $(this);

      $this.focus();
    },

    select: function (e) {
      var $this,
          $parent,
          $span,
          $input;

      $this = $(this);

      e.preventDefault();
      e.stopPropagation();

      if ($this.is('.disabled') || $this.attr('disabled') !== undefined) {
        return true;
      }

      $parent = getParent($this);

      $parent.val($this.data('option'));
      $parent.trigger('change.bfhselectbox');

      clearMenus();
    }

  };

  function clearMenus() {
    var $parent;

    $(toggle).each(function (e) {
      $parent = getParent($(this));

      if (!$parent.hasClass('open')) {
        return true;
      }

      $parent.trigger(e = $.Event('hide.bfhselectbox'));

      if (e.isDefaultPrevented()) {
        return true;
      }

      $parent
        .removeClass('open')
        .trigger('hidden.bfhselectbox');
    });
  }

  function getParent($this) {
    return $this.closest('.bfh-selectbox');
  }


  /* SELECTBOX PLUGIN DEFINITION
   * ========================== */

  var old = $.fn.bfhselectbox;

  $.fn.bfhselectbox = function (option) {
    return this.each(function () {
      var $this,
          data,
          options;

      $this = $(this);
      data = $this.data('bfhselectbox');
      options = typeof option === 'object' && option;
      this.type = 'bfhselectbox';

      if (!data) {
        $this.data('bfhselectbox', (data = new BFHSelectBox(this, options)));
      }
      if (typeof option === 'string') {
        data[option].call($this);
      }
    });
  };

  $.fn.bfhselectbox.Constructor = BFHSelectBox;

  $.fn.bfhselectbox.defaults = {
    icon: 'caret',
    input: 'form-control',
    name: '',
    value: '',
    filter: false
  };


  /* SELECTBOX NO CONFLICT
   * ========================== */

  $.fn.bfhselectbox.noConflict = function () {
    $.fn.bfhselectbox = old;
    return this;
  };


  /* SELECTBOX VALHOOKS
   * ========================== */

  var origHook;
  if ($.valHooks.div){
    origHook = $.valHooks.div;
  }
  $.valHooks.div = {
    get: function(el) {
      if ($(el).hasClass('bfh-selectbox')) {
        return $(el).find('input[type="hidden"]').val();
      } else if (origHook) {
        return origHook.get(el);
      }
    },
    set: function(el, val) {
      var $el,
          html;

      if ($(el).hasClass('bfh-selectbox')) {

        $el = $(el);
        if ($el.find('li a[data-option=\'' + val + '\']').length > 0) {
          html = $el.find('li a[data-option=\'' + val + '\']').html();
        } else if ($el.find('li a').length > 0) {
          html = $el.find('li a').eq(0).html();
        } else {
          val = '';
          html = '';
        }

        $el.find('input[type="hidden"]').val(val);
        $el.find('.bfh-selectbox-option').html(html);
      } else if (origHook) {
        return origHook.set(el,val);
      }
    }
  };


  /* SELECTBOX DATA-API
   * ============== */

  $(document).ready( function () {
    $('div.bfh-selectbox').each(function () {
      var $selectbox;

      $selectbox = $(this);

      $selectbox.bfhselectbox($selectbox.data());
    });
  });


  /* APPLY TO STANDARD SELECTBOX ELEMENTS
   * =================================== */

  $(document)
    .on('click.bfhselectbox.data-api', clearMenus);

}(window.jQuery);
