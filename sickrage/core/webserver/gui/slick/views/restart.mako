<%!
    import sys
    import sickrage
%>
<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
    <%
        try:
            curSRHost = srHost
            curSRHttpPort = srHttpPort
            curSRHttpsEnabled = srHttpsEnabled
            curSRHandleReverseProxy = srHandleReverseProxy
            themeSpinner = srThemeName
        except NameError:
            curSRHost = "localhost"
            curSRHttpPort = sickrage.WEB_PORT
            curSRHttpsEnabled = "False"
            curSRHandleReverseProxy = "False"
            themeSpinner = sickrage.THEME_NAME
    %>
    <script type="text/javascript" charset="utf-8">
        srRoot = "${srRoot}";
        srHttpPort = "${curSRHttpPort}";
        srHttpsEnabled = "${curSRHttpsEnabled}";
        srHandleReverseProxy = "${curSRHandleReverseProxy}";
        srHost = "${curSRHost}";
        srDefaultPage = "${srDefaultPage}";
    </script>
    <script type="text/javascript" src="${srRoot}/js/lib/jquery-1.11.2.min.js?${srPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/restart.js?${srPID}&amp;${srDefaultPage}"></script>
</%block>
<%block name="css">
    <style>
        .upgrade-notification {
            display: none;
        }
    </style>
</%block>
<%block name="content">
    <%
        try:
            curSRHost = srHost
            curSRHttpPort = srHttpPort
            curSRHttpsEnabled = srHttpsEnabled
            curSRHandleReverseProxy = srHandleReverseProxy
            themeSpinner = srThemeName
        except NameError:
            curSRHost = "localhost"
            curSRHttpPort = sickrage.WEB_PORT
            curSRHttpsEnabled = "False"
            curSRHandleReverseProxy = "False"
            themeSpinner = sickrage.THEME_NAME
    %>
    <% themeSpinner = ('', '-dark')['dark' == themeSpinner] %>
    <h2>Performing Restart</h2>
    <br>
    <div id="shut_down_message">
        Waiting for SickRage to shut down:
        <img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="shut_down_loading"/>
        <img src="${srRoot}/images/yes16.png" height="16" width="16" id="shut_down_success" style="display: none;"/>
    </div>

    <div id="restart_message" style="display: none;">
        Waiting for SickRage to start again:
        <img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="restart_loading"/>
        <img src="${srRoot}/images/yes16.png" height="16" width="16" id="restart_success" style="display: none;"/>
        <img src="${srRoot}/images/no16.png" height="16" width="16" id="restart_failure" style="display: none;"/>
    </div>

    <div id="refresh_message" style="display: none;">
        Loading the default page:
        <img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="refresh_loading"/>
    </div>

    <div id="restart_fail_message" style="display: none;">
        Error: The restart has timed out, perhaps something prevented SickRage from starting again?
    </div>
</%block>