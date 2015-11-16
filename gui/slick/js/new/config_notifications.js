$(document).ready(function(){
    $('#config-components').tabs();

    $(".enabler").each(function () {
        if (!$(this).prop('checked')) { $('#content_' + $(this).attr('id')).hide(); }
    });

    $(".enabler").click(function () {
        if ($(this).prop('checked')) {
            $('#content_' + $(this).attr('id')).fadeIn("fast", "linear");
        } else {
            $('#content_' + $(this).attr('id')).fadeOut("fast", "linear");
        }
    });
});
