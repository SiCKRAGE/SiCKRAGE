<%inherit file="../layouts/main.mako"/>
<%!
    import sys, os

    import sickrage
    from sickrage.core.databases import dbFilename
    from sickrage.core.helpers import anon_url
%>
<%block name="content">

<div id="ui-content">
<table class="infoTable" cellspacing="1" border="0" cellpadding="0" width="100%">
    <tr>
        <td class="infoTableHeader">SR Version: </td>
        <td class="infoTableCell">
            ${sickrage.srCore.VERSIONUPDATER.updater.version}<br>
        </td>
    </tr>

    <tr>
        <td class="infoTableHeader">SR Type: </td>
        <td class="infoTableCell">
            ${sickrage.srCore.VERSIONUPDATER.updater.type}<br>
        </td>
    </tr>

<%
    sr_user = None
    try:
        import pwd
        sr_user = pwd.getpwuid(os.getuid()).pw_name
    except ImportError:
        import getpass
        sr_user = getpass.getuser()
%>
% if sr_user:
    <tr><td class="infoTableHeader">SR User:</td><td class="infoTableCell">${sr_user}</td></tr>
% endif

    <tr><td class="infoTableHeader">SR Locale:</td><td class="infoTableCell">${sickrage.SYS_ENCODING}</td></tr>
    <tr>
        <td class="infoTableHeader">SR Config:</td>
        <td class="infoTableCell">${sickrage.CONFIG_FILE}</td>
    </tr>
    <tr>
        <td class="infoTableHeader">SR Database:</td>
        <td class="infoTableCell">${dbFilename()}</td>
    </tr>
    <tr>
        <td class="infoTableHeader">SR Cache Dir:</td>
        <td class="infoTableCell">${sickrage.srCore.srConfig.CACHE_DIR}</td>
    </tr>
    <tr>
        <td class="infoTableHeader">SR Log Dir:</td>
        <td class="infoTableCell">${sickrage.srCore.srConfig.LOG_DIR}</td>
    </tr>
    <tr>
        <td class="infoTableHeader">SR Arguments:</td>
        <td class="infoTableCell">${sys.argv[1:]}</td>
    </tr>
    % if sickrage.srCore.srConfig.WEB_ROOT:
        <tr>
            <td class="infoTableHeader">SR Web Root:</td>
            <td class="infoTableCell">${sickrage.srCore.srConfig.WEB_ROOT}</td>
        </tr>
% endif
    <tr><td class="infoTableHeader">Python Version:</td><td class="infoTableCell">${sys.version[:120]}</td></tr>
    <tr class="infoTableSeperator"><td class="infoTableHeader"><i class="icon16-sb"></i> Homepage</td><td class="infoTableCell"><a href="${anon_url('http://www.sickrage.ca/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://www.sickrage.ca/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-WiKi"></i> WiKi</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SiCKRAGETV/sickrage-issues/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SiCKRAGETV/sickrage-issues/wiki</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-web"></i> Forums</td><td class="infoTableCell"><a href="${anon_url('http://sickrage.tv/forums/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://www.sickrage.ca/forums/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-github"></i> Source</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SiCKRAGETV/SiCKRAGE/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SiCKRAGETV/SickRage/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-mirc"></i> IRChat</td><td class="infoTableCell"><a href="irc://irc.freenode.net/#sickrage" rel="noreferrer"><i>#sickrage</i> on <i>irc.freenode.net</i></a></td></tr>
</table>
</div>
</%block>
