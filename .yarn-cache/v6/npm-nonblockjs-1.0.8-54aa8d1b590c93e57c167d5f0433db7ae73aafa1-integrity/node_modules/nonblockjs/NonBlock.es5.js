;

(function () {
  /**
   * NonBlock.js
   *
   * Copyright (c) 2017-2018 Hunter Perrin
   *
   * @author Hunter Perrin <hperrin@gmail.com>
   */
  'use strict';

  function _toConsumableArray(arr) {
    if (Array.isArray(arr)) {
      for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) {
        arr2[i] = arr[i];
      }

      return arr2;
    } else {
      return Array.from(arr);
    }
  }

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError("Cannot call a class as a function");
    }
  }

  var _createClass = function () {
    function defineProperties(target, props) {
      for (var i = 0; i < props.length; i++) {
        var descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ("value" in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function (Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  }();

  (function (NonBlock) {
    window.NonBlockJs = {
      NonBlock: NonBlock
    };
    if (document.body) {
      window.NonBlockJs.nonBlock = new NonBlock(document.body);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        window.NonBlockJs.nonBlock = new NonBlock(document.body);
      });
    }
  })(function () {
    var NonBlock = function () {
      function NonBlock(root, mode) {
        _classCallCheck(this, NonBlock);

        this.root = root;

        // Detect if we can use "pointer-events".
        // Can't use document.documentElement.style because IE9/IE10 report true,
        // but only support it on SVG elements, not HTML elements.
        var windowStyle = window.getComputedStyle(document.body);
        this.pointerEventsSupport = windowStyle.pointerEvents && windowStyle.pointerEvents === 'auto';

        // Some useful regexes.
        this.regexOn = /^on/;
        this.regexMouseEvents = /^(dbl)?click$|^mouse(move|down|up|over|out|enter|leave)$|^contextmenu$/;
        this.regexUiEvents = /^(focus|blur|select|change|reset)$|^key(press|down|up)$/;
        this.regexHtmlEvents = /^(scroll|resize|(un)?load|abort|error)$/;
        // Whether to use event constructors.
        this.useEventConstructors = true;
        try {
          var e = new MouseEvent('click');
        } catch (e) {
          this.useEventConstructors = false;
        }

        // If mode is not provided, use PointerEvents, if it's supported.
        if (typeof mode === 'undefined') {
          this.mode = this.pointerEventsSupport ? 'PointerEvents' : 'EventForwarding';
        } else {
          this.mode = mode;
        }

        // Init the current mode.
        if (this['init' + this.mode]) {
          this['init' + this.mode]();
        }
      }

      _createClass(NonBlock, [{
        key: 'initPointerEvents',
        value: function initPointerEvents() {
          var _this = this;

          // Using pointer-events, we can just detect whether an element is being
          // hovered over. No event forwarding necessary.

          this.addCSS('.nonblock{transition:opacity .3s ease; pointer-events: none;}.nonblock:hover,.nonblock-hover{opacity:.1 !important;}');

          this.onmousemove = function (ev) {
            var nonblocks = document.querySelectorAll('.nonblock');

            var _iteratorNormalCompletion = true;
            var _didIteratorError = false;
            var _iteratorError = undefined;

            try {
              for (var _iterator = nonblocks[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                var nonblock = _step.value;

                var rect = nonblock.getBoundingClientRect();
                if (ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom) {
                  if (!nonblock.classList.contains('nonblock-hover')) {
                    nonblock.classList.add('nonblock-hover');
                    if (_this.isSimulateMouse(nonblock) && ev.isTrusted) {
                      _this.domEvent(nonblock, 'onmouseenter', ev, false);
                      _this.domEvent(nonblock, 'onmouseover', ev, true);
                    }
                  } else if (_this.isSimulateMouse(nonblock) && ev.isTrusted) {
                    _this.domEvent(nonblock, 'onmousemove', ev, true);
                  }
                } else {
                  if (nonblock.classList.contains('nonblock-hover')) {
                    if (_this.isSimulateMouse(nonblock) && ev.isTrusted) {
                      _this.domEvent(nonblock, 'onmouseout', ev, true);
                      _this.domEvent(nonblock, 'onmouseleave', ev, false);
                    }
                    nonblock.classList.remove('nonblock-hover');
                  }
                }
              }
            } catch (err) {
              _didIteratorError = true;
              _iteratorError = err;
            } finally {
              try {
                if (!_iteratorNormalCompletion && _iterator.return) {
                  _iterator.return();
                }
              } finally {
                if (_didIteratorError) {
                  throw _iteratorError;
                }
              }
            }
          };

          this.root.addEventListener('mousemove', this.onmousemove);
        }
      }, {
        key: 'initEventForwarding',
        value: function initEventForwarding() {
          var _this2 = this;

          // No pointer-events means we have to fall back to using event forwarding.

          this.addCSS('.nonblock{transition:opacity .3s ease;}\n.nonblock:hover{opacity:.1 !important;}\n.nonblock-hide{position:absolute !important;left:-10000000px !important;right:10000000px !important;}\n.nonblock-cursor-auto{cursor:auto !important;}\n.nonblock-cursor-default{cursor:default !important;}\n.nonblock-cursor-none{cursor:none !important;}\n.nonblock-cursor-context-menu{cursor:context-menu !important;}\n.nonblock-cursor-help{cursor:help !important;}\n.nonblock-cursor-pointer{cursor:pointer !important;}\n.nonblock-cursor-progress{cursor:progress !important;}\n.nonblock-cursor-wait{cursor:wait !important;}\n.nonblock-cursor-cell{cursor:cell !important;}\n.nonblock-cursor-crosshair{cursor:crosshair !important;}\n.nonblock-cursor-text{cursor:text !important;}\n.nonblock-cursor-vertical-text{cursor:vertical-text !important;}\n.nonblock-cursor-alias{cursor:alias !important;}\n.nonblock-cursor-copy{cursor:copy !important;}\n.nonblock-cursor-move{cursor:move !important;}\n.nonblock-cursor-no-drop{cursor:no-drop !important;}\n.nonblock-cursor-not-allowed{cursor:not-allowed !important;}\n.nonblock-cursor-all-scroll{cursor:all-scroll !important;}\n.nonblock-cursor-col-resize{cursor:col-resize !important;}\n.nonblock-cursor-row-resize{cursor:row-resize !important;}\n.nonblock-cursor-n-resize{cursor:n-resize !important;}\n.nonblock-cursor-e-resize{cursor:e-resize !important;}\n.nonblock-cursor-s-resize{cursor:s-resize !important;}\n.nonblock-cursor-w-resize{cursor:w-resize !important;}\n.nonblock-cursor-ne-resize{cursor:ne-resize !important;}\n.nonblock-cursor-nw-resize{cursor:nw-resize !important;}\n.nonblock-cursor-se-resize{cursor:se-resize !important;}\n.nonblock-cursor-sw-resize{cursor:sw-resize !important;}\n.nonblock-cursor-ew-resize{cursor:ew-resize !important;}\n.nonblock-cursor-ns-resize{cursor:ns-resize !important;}\n.nonblock-cursor-nesw-resize{cursor:nesw-resize !important;}\n.nonblock-cursor-nwse-resize{cursor:nwse-resize !important;}\n.nonblock-cursor-zoom-in{cursor:zoom-in !important;}\n.nonblock-cursor-zoom-out{cursor:zoom-out !important;}\n.nonblock-cursor-grab{cursor:grab !important;}\n.nonblock-cursor-grabbing{cursor:grabbing !important;}');

          // This keeps track of the last element the mouse was over, so
          // mouseleave, mouseenter, etc can be called.
          this.nonBlockLastElem = null;
          // These are used for selecting text under a nonblock element.
          this.isOverTextNode = false;
          this.selectingText = false;

          this.onmouseenter = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonBlockLastElem = false;
              if (!_this2.isPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.onmouseleave = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.remCursor(nonblock);
              _this2.nonBlockLastElem = null;
              _this2.selectingText = false;
              if (!_this2.isPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.onmouseover = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target)) && !_this2.isPropagating(nonblock)) {
              ev.stopPropagation();
            }
          };
          this.onmouseout = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target)) && !_this2.isPropagating(nonblock)) {
              ev.stopPropagation();
            }
          };
          this.onmousemove = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonblockPass(nonblock, ev, 'onmousemove');
              // If the user just clicks somewhere, we don't want to select text, so this
              // detects that the user moved their mouse.
              if (_this2.selectingText === null) {
                window.getSelection().removeAllRanges();
                _this2.selectingText = true;
              } else if (_this2.selectingText) {
                // Stop the default action, which would be selecting text.
                ev.preventDefault();
              }
              if (!_this2.isPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.onmousedown = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonblockPass(nonblock, ev, 'onmousedown');
              _this2.selectingText = null;
              if (!_this2.isFocusable(nonblock)) {
                // Stop the default action, which would focus the element.
                ev.preventDefault();
              }
              if (!_this2.isPropagating(nonblock) || !_this2.isActionPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.onmouseup = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonblockPass(nonblock, ev, 'onmouseup');
              if (_this2.selectingText === null) {
                window.getSelection().removeAllRanges();
              }
              _this2.selectingText = false;
              if (!_this2.isPropagating(nonblock) || !_this2.isActionPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.onclick = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonblockPass(nonblock, ev, 'onclick');
              if (!_this2.isPropagating(nonblock) || !_this2.isActionPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };
          this.ondblclick = function (ev) {
            var nonblock = void 0;
            if (ev.isTrusted && (nonblock = _this2.getNonBlocking(ev.target))) {
              _this2.nonblockPass(nonblock, ev, 'ondblclick');
              if (!_this2.isPropagating(nonblock) || !_this2.isActionPropagating(nonblock)) {
                ev.stopPropagation();
              }
            }
          };

          this.root.addEventListener('mouseenter', this.onmouseenter, true);
          this.root.addEventListener('mouseleave', this.onmouseleave, true);
          this.root.addEventListener('mouseover', this.onmouseover, true);
          this.root.addEventListener('mouseout', this.onmouseout, true);
          this.root.addEventListener('mousemove', this.onmousemove, true);
          this.root.addEventListener('mousedown', this.onmousedown, true);
          this.root.addEventListener('mouseup', this.onmouseup, true);
          this.root.addEventListener('click', this.onclick, true);
          this.root.addEventListener('dblclick', this.ondblclick, true);
        }
      }, {
        key: 'destroy',
        value: function destroy() {
          var _arr = ['mouseenter', 'mouseleave', 'mouseover', 'mouseout', 'mousemove', 'mousedown', 'mouseup', 'click', 'dblclick'];

          for (var _i = 0; _i < _arr.length; _i++) {
            var event = _arr[_i];
            if (this['on' + event]) {
              this.root.removeEventListener(event, this['on' + event], true);
              delete this['on' + event];
            }
          }
          this.styling.parentNode.removeChild(this.styling);
          delete this.styling;
        }
      }, {
        key: 'addCSS',
        value: function addCSS(css) {
          this.styling = document.createElement('style');
          this.styling.setAttribute('type', 'text/css');
          if (this.styling.styleSheet) {
            this.styling.styleSheet.cssText = css; // IE
          } else {
            this.styling.appendChild(document.createTextNode(css));
          }
          document.getElementsByTagName('head')[0].appendChild(this.styling);
        }
      }, {
        key: 'domEvent',
        value: function domEvent(elem, event, origEvent, bubbles) {
          var eventObject = void 0;
          event = event.toLowerCase();
          if (this.useEventConstructors) {
            // New browsers
            event = event.replace(this.regexOn, '');
            if (event.match(this.regexMouseEvents)) {
              eventObject = new MouseEvent(event, {
                screenX: origEvent.screenX,
                screenY: origEvent.screenY,
                clientX: origEvent.clientX,
                clientY: origEvent.clientY,
                ctrlKey: origEvent.ctrlKey,
                shiftKey: origEvent.shiftKey,
                altKey: origEvent.altKey,
                metaKey: origEvent.metaKey,
                button: origEvent.button,
                buttons: origEvent.buttons,
                relatedTarget: origEvent.relatedTarget,
                region: origEvent.region,

                detail: origEvent.detail,
                view: origEvent.view,

                bubbles: bubbles === undefined ? origEvent.bubbles : bubbles,
                cancelable: origEvent.cancelable,
                composed: origEvent.composed
              });
            } else if (event.match(this.regexUiEvents)) {
              eventObject = new UIEvent(event, {
                detail: origEvent.detail,
                view: origEvent.view,

                bubbles: bubbles === undefined ? origEvent.bubbles : bubbles,
                cancelable: origEvent.cancelable,
                composed: origEvent.composed
              });
            } else if (event.match(this.regexHtmlEvents)) {
              eventObject = new Event(event, {
                bubbles: bubbles === undefined ? origEvent.bubbles : bubbles,
                cancelable: origEvent.cancelable,
                composed: origEvent.composed
              });
            }
            if (!eventObject) {
              return;
            }
            elem.dispatchEvent(eventObject);
          } else if (document.createEvent && elem.dispatchEvent) {
            // Old method for FireFox, Opera, Safari, Chrome
            event = event.replace(this.regexOn, '');
            if (event.match(this.regexMouseEvents)) {
              // This allows the click event to fire on the notice. There is
              // probably a much better way to do it.
              elem.getBoundingClientRect();
              eventObject = document.createEvent("MouseEvents");
              eventObject.initMouseEvent(event, bubbles === undefined ? origEvent.bubbles : bubbles, origEvent.cancelable, origEvent.view, origEvent.detail, origEvent.screenX, origEvent.screenY, origEvent.clientX, origEvent.clientY, origEvent.ctrlKey, origEvent.altKey, origEvent.shiftKey, origEvent.metaKey, origEvent.button, origEvent.relatedTarget);
            } else if (event.match(this.regexUiEvents)) {
              eventObject = document.createEvent("UIEvents");
              eventObject.initUIEvent(event, bubbles === undefined ? origEvent.bubbles : bubbles, origEvent.cancelable, origEvent.view, origEvent.detail);
            } else if (event.match(this.regexHtmlEvents)) {
              eventObject = document.createEvent("HTMLEvents");
              eventObject.initEvent(event, bubbles === undefined ? origEvent.bubbles : bubbles, origEvent.cancelable);
            }
            if (!eventObject) {
              return;
            }
            elem.dispatchEvent(eventObject);
          } else {
            // Internet Explorer
            if (!event.match(this.regexOn)) {
              event = "on" + event;
            };
            eventObject = document.createEventObject(origEvent);
            elem.fireEvent(event, eventObject);
          }
        }
      }, {
        key: 'nonblockPass',
        value: function nonblockPass(elem, event, eventName) {
          elem.classList.add('nonblock-hide');
          var elBelow = document.elementFromPoint(event.clientX, event.clientY);
          if (this.nonBlockLastElem === false) {
            this.nonBlockLastElem = elBelow;
          }
          var range = void 0,
              textNode = void 0,
              whitespaceBefore = void 0,
              text = void 0,
              offset = void 0;
          if (document.caretPositionFromPoint) {
            range = document.caretPositionFromPoint(event.clientX, event.clientY);
            textNode = range ? range.offsetNode : null;
            offset = range ? range.offset : null;
          } else if (document.caretRangeFromPoint) {
            range = document.caretRangeFromPoint(event.clientX, event.clientY);
            textNode = range ? range.endContainer : null;
            offset = range ? range.endOffset : null;
          }
          if (range) {
            whitespaceBefore = range.startContainer.textContent.match(/^[\s\n]*/)[0];
            text = range.startContainer.textContent.replace(/[\s\n]+$/g, '');
          }

          elem.classList.remove('nonblock-hide');
          var cursorStyle = this.getCursor(elBelow);
          this.isOverTextNode = false;
          if (cursorStyle === 'auto' && elBelow.tagName === 'A') {
            cursorStyle = 'pointer';
          } else if (range && (!whitespaceBefore.length || offset > whitespaceBefore.length) && offset < text.length) {
            if (cursorStyle === 'auto') {
              cursorStyle = 'text';
            }
            this.isOverTextNode = true;
          }

          if (range && this.selectingText && offset > 0) {
            var selection = window.getSelection();
            var selectionRange = void 0;
            if (selection.rangeCount === 0) {
              this.selectingText = {
                originContainer: range.startContainer ? range.startContainer : textNode,
                originOffset: offset - 1
              };
              selectionRange = document.createRange();
              selection.addRange(selectionRange);
            } else {
              selectionRange = selection.getRangeAt(0);
            }

            if (textNode === this.selectingText.originContainer && offset < this.selectingText.originOffset || textNode.compareDocumentPosition(this.selectingText.originContainer) & Node.DOCUMENT_POSITION_FOLLOWING) {
              selectionRange.setEnd(this.selectingText.originContainer, this.selectingText.originOffset);
              selectionRange.setStart(textNode, offset);
            } else {
              selectionRange.setStart(this.selectingText.originContainer, this.selectingText.originOffset);
              selectionRange.setEnd(textNode, offset);
            }
          }

          this.setCursor(elem, cursorStyle !== 'auto' ? cursorStyle : 'default');
          // If the element changed, call mouseenter, mouseleave, etc.
          if (!this.nonBlockLastElem || this.nonBlockLastElem !== elBelow) {
            if (this.nonBlockLastElem) {
              var lastElem = this.nonBlockLastElem;
              if (!lastElem.contains(elBelow)) {
                this.domEvent(lastElem, 'mouseleave', event, false);
              }
              this.domEvent(lastElem, 'mouseout', event, true);
              if (!elBelow.contains(lastElem)) {
                this.domEvent(elBelow, 'mouseenter', event, false);
              }
            } else if (!elBelow.contains(elem)) {
              this.domEvent(elBelow, 'mouseenter', event, false);
            }
            this.domEvent(elBelow, 'mouseover', event, true);
          }

          // If the event is mousedown, then we need to focus the element.
          if (eventName === 'onmousedown') {
            document.activeElement && document.activeElement.blur();
            elBelow.focus({ preventScroll: true });
          }

          // Forward the event.
          this.domEvent(elBelow, eventName, event);
          // Remember the latest element the mouse was over.
          this.nonBlockLastElem = elBelow;
        }
      }, {
        key: 'getNonBlocking',
        value: function getNonBlocking(el) {
          var nonblock = el;
          while (nonblock) {
            if (nonblock.classList && nonblock.classList.contains('nonblock')) {
              return nonblock;
            }
            nonblock = nonblock.parentNode;
          }
          return false;
        }
      }, {
        key: 'isPropagating',
        value: function isPropagating(el) {
          return !el.classList.contains('nonblock-stop-propagation');
        }
      }, {
        key: 'isActionPropagating',
        value: function isActionPropagating(el) {
          return el.classList.contains('nonblock-allow-action-propagation');
        }
      }, {
        key: 'isFocusable',
        value: function isFocusable(el) {
          return el.classList.contains('nonblock-allow-focus');
        }
      }, {
        key: 'isSimulateMouse',
        value: function isSimulateMouse(el) {
          return !el.classList.contains('nonblock-stop-mouse-simulation');
        }
      }, {
        key: 'getCursor',
        value: function getCursor(el) {
          var style = window.getComputedStyle(el);
          return style.getPropertyValue('cursor');
        }
      }, {
        key: 'setCursor',
        value: function setCursor(el, value) {
          if (el.classList.contains('nonblock-cursor-' + value)) {
            return;
          }
          this.remCursor(el);
          el.classList.add('nonblock-cursor-' + value);
        }
      }, {
        key: 'remCursor',
        value: function remCursor(el) {
          var values = Object.keys(el.classList).map(function (e) {
            return el.classList[e];
          });
          [].concat(_toConsumableArray(values)).forEach(function (className) {
            if (className.indexOf('nonblock-cursor-') === 0) {
              el.classList.remove(className);
            }
          });
        }
      }]);

      return NonBlock;
    }();

    return NonBlock;
  }());
})();
