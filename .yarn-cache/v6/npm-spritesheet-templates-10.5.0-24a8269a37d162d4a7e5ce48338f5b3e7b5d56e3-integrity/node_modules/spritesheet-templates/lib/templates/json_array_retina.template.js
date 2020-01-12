function jsonArrayTemplate(data) {
  // Clean up the retina group sprite names/indicies
  var retinaGroups = data.retina_groups;
  retinaGroups.forEach(function cleanRetinaGroup (retinaGroup) {
    delete retinaGroup.index;
    delete retinaGroup.normal.name;
    delete retinaGroup.retina.name;
  });

  // Stringify and return the groups
  var retStr = JSON.stringify(retinaGroups, null, 4);
  return retStr;
}

// Export our JSON template
module.exports = jsonArrayTemplate;
