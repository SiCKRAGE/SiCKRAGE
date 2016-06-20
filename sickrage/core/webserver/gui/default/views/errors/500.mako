<%inherit file="../layouts/main.mako"/>

<%block name="content">

<p>A mako error has occured.</p>
<hr>
<a href="#mako-error" class="btn btn-default" data-toggle="collapse">Show/Hide Error</a>
<div id="mako-error" class="collapse">
<br>
<div class="align-center">
<pre>
<% filename, lineno, function, line = backtrace.traceback[-1] %>
File ${filename}:${lineno}, in ${function}:
% if line:
${line}
% endif
${str(backtrace.error.__class__.__name__)}:${backtrace.error}
</pre>
</div>
</div>
</%block>