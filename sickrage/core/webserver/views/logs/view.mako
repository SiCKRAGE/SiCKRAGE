<%inherit file="../layouts/main.mako"/>
<%!
    from functools import cmp_to_key
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">
                    <h3 class="float-md-left">${title}</h3>
                    <div class="form-inline float-md-right">
                        <label class="m-1">
                            <select name="refreshInterval" id="refreshInterval"
                                    class="form-control form-control-inline">
                                <option value="5" selected>5s</option>
                                <option value="10">10s</option>
                                <option value="15">15s</option>
                            </select>
                        </label>

                        <label class="m-1">
                            <select name="minLevel" id="minLevel"
                                    class="form-control form-control-inline">
                                <% levels = [x for x in sickrage.app.log.logLevels.keys() if x not in ['DEBUG','DB']]%>
                                <% levels += [x for x in sickrage.app.log.logLevels.keys() if (sickrage.app.debug or sickrage.app.config.general.debug) and x in ['DEBUG','DB']]%>
                                <% levels.sort(key=cmp_to_key(lambda x,y: sickrage.app.log.logLevels[x] < sickrage.app.log.logLevels[y])) %>
                                % for level in levels:
                                    <option value="${sickrage.app.log.logLevels[level]}" ${('', 'selected')[minLevel == sickrage.app.log.logLevels[level]]}>${level.title()}</option>
                                % endfor
                            </select>
                        </label>

                        <label class="m-1">
                            <select name="logFilter" id="logFilter" class="form-control form-control-inline">
                                % for logNameFilter in sorted(logNameFilters):
                                    <option value="${logNameFilter}" ${('', 'selected')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                                % endfor
                            </select>
                        </label>

                        <label class="m-1">
                            <input type="text" name="logSearch" placeholder="${_('clear to reset')}" id="logSearch"
                                   value="${('', logSearch)[bool(logSearch)]}"
                                   class="form-control form-control-inline"/>
                        </label>
                    </div>
                </div>
                <div class="card-body">
                    <div class="text-left" style="white-space: pre-line;">
                        <div id="loglines">${logLines}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
