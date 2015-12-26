<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.logger import SRLogger
    from sickbeard import classes
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/viewlogs.js"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div class="h2footer pull-right">Minimum logging level to display: <select name="minLevel" id="minLevel" class="form-control form-control-inline input-sm">
<% levels = [x for x in SRLogger.logLevels.keys() if any([sickbeard.DEBUG and x in ['DEBUG','DB'], x not in ['DEBUG','DB']])]%>
<% levels.sort(lambda x,y: cmp(SRLogger.logLevels[x], SRLogger.logLevels[y])) %>
% for level in levels:
    <option value="${SRLogger.logLevels[level]}" ${('', 'selected="selected"')[minLevel == SRLogger.logLevels[level]]}>${level.title()}</option>
% endfor
</select>

Filter log by: <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm">
% for logNameFilter in sorted(logNameFilters):
    <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
% endfor
</select>
Search log by:
<input type="text" name="logSearch" placeholder="clear to reset" id="logSearch" value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm" />
</div>
<br>
<div class="align-left"><pre>
${logLines}
</pre>
</div>
<br>
</%block>
