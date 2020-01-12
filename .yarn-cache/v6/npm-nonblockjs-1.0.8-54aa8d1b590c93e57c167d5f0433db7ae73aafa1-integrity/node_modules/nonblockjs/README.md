# NonBlock.js

Unobtrusive (click through) UI elements in JavaScript.

NonBlock.js lets you provide unobstrusive UI elements. They will fade when a user hovers over them, and let the user click, select, and interact with elements under them.

## Demos

https://sciactive.github.io/nonblockjs/

## Installation

### Install via NPM with:

```sh
npm install --save nonblockjs
```

```html
<script src="node_modules/nonblockjs/NonBlock.es5.js" type="text/javascript"></script>
```

### Or use jsDelivr:

```html
<script src="https://cdn.jsdelivr.net/npm/nonblockjs@1/NonBlock.es5.js" type="text/javascript"></script>
```

## Usage

Add the class `nonblock` to any element you want to make nonblocking.

## How Does it Work?

There are two modes that NonBlock.js can use, "PointerEvents" and "EventForwarding".

* "PointerEvents" is used for newer browsers, and allows *all* features of below elements to work.
* "EventForwarding" is used for browsers that don't support the CSS "pointer-events" property (IE9 and IE10), and allows *most* features of below elements to work.

NonBlock.js detects whether the browser supports "pointer-events" and selects the mode automatically. If you want to force NonBlock.js into a specific mode, like "EventForwarding", you can do this:

```js
window.NonBlockJs.nonBlock.destroy();
window.NonBlockJs.nonBlock = new window.NonBlockJs.NonBlock(document.body, "EventForwarding");
```

### PointerEvents Mode

Nonblocking elements are given the `pointer-events: none;` style, so that the cursor does not interact with them. NonBlock.js will listen to `mousemove` events on the document body and will detect when the cursor passes over a nonblocking element. It applies the `nonblock-hover` class to fade the element.

#### Mouse Events in PointerEvents Mode

Normally, an element with the `pointer-events: none;` style will not receive any events related to mouse movement/interaction. In order to let you listen for these events, NonBlock.js will fire simulated `mouseover`, `mouseenter`, `mousemove`, `mouseout`, and `mouseleave` events on the nonblocking element. You can add the class `nonblock-stop-mouse-simulation` to prevent this behavior. (It is worth noting that only the element with `nonblock` receives these events. None of its children receive any events.)

### EventForwarding Mode

Nonblocking elements have a `:hover` pseudoclass applied to them that will fade them. NonBlock.js will listen for mouse events on document.body and detect when a mouse event is fired on a nonblocking element. It will detect what element is below the nonblocking element and forward the event to that element. It will detect the cursor that applies to that element and apply the same cursor to the nonblocking element. It also watches mousedown and mousemove and attempts to allow the user to select text.

All of this means that *most* features of the below elements will work in EventForwarding mode, with the notable exception of `:hover` styles, since those cannot be programmatically activated.

#### Event Propagation and Default Actions in EventForwarding Mode

By default in EventForwarding mode, NonBlock.js will propagate mouse events that are unrelated to clicking the mouse. It will also stop the default action of mousedown events, preventing nonblocking elements from being focused with the mouse (which allows elements underneath to gain focus).

Add the class `nonblock-allow-focus` to keep NonBlock.js from preventing the default action of mousedown events.

Add the class `nonblock-stop-propagation` if you want NonBlock.js to stop event propagation for all mouse events, effectively disguising it from its ancestors.

Add the class `nonblock-allow-action-propagation` if you want NonBlock.js to allow event propagation for action events (related to clicking the mouse). This may cause components that are designed to open on mouse clicks (like dropdown menus) to detect the click on the nonblocking element and mistakenly assume the user has clicked elsewhere and make the component inaccessible (close the menu).

## Author

NonBlock.js was written by Hunter Perrin as part of [PNotify](https://github.com/sciactive/pnotify).
