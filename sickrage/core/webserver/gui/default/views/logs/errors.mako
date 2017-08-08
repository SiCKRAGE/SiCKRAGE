<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.classes import ErrorViewer, WarningViewer
%>
<%block name="content">
    <%
        if logLevel == sickrage.srCore.srLogger.logLevels['WARNING']:
            errors = WarningViewer.errors
            title = 'WARNING logs'
        else:
            errors = ErrorViewer.errors
            title = 'ERROR logs'
    %>
    <div class="row">
        <div class="col-md-12">
            <h1 class="header">${title}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <div class="align-left">
                <pre>
                    % if errors:
                        % for curError in sorted(errors, key=lambda error: error.time, reverse=True)[:500]:
                            ${curError.time} ${curError.message}
                        % endfor
                    % else:
                        There are no events to display.
                    % endif
                </pre>
            </div>
        </div>
    </div>
</%block>
