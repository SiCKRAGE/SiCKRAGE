<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="metas">
<meta data-var="srDefaultPage" data-content="${srDefaultPage}">
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
    themeSpinner = srThemeName
except NameError:
    themeSpinner = sickrage.srCore.srConfig.THEME_NAME
%>
<h2>Performing Restart</h2>
<div class="messages">
    <div id="shut_down_message">
        Waiting for SiCKRAGE to shut down:
        <img src="/images/loading16-${themeSpinner}.gif" height="16" width="16" id="shut_down_loading" />
        <img src="/images/yes16.png" height="16" width="16" id="shut_down_success" style="display: none;" />
    </div>
    <div id="restart_message" style="display: none;">
        Waiting for SiCKRAGE to start again:
        <img src="/images/loading16-${themeSpinner}.gif" height="16" width="16" id="restart_loading" />
        <img src="/images/yes16.png" height="16" width="16" id="restart_success" style="display: none;" />
        <img src="/images/no16.png" height="16" width="16" id="restart_failure" style="display: none;" />
    </div>
    <div id="refresh_message" style="display: none;">
        Loading the default page:
        <img src="/images/loading16-${themeSpinner}.gif" height="16" width="16" id="refresh_loading" />
    </div>
    <div id="restart_fail_message" style="display: none;">
        Error: The restart has timed out, perhaps something prevented SiCKRAGE from starting again?
    </div>
</div>
</%block>