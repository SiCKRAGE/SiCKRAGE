<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-xs-12 text-center">
            <label for="minLevel" class="badge">Minimum logging level to display:
                <select name="minLevel" id="minLevel"
                        class="form-control form-control-inline input-sm">
                    <% levels = [x for x in sickrage.srCore.srLogger.logLevels.keys() if any([sickrage.DEBUG and x in ['DEBUG','DB'], x not in ['DEBUG','DB']])]%>
                    <% levels.sort(lambda x,y: cmp(sickrage.srCore.srLogger.logLevels[x], sickrage.srCore.srLogger.logLevels[y])) %>
                    % for level in levels:
                        <option value="${sickrage.srCore.srLogger.logLevels[level]}" ${('', 'selected="selected"')[minLevel == sickrage.srCore.srLogger.logLevels[level]]}>${level.title()}</option>
                    % endfor
                </select>
            </label>

            <label for="logFilter" class="badge">Filter log by:
                <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm">
                    % for logNameFilter in sorted(logNameFilters):
                        <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                    % endfor
                </select>
            </label>

            <label for="logSearch" class="badge">Search log by:
                <input type="text" name="logSearch" placeholder="clear to reset" id="logSearch"
                       value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm"/>
            </label>
        </div>
    </div>
    <div class="row">
        <div class="col-xs-12">
            <pre>
                ${logLines}
            </pre>
        </div>
    </div>
    <br>
</%block>
