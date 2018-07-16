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
    <div class="sickrage-card">
        <div class="sickrage-card-header">
            <h3>${title}</h3>
        </div>
        <div class="card-body">
            <div class="align-left">
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
