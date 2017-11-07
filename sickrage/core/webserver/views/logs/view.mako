<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 col-md-9 col-sm-12 col-xs-12 pull-right">
            <div class="pull-right">
                <label for="minLevel" class="badge">${_('Minimum logging level to display:')}
                    <select name="minLevel" id="minLevel"
                            class="form-control form-control-inline input-sm">
                        <% levels = [x for x in sickrage.app.log.logLevels.keys() if any([sickrage.app.config.DEBUG and x in ['DEBUG','DB'], x not in ['DEBUG','DB']])]%>
                        <% levels.sort(lambda x,y: cmp(sickrage.app.log.logLevels[x], sickrage.app.log.logLevels[y])) %>
                        % for level in levels:
                            <option value="${sickrage.app.log.logLevels[level]}" ${('', 'selected')[minLevel == sickrage.app.log.logLevels[level]]}>${level.title()}</option>
                        % endfor
                    </select>
                </label>

                <label for="logFilter" class="badge">${_('Filter log by:')}
                    <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm">
                        % for logNameFilter in sorted(logNameFilters):
                            <option value="${logNameFilter}" ${('', 'selected')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                        % endfor
                    </select>
                </label>

                <label for="logSearch" class="badge">${_('Search log by:')}
                    <input type="text" name="logSearch" placeholder="${_('clear to reset')}" id="logSearch"
                           value="${('', logSearch)[bool(logSearch)]}"
                           class="form-control form-control-inline input-sm"/>
                </label>
            </div>
        </div>
        <div class="col-lg-2 col-md-3 col-sm-12 col-xs-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <pre style="text-align: left;white-space: pre-line;">
                ${logLines}
            </pre>
        </div>
    </div>
</%block>
