<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime
    import calendar

    import sickrage
    from sickrage.core.common import Quality
    from sickrage.core.enums import SearchFormat
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
                    <input type="hidden" id="series_id" value="${show.series_id}"/>

                    <div class="row">
                        <div class="col mx-auto">

                            <div class="card mb-3">
                                <div class="card-body">
                                    <h3>${_('Preview of the proposed name changes')}</h3>
                                    <blockquote>
                                        % if show.search_format == SearchFormat.AIR_BY_DATE and sickrage.app.config.general.naming_custom_abd:
                                    ${sickrage.app.config.general.naming_abd_pattern}
                                        % elif show.search_format == SearchFormat.SPORTS and sickrage.app.config.general.naming_custom_sports:
                                    ${sickrage.app.config.general.naming_sports_pattern}
                                        % else:
                                    ${sickrage.app.config.general.naming_pattern}
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
                                    <a href="${srWebRoot}/home/displayShow?show=${show.series_id}"
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
                                            % for episode_object in episode_objects:
                                            <%
                                                curLoc = episode_object.location[len(episode_object.show.location)+1:]
                                                curExt = curLoc.split('.')[-1]
                                                newLoc = episode_object.proper_path() + '.' + curExt
                                            %>
                                            % if int(episode_object.season) != curSeason:
                                                <thead>
                                                <tr id="season-${episode_object.season}">
                                                    <td colspan="4">
                                                        <h2>${('Season '+str(episode_object.season), 'Specials')[int(episode_object.season) == 0]}</h2>
                                                    </td>
                                                </tr>
                                                <tr class="seasoncols" id="season-${episode_object.season}-cols">
                                                    <th class="col-checkbox">
                                                        <input type="checkbox" class="seasonCheck"
                                                               id="${episode_object.season}"/>
                                                    </th>
                                                    <th>${_('Episode')}</th>
                                                    <th>${_('Old Location')}</th>
                                                    <th>${_('New Location')}</th>
                                                </tr>
                                                </thead>
                                            <% curSeason = int(episode_object.season) %>
                                            % endif
                                                <tbody>
                                                    <%
                                                        odd = not odd
                                                        epStr = str(episode_object.season) + "x" + str(episode_object.episode)
                                                        epList = sorted([x.episode for x in [episode_object] + episode_object.related_episodes])
                                                        if len(epList) > 1:
                                                            epList = [min(epList), max(epList)]
                                                    %>
                                                <tr class="season-${curSeason} ${('wanted', 'good')[curLoc == newLoc]} text-dark">
                                                    <td class="table-fit">
                                                        % if curLoc != newLoc:
                                                            <input type="checkbox" class="epCheck"
                                                                   id="${"{}x{}".format(episode_object.season, episode_object.episode)}"
                                                                   name="${"{}x{}".format(episode_object.season, episode_object.episode)}"/>
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
                                    <a href="${srWebRoot}/home/displayShow?show=${show.series_id}"
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
