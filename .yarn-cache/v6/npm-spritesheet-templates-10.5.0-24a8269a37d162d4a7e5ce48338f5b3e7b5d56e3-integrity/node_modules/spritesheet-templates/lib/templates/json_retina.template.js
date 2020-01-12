function jsonRetinaTemplate(data) {
  // Convert retina groups from an array into an object
  var retinaGroups = data.retina_groups;
  var retinaGroupObj = {};
  retinaGroups.forEach(function (retinaGroup) {
    // Grab the name and store the retina group under it
    var name = retinaGroup.name;
    retinaGroupObj[name] = retinaGroup;

    // Delete the names and indicies from the retinaGroup
    delete retinaGroup.name;
    delete retinaGroup.index;
    delete retinaGroup.normal.name;
    delete retinaGroup.retina.name;
  });

  // Stringify the retinaGroupObj
  var retStr = JSON.stringify(retinaGroupObj, null, 4);

  // Return the stringified JSON
  return retStr;
}

// Export our JSON template
module.exports = jsonRetinaTemplate;
