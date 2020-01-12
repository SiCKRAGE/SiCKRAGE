"use strict";

module.exports = function (obj) {
  // Get all the source objects to merge
  var sources = Array.prototype.slice.call(arguments, 1);

  // Loop over the source objects and set all of their properties onto the
  // destination object, overriding properties with the same name
  sources.forEach(function (source) {
    var prop;
    for (prop in source) {
      if (source.hasOwnProperty(prop)) {
        obj[prop] = source[prop];
      }
    }
  });

  // Return the extended object
  return obj;
};
