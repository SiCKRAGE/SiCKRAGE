<%inherit file="../layouts/main.mako"/>
<%block name="content">
    <p>
        A mako error has occured.<br>
        If this happened during an update a simple page refresh may be the solution.<br>
        Mako errors that happen during updates may be a one time error if there were significant ui changes.
    </p>
    <hr>
    <a href="#mako-error" class="btn btn-default" data-toggle="collapse">Show/Hide Error</a>
    <div id="mako-error" class="collapse">
        <br>
        <div class="align-center">
            <% filename, lineno, function, line = backtrace.traceback[-1] %>
            <pre>
                File ${filename}:${lineno}, in ${function}:
                % if line:
                    ${line}
                % endif
                ${str(backtrace.error.__class__.__name__)}:${backtrace.error}
            </pre>
        </div>
    </div>
</%block>