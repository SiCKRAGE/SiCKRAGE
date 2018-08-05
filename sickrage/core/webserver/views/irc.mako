<%inherit file="./layouts/main.mako"/>
<%block name="content">
<%
    import sickrage
    username = "SiCKRAGE-UI|?"
%>
<iframe id="extFrame" src="https://kiwiirc.com/client/irc.freenode.net/?nick=${username}&theme=basic#sickrage" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
</%block>
