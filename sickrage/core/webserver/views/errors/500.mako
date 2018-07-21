<%inherit file="../layouts/main.mako"/>
<%block name="content">
    <p>
        ${_('A mako error has occured.')}<br>
        ${_('If this happened during an update a simple page refresh may be the solution.')}<br>
        ${_('Mako errors that happen during updates may be a one time error if there were significant ui changes.')}
    </p>
    <hr>
    <a href="#mako-error" class="sickrage-btn" data-toggle="collapse">${_('Show/Hide Error')}</a>
    <div id="mako-error" class="collapse">
        <br>
        <div class="text-left">
            <% filename, lineno, function, line = backtrace.traceback[-1] %>
            <pre class="text-white">
                ${_('File')} ${filename}:${lineno}, ${_('in')} ${function}:
                % if line:
                    ${line}
                % endif
                ${str(backtrace.error.__class__.__name__)}:${backtrace.error}
            </pre>
        </div>
    </div>
</%block>