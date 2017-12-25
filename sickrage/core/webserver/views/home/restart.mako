<%!
    import sickrage
%>

<meta data-var="srWebRoot" data-content="${srWebRoot}">
<meta data-var="srDefaultPage" data-content="${srDefaultPage}">
<%block name="metas" />

<link rel="stylesheet" type="text/css" href="${srWebRoot}/css/bower.min.css"/>
<%block name="css" />

<%block name="content">
    <%
        try:
            themeSpinner = srThemeName
        except NameError:
            themeSpinner = sickrage.app.config.theme_name
    %>
    <div class="messages text-center">
        <h2>${_('Performing Restart')}</h2>
        <div id="shut_down_message">
            ${_('Waiting for SiCKRAGE to shut down:')}
            <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="shut_down_loading"/>
            <img src="${srWebRoot}/images/yes16.png" height="16" width="16" id="shut_down_success"
                 style="display: none;"/>
        </div>
        <div id="restart_message" style="display: none;">
            ${_('Waiting for SiCKRAGE to start again:')}
            <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="restart_loading"/>
            <img src="${srWebRoot}/images/yes16.png" height="16" width="16" id="restart_success"
                 style="display: none;"/>
            <img src="${srWebRoot}/images/no16.png" height="16" width="16" id="restart_failure" style="display: none;"/>
        </div>
        <div id="refresh_message" style="display: none;">
            ${_('Loading the default page:')}
            <img src="${srWebRoot}/images/loading16-${themeSpinner}.gif" height="16" width="16" id="refresh_loading"/>
        </div>
        <div id="restart_fail_message" style="display: none;">
            ${_('Error: The restart has timed out, perhaps something prevented SiCKRAGE from starting again?')}
        </div>
    </div>
</%block>

<script src="${srWebRoot}/js/bower.min.js"></script>
<script>
    var current_pid = '';
    var timeout_id;
    var num_restart_waits = 0;
    var srWebRoot = $('meta[data-var="srWebRoot"]').data('content');
    var srDefaultPage = $('meta[data-var="srDefaultPage"]').data('content');

    (function checkIsAlive() {
        timeout_id = 0;

        $.ajax({
            url: srWebRoot + '/home/is_alive/',
            dataType: 'jsonp',
            jsonp: 'srcallback',
            success: function (data) {
                if (data.msg === 'nope') {
                    $('#shut_down_loading').hide();
                    $('#shut_down_success').show();
                    $('#restart_message').show();
                    setTimeout(checkIsAlive, 1000);
                } else {
                    if (current_pid === '' || data.msg === current_pid) {
                        current_pid = data.msg;
                        setTimeout(checkIsAlive, 1000);
                    } else {
                        $('#restart_loading').hide();
                        $('#restart_success').show();
                        $('#restart_message').show();
                        window.location = srWebRoot + '/' + srDefaultPage + '/';
                    }
                }
            },
            error: function (error) {
                num_restart_waits += 1;

                $('#shut_down_loading').hide();
                $('#shut_down_success').show();
                $('#restart_message').show();

                // if it is taking forever just give up
                if (num_restart_waits > 90) {
                    $('#restart_loading').hide();
                    $('#restart_failure').show();
                    $('#restart_fail_message').show();
                    return;
                }

                if (timeout_id === 0) {
                    timeout_id = setTimeout(checkIsAlive, 1000);
                }
            }
        });
    })();
</script>
<%block name="scripts" />