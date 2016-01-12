$(document).ready(function(){
    $( "#tabs" ).tabs({
        collapsible: true,
        selected: (metaToBool('sickrage.SORT_ARTICLE') ? -1 : 0)
    });
});
