# obj-extend

When called, this module simply sets all of the properties of each source
object onto the destination object (the first argument). Every property with
the same name is overridden in the order in which they were passed.

## Installation

``` bash
$ npm install obj-extend
```

## Usage

``` javascript
var extend = require('obj-extend');

var Person = function (name) {
  this.name = name;
};

Person.prototype = extend(events.EventEmitter.prototype, {

  emitName: function () {
    this.emit('name', this.name);
  }

});
```
