<%inherit file="../layouts/main.mako"/>
<%block name="content">
    <div class="row">
        <div class="col-md-8 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <p>
                        ${_('A mako error has occured.')}<br>
                        ${_('If this happened during an update a simple page refresh may be the solution.')}<br>
                        ${_('Mako errors that happen during updates may be a one time error if there were significant UI changes.')}
                    </p>
                    <hr>
                    <a href="#mako-error" class="btn" data-toggle="collapse">${_('Show/Hide Error')}</a>
                    <br><br>
                    <div id="mako-error" class="collapse">
                        <div class="text-left">
                            <% filename, lineno, function, line = backtrace.traceback[-1] %>

                            <pre class="text-danger" style="white-space: pre-line">
                                ${_('File')} ${filename}:${lineno}, ${_('in')} ${function}:
                                % if line:
                                    ${line}
                                % endif
                                ${str(backtrace.error.__class__.__name__)}:${backtrace.error}
                            </pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>