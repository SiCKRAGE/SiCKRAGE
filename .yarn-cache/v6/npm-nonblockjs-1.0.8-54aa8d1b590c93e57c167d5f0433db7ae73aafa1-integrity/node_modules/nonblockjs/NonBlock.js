/**
 * NonBlock.js
 *
 * Copyright (c) 2017-2018 Hunter Perrin
 *
 * @author Hunter Perrin <hperrin@gmail.com>
 */
'use strict';

((NonBlock) => {
  window.NonBlockJs = {
    NonBlock
  };
  if (document.body) {
    window.NonBlockJs.nonBlock = new NonBlock(document.body);
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      window.NonBlockJs.nonBlock = new NonBlock(document.body);
    });
  }
})((() => {
  class NonBlock {
    constructor(root, mode) {
      this.root = root;

      // Detect if we can use "pointer-events".
      // Can't use document.documentElement.style because IE9/IE10 report true,
      // but only support it on SVG elements, not HTML elements.
      const windowStyle = window.getComputedStyle(document.body);
      this.pointerEventsSupport = (windowStyle.pointerEvents && windowStyle.pointerEvents === 'auto');

      // Some useful regexes.
      this.regexOn = /^on/;
      this.regexMouseEvents = /^(dbl)?click$|^mouse(move|down|up|over|out|enter|leave)$|^contextmenu$/;
      this.regexUiEvents = /^(focus|blur|select|change|reset)$|^key(press|down|up)$/;
      this.regexHtmlEvents = /^(scroll|resize|(un)?load|abort|error)$/;
      // Whether to use event constructors.
      this.useEventConstructors = true;
      try {
        const e = new MouseEvent('click');
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
      if (this['init'+this.mode]) {
        this['init'+this.mode]();
      }
    }

    initPointerEvents() {
      // Using pointer-events, we can just detect whether an element is being
      // hovered over. No event forwarding necessary.

      this.addCSS(`.nonblock{transition:opacity .3s ease; pointer-events: none;}.nonblock:hover,.nonblock-hover{opacity:.1 !important;}`);

      this.onmousemove = (ev) => {
        const nonblocks = document.querySelectorAll('.nonblock');

        for (let nonblock of nonblocks) {
          const rect = nonblock.getBoundingClientRect();
          if (ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom) {
            if (!nonblock.classList.contains('nonblock-hover')) {
              nonblock.classList.add('nonblock-hover');
              if (this.isSimulateMouse(nonblock) && ev.isTrusted) {
                this.domEvent(nonblock, 'onmouseenter', ev, false);
                this.domEvent(nonblock, 'onmouseover', ev, true);
              }
            } else if (this.isSimulateMouse(nonblock) && ev.isTrusted) {
              this.domEvent(nonblock, 'onmousemove', ev, true);
            }
          } else {
            if (nonblock.classList.contains('nonblock-hover')) {
              if (this.isSimulateMouse(nonblock) && ev.isTrusted) {
                this.domEvent(nonblock, 'onmouseout', ev, true);
                this.domEvent(nonblock, 'onmouseleave', ev, false);
              }
              nonblock.classList.remove('nonblock-hover');
            }
          }
        }
      };

      this.root.addEventListener('mousemove', this.onmousemove);
    }

    initEventForwarding() {
      // No pointer-events means we have to fall back to using event forwarding.

      this.addCSS(`.nonblock{transition:opacity .3s ease;}
.nonblock:hover{opacity:.1 !important;}
.nonblock-hide{position:absolute !important;left:-10000000px !important;right:10000000px !important;}
.nonblock-cursor-auto{cursor:auto !important;}
.nonblock-cursor-default{cursor:default !important;}
.nonblock-cursor-none{cursor:none !important;}
.nonblock-cursor-context-menu{cursor:context-menu !important;}
.nonblock-cursor-help{cursor:help !important;}
.nonblock-cursor-pointer{cursor:pointer !important;}
.nonblock-cursor-progress{cursor:progress !important;}
.nonblock-cursor-wait{cursor:wait !important;}
.nonblock-cursor-cell{cursor:cell !important;}
.nonblock-cursor-crosshair{cursor:crosshair !important;}
.nonblock-cursor-text{cursor:text !important;}
.nonblock-cursor-vertical-text{cursor:vertical-text !important;}
.nonblock-cursor-alias{cursor:alias !important;}
.nonblock-cursor-copy{cursor:copy !important;}
.nonblock-cursor-move{cursor:move !important;}
.nonblock-cursor-no-drop{cursor:no-drop !important;}
.nonblock-cursor-not-allowed{cursor:not-allowed !important;}
.nonblock-cursor-all-scroll{cursor:all-scroll !important;}
.nonblock-cursor-col-resize{cursor:col-resize !important;}
.nonblock-cursor-row-resize{cursor:row-resize !important;}
.nonblock-cursor-n-resize{cursor:n-resize !important;}
.nonblock-cursor-e-resize{cursor:e-resize !important;}
.nonblock-cursor-s-resize{cursor:s-resize !important;}
.nonblock-cursor-w-resize{cursor:w-resize !important;}
.nonblock-cursor-ne-resize{cursor:ne-resize !important;}
.nonblock-cursor-nw-resize{cursor:nw-resize !important;}
.nonblock-cursor-se-resize{cursor:se-resize !important;}
.nonblock-cursor-sw-resize{cursor:sw-resize !important;}
.nonblock-cursor-ew-resize{cursor:ew-resize !important;}
.nonblock-cursor-ns-resize{cursor:ns-resize !important;}
.nonblock-cursor-nesw-resize{cursor:nesw-resize !important;}
.nonblock-cursor-nwse-resize{cursor:nwse-resize !important;}
.nonblock-cursor-zoom-in{cursor:zoom-in !important;}
.nonblock-cursor-zoom-out{cursor:zoom-out !important;}
.nonblock-cursor-grab{cursor:grab !important;}
.nonblock-cursor-grabbing{cursor:grabbing !important;}`);

      // This keeps track of the last element the mouse was over, so
      // mouseleave, mouseenter, etc can be called.
      this.nonBlockLastElem = null;
      // These are used for selecting text under a nonblock element.
      this.isOverTextNode = false;
      this.selectingText = false;

      this.onmouseenter = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonBlockLastElem = false;
          if (!this.isPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.onmouseleave = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.remCursor(nonblock);
          this.nonBlockLastElem = null;
          this.selectingText = false;
          if (!this.isPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.onmouseover = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target)) && !this.isPropagating(nonblock)) {
          ev.stopPropagation();
        }
      };
      this.onmouseout = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target)) && !this.isPropagating(nonblock)) {
          ev.stopPropagation();
        }
      };
      this.onmousemove = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonblockPass(nonblock, ev, 'onmousemove');
          // If the user just clicks somewhere, we don't want to select text, so this
          // detects that the user moved their mouse.
          if (this.selectingText === null) {
            window.getSelection().removeAllRanges();
            this.selectingText = true;
          } else if (this.selectingText) {
            // Stop the default action, which would be selecting text.
            ev.preventDefault();
          }
          if (!this.isPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.onmousedown = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonblockPass(nonblock, ev, 'onmousedown');
          this.selectingText = null;
          if (!this.isFocusable(nonblock)) {
            // Stop the default action, which would focus the element.
            ev.preventDefault();
          }
          if (!this.isPropagating(nonblock) || !this.isActionPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.onmouseup = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonblockPass(nonblock, ev, 'onmouseup');
          if (this.selectingText === null) {
            window.getSelection().removeAllRanges();
          }
          this.selectingText = false;
          if (!this.isPropagating(nonblock) || !this.isActionPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.onclick = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonblockPass(nonblock, ev, 'onclick');
          if (!this.isPropagating(nonblock) || !this.isActionPropagating(nonblock)) {
            ev.stopPropagation();
          }
        }
      };
      this.ondblclick = (ev) => {
        let nonblock;
        if (ev.isTrusted && (nonblock = this.getNonBlocking(ev.target))) {
          this.nonblockPass(nonblock, ev, 'ondblclick');
          if (!this.isPropagating(nonblock) || !this.isActionPropagating(nonblock)) {
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

    destroy() {
      for (let event of ['mouseenter', 'mouseleave', 'mouseover', 'mouseout', 'mousemove', 'mousedown', 'mouseup', 'click', 'dblclick']) {
        if (this['on'+event]) {
          this.root.removeEventListener(event, this['on'+event], true);
          delete this['on'+event];
        }
      }
      this.styling.parentNode.removeChild(this.styling);
      delete this.styling;
    }

    addCSS(css) {
      this.styling = document.createElement('style');
      this.styling.setAttribute('type', 'text/css');
      if (this.styling.styleSheet) {
        this.styling.styleSheet.cssText = css; // IE
      } else {
        this.styling.appendChild(document.createTextNode(css));
      }
      document.getElementsByTagName('head')[0].appendChild(this.styling);
    }

    // Fire a DOM event.
    domEvent(elem, event, origEvent, bubbles) {
      let eventObject;
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
          event = "on"+event
        };
        eventObject = document.createEventObject(origEvent);
        elem.fireEvent(event, eventObject);
      }
    }

    // This is used to pass events through the el if it is nonblocking.
    nonblockPass(elem, event, eventName) {
      elem.classList.add('nonblock-hide');
      const elBelow = document.elementFromPoint(event.clientX, event.clientY);
      if (this.nonBlockLastElem === false) {
        this.nonBlockLastElem = elBelow;
      }
      let range, textNode, whitespaceBefore, text, offset;
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
      let cursorStyle = this.getCursor(elBelow);
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
        const selection = window.getSelection();
        let selectionRange;
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

        if (
            (textNode === this.selectingText.originContainer && offset < this.selectingText.originOffset)
            || (textNode.compareDocumentPosition(this.selectingText.originContainer) & Node.DOCUMENT_POSITION_FOLLOWING)
          ) {
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
          const lastElem = this.nonBlockLastElem;
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
        elBelow.focus({preventScroll: true});
      }

      // Forward the event.
      this.domEvent(elBelow, eventName, event);
      // Remember the latest element the mouse was over.
      this.nonBlockLastElem = elBelow;
    }

    getNonBlocking(el) {
      let nonblock = el;
      while (nonblock) {
        if (nonblock.classList && nonblock.classList.contains('nonblock')) {
          return nonblock;
        }
        nonblock = nonblock.parentNode;
      }
      return false;
    }

    isPropagating(el) {
      return !el.classList.contains('nonblock-stop-propagation');
    }

    isActionPropagating(el) {
      return el.classList.contains('nonblock-allow-action-propagation');
    }

    isFocusable(el) {
      return el.classList.contains('nonblock-allow-focus');
    }

    isSimulateMouse(el) {
      return !el.classList.contains('nonblock-stop-mouse-simulation');
    }

    getCursor(el) {
      const style = window.getComputedStyle(el);
      return style.getPropertyValue('cursor');
    }

    setCursor(el, value) {
      if (el.classList.contains('nonblock-cursor-' + value)) {
        return;
      }
      this.remCursor(el);
      el.classList.add('nonblock-cursor-' + value);
    }

    remCursor(el) {
      const values = Object.keys(el.classList).map(e => el.classList[e]);
      [...values].forEach((className) => {
        if (className.indexOf('nonblock-cursor-') === 0) {
          el.classList.remove(className);
        }
      });
    }
  }

  return NonBlock;
})());
