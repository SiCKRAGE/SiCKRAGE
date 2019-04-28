<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <%
        if int(logLevel) == sickrage.app.log.logLevels['WARNING']:
            logs = sickrage.app.log.warning_viewer.get()
            title = _('WARNING Logs')
        else:
            logs = sickrage.app.log.error_viewer.get()
            title = _('ERROR Logs')
    %>
    <div class="card">
        <div class="card-header">
            <h3>${title}</h3>
        </div>
        <div class="card-body">
            <div class="text-left" style="white-space: pre-line;">
                % if len(logs):
                <% logs = sorted(logs, key=lambda x: x.time, reverse=True) %>
                % for entry in logs[:500]:
                    ${entry.time} ${entry.message}
                % endfor
                % else:
                    ${_('There are no events to display.')}
                % endif
            </div>
        </div>
    </div>
</%block>
