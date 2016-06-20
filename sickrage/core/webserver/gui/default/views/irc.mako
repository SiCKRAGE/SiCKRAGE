<%inherit file="/layouts/main.mako"/>
<%block name="content">
<%
    import sickrage
    from sickrage.srCore.srConfig import GIT_USERNAME
    username = ("SiCKRAGEUI|?", GIT_USERNAME)[bool(GIT_USERNAME)]
%>
<iframe id="extFrame" src="https://kiwiirc.com/client/irc.freenode.net/?nick=${username}&theme=basic#sickrage" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
</%block>
