<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime
    import calendar

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings
    from sickrage.core.helpers import srdatetime
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <input type="hidden" id="showID" value="${show.indexer_id}"/>

                    <div class="row">
                        <div class="col mx-auto">

                            <div class="card mb-3">
                                <div class="card-body">
                                    <h3>${_('Preview of the proposed name changes')}</h3>
                                    <blockquote>
                                        % if int(show.air_by_date) == 1 and sickrage.app.config.naming_custom_abd:
                                    ${sickrage.app.config.naming_abd_pattern}
                                        % elif int(show.sports) == 1 and sickrage.app.config.naming_custom_sports:
                                    ${sickrage.app.config.naming_sports_pattern}
                                        % else:
                                    ${sickrage.app.config.naming_pattern}
                                        % endif
                                    </blockquote>
                                </div>
                            </div>
                        </div>
                    </div>

                    <% curSeason = -1 %>
                    <% odd = False%>

                    <div class="row">
                        <div class="col mx-auto">
                            <div class="card mb-3">
                                <div class="card-header">
                                    <h3>${_('All Seasons')}</h3>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table id="SelectAllTable" class="table">
                                            <thead>
                                            <tr class="seasoncols" id="selectall">
                                                <th class="col-checkbox">
                                                    <input type="checkbox" class="seriesCheck" id="SelectAll"/>
                                                </th>
                                                <th align="left" valign="top"
                                                    class="text-nowrap">${_('Select All')}</th>
                                                <th width="100%" class="col-name d-none"></th>
                                            </tr>
                                            </thead>
                                        </table>
                                    </div>
                                </div>
                                <div class="card-footer">
                                    <input type="submit" value="${_('Rename Selected')}" class="btn btn-success"/>
                                    <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}"
                                       class="btn btn-danger">${_('Cancel Rename')}</a>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col mx-auto">
                            <div class="card mb-3">
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table id="testRenameTable" class="table">
                                            % for cur_ep_obj in ep_obj_list:
                                            <%
                                                curLoc = cur_ep_obj.location[len(cur_ep_obj.show.location)+1:]
                                                curExt = curLoc.split('.')[-1]
                                                newLoc = cur_ep_obj.proper_path() + '.' + curExt
                                            %>
                                            % if int(cur_ep_obj.season) != curSeason:
                                                <thead>
                                                <tr id="season-${cur_ep_obj.season}">
                                                    <td colspan="4">
                                                        <h2>${('Season '+str(cur_ep_obj.season), 'Specials')[int(cur_ep_obj.season) == 0]}</h2>
                                                    </td>
                                                </tr>
                                                <tr class="seasoncols" id="season-${cur_ep_obj.season}-cols">
                                                    <th class="col-checkbox">
                                                        <input type="checkbox" class="seasonCheck"
                                                               id="${cur_ep_obj.season}"/>
                                                    </th>
                                                    <th>${_('Episode')}</th>
                                                    <th>${_('Old Location')}</th>
                                                    <th>${_('New Location')}</th>
                                                </tr>
                                                </thead>
                                            <% curSeason = int(cur_ep_obj.season) %>
                                            % endif
                                                <tbody>
                                                    <%
                                                        odd = not odd
                                                        epStr = str(cur_ep_obj.season) + "x" + str(cur_ep_obj.episode)
                                                        epList = sorted([cur_ep_obj.episode] + [x.episode for x in cur_ep_obj.relatedEps])
                                                        if len(epList) > 1:
                                                            epList = [min(epList), max(epList)]
                                                    %>
                                                <tr class="season-${curSeason} ${('wanted', 'good')[curLoc == newLoc]} text-dark">
                                                    <td class="table-fit">
                                                        % if curLoc != newLoc:
                                                            <input type="checkbox" class="epCheck"
                                                                   id="${"{}x{}".format(cur_ep_obj.season, cur_ep_obj.episode)}"
                                                                   name="${"{}x{}".format(cur_ep_obj.season, cur_ep_obj.episode)}"/>
                                                        % endif
                                                    </td>
                                                    <td class="table-fit">${"-".join(map(str, epList))}</td>
                                                    <td>${curLoc}</td>
                                                    <td>${newLoc}</td>
                                                </tr>
                                                </tbody>
                                            % endfor
                                        </table>
                                    </div>
                                </div>
                                <div class="card-footer">
                                    <input type="submit" value="${_('Rename Selected')}" class="btn btn-success"/>
                                    <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}"
                                       class="btn btn-danger">${_('Cancel Rename')}</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
