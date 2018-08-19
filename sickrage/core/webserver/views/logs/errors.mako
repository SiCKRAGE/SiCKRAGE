<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.classes import ErrorViewer, WarningViewer
%>
<%block name="content">
    <%
        if logLevel == sickrage.app.log.logLevels['WARNING']:
            errors = WarningViewer.errors
            title = _('WARNING Logs')
        else:
            errors = ErrorViewer.errors
            title = _('ERROR Logs')
    %>
    <div class="card">
        <div class="card-header">
            <h3>${title}</h3>
        </div>
        <div class="card-body">
            <div class="text-left" style="white-space: pre-line;">
                % if errors:
                % for curError in sorted(errors, key=lambda error: error.time, reverse=True)[:500]:
                                                ${curError.time} ${curError.message}
                % endfor
                % else:
                ${_('There are no events to display.')}
                % endif
            </div>
        </div>
    </div>
</%block>
