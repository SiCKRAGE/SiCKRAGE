<%inherit file="./layouts/main.mako"/>
<%!
    import re
    import time
    import datetime

    import sickrage
    from sickrage.core.helpers import anon_url, srdatetime
    from sickrage.core.media.util import series_image, SeriesImageType
    from sickrage.core.tv.show.coming_episodes import ComingEpsLayout, ComingEpsSortBy
%>
<%block name="content">
    <%namespace file="./includes/quality_defaults.mako" import="renderQualityPill"/>
    <div class="row">
        <div class="col-lg-10 mx-auto">
        <div class="card">
            <div class="card-header">
                <h3 class="float-left">${title}</h3>
                <div class="float-right">
                    <div class="form-inline">
                        % if layout == ComingEpsLayout.LIST:
                            <button class="btn btn-dark mr-1" id="popover" type="button">
                                ${_('Select Columns')} <b class="fas fa-caret-down"></b>
                            </button>
                        % else:
                            <select id="sortby" name="sort" class="form-control mr-1"
                                    onchange="location = this.options[this.selectedIndex].value;">
                                % for item in ComingEpsSortBy:
                                    <option value="${srWebRoot}/setScheduleSort/?sort=${item.name}" ${('', 'selected')[sickrage.app.config.gui.coming_eps_sort == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        % endif

                        <select id="viewpaused" name="viewpaused" class="form-control mr-1"
                                onchange="location = this.options[this.selectedIndex].value;">
                            <option value="${srWebRoot}/toggleScheduleDisplayPaused" ${('', 'selected')[not bool(sickrage.app.config.gui.coming_eps_display_paused)]}>
                                Hidden
                            </option>
                            <option value="${srWebRoot}/toggleScheduleDisplayPaused" ${('', 'selected')[bool(sickrage.app.config.gui.coming_eps_display_paused)]}>
                                Shown
                            </option>
                        </select>

                        <select id="layout" name="layout" class="form-control mr-1"
                                onchange="location = this.options[this.selectedIndex].value;">
                            % for item in ComingEpsLayout:
                                <option value="${srWebRoot}/setScheduleLayout/?layout=${item.name}" ${('', 'selected')[sickrage.app.config.gui.coming_eps_layout == item]}>${item.display_name}</option>
                            % endfor
                        </select>

                        <a class="btn btn-dark forceBacklog"
                           href="webcal://${srHost}:${srHttpPort}/calendar">
                            <i class="icon-calendar icon-white"></i>
                            Subscribe
                        </a>
                    </div>
                    <div class="float-right mt-1">
                        % if ComingEpsLayout.CALENDAR != layout:
                            <span class="badge text-black-50 listing-overdue">Missed</span>
                            <span class="badge text-black-50 listing-current">Today</span>
                            <span class="badge text-black-50 listing-default">Soon</span>
                            <span class="badge text-black-50 listing-toofar">Later</span>
                        % endif
                    </div>
                </div>
            </div>
        <div class="card-body">
            % if ComingEpsLayout.LIST == layout:
                <div class="col-md-12">
                    <% show_div = 'listing-default' %>

                    <div class="table-responsive">
                        <table class="table" id="showListTable">
                            <thead class="thead-dark">
                            <tr>
                                <th>
                                    Airdate
                                    (${sickrage.app.config.gui.timezone_display.display_name})
                                </th>
                                <th>Ends</th>
                                <th>Next Ep</th>
                                <th>Show</th>
                                <th>Next Ep Name</th>
                                <th>Network</th>
                                <th>Run time</th>
                                <th>Quality</th>
                                <th>Series Provider</th>
                                <th>Search</th>
                            </tr>
                            </thead>

                            <tbody class="text-dark">
                                % for cur_result in results:
                                    % if not int(cur_result['paused']) or sickrage.app.config.gui.coming_eps_display_paused:
                                        <%
                                            cur_series_provider_id = cur_result['series_provider_id']
                                            run_time = int(cur_result['runtime'] or 0)

                                            cur_ep_airdate = cur_result['localtime'].date()
                                            cur_ep_enddate = cur_result['localtime']

                                            if run_time:
                                                            cur_ep_enddate += datetime.timedelta(minutes = run_time)

                                            if cur_ep_enddate < today:
                                                            show_div = 'listing-overdue'
                                            elif cur_ep_airdate >= next_week.date():
                                                            show_div = 'listing-toofar'
                                            elif today.date() <= cur_ep_airdate < next_week.date():
                                                            if cur_ep_airdate == today.date():
                                                                show_div = 'listing-current'
                                                            else:
                                                                show_div = 'listing-default'
                                        %>

                                        <tr class="${show_div}">
                                            <td class="table-fit text-nowrap">
                                                <% airDate = srdatetime.SRDateTime(cur_result['localtime'], convert=True).dt %>
                                                <time datetime="${airDate.isoformat()}"
                                                      class="date">${srdatetime.SRDateTime(airDate).srfdatetime()}</time>
                                            </td>

                                            <td class="table-fit text-nowrap">
                                                <% ends = srdatetime.SRDateTime(cur_ep_enddate, convert=True).dt %>
                                                <time datetime="${ends.isoformat()}"
                                                      class="date">${srdatetime.SRDateTime(ends).srfdatetime()}</time>
                                            </td>

                                            <td class="table-fit text-nowrap">
                                                ${'S{:02d}E{:02d}'.format(int(cur_result['season']), int(cur_result['episode']))}
                                            </td>

                                            <td class="tvShow" class="text-nowrap">
                                                <a href="${srWebRoot}/home/displayShow?show=${cur_result['series_id']}">
                                                    ${cur_result['show_name']}
                                                </a>
                                                % if int(cur_result['paused']):
                                                    <span class="pause">[paused]</span>
                                                % endif
                                            </td>

                                            <td>
                                                % if cur_result['description']:
                                                    <i class="fas fa-exclamation-circle"
                                                       title="${cur_result["description"]}"
                                                       id="plot_info_${'{}_{}_{}'.format(cur_result['series_id'], cur_result['season'], cur_result['episode'])}"></i>
                                                % else:
                                                    <i class="fas fa-exclamation-circle"></i>
                                                % endif
                                                ${cur_result['name']}
                                            </td>

                                            <td class="table-fit text-nowrap">
                                                ${cur_result['network']}
                                            </td>

                                            <td class="table-fit">
                                                ${run_time}min
                                            </td>

                                            <td class="table-fit">
                                                ${renderQualityPill(cur_result['quality'], showTitle=True)}
                                            </td>

                                            <td class="table-fit" style="vertical-align: middle;">
                                                % if cur_result['imdb_id']:
                                                    <a href="${anon_url('http://www.imdb.com/title/', cur_result['imdb_id'])}"
                                                       rel="noreferrer"
                                                       onclick="window.open(this.href, '_blank'); return false"
                                                       title="http://www.imdb.com/title/${cur_result['imdb_id']}">
                                                        <i class="sickrage-core sickrage-core-imdb"></i>
                                                    </a>
                                                % endif
                                                <a href="${anon_url(sickrage.app.series_providers[cur_series_provider_id].show_url, cur_result['series_id'])}"
                                                   rel="noreferrer"
                                                   onclick="window.open(this.href, '_blank'); return false"
                                                   title="${sickrage.app.series_providers[cur_series_provider_id].show_url}${cur_result['series_id']}"><i
                                                        class="sickrage-core sickrage-core-${cur_series_provider_id.name.lower()}"></i>
                                                </a>
                                            </td>

                                            <td class="table-fit col-search">
                                                <a href="${srWebRoot}/home/searchEpisode?show=${cur_result['series_id']}&seriesProviderID=${cur_result['series_provider_id'].name}&season=${cur_result['season']}&episode=${cur_result['episode']}"
                                                   class="epSearch" title="${_('Manual Search')}"
                                                   id="${cur_result['series_id']}x${cur_result['season']}x${cur_result['episode']}"
                                                   name="${cur_result['series_id']}x${cur_result['season']}x${cur_result['episode']}">
                                                    <i class="fas fa-search"></i>
                                                </a>
                                            </td>
                                        </tr>
                                    % endif
                                % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            % elif layout in [ComingEpsLayout.BANNER, ComingEpsLayout.POSTER]:
                <%
                    cur_segment = None
                    too_late_header = False
                    missed_header = False
                    today_header = False
                    show_div = 'ep_listing listing-default'
                %>
                % if sickrage.app.config.gui.coming_eps_sort == ComingEpsSortBy.SHOW:
                    <br/><br/>
                % endif

                % for cur_result in results:
                    % if not int(cur_result['paused']) or sickrage.app.config.gui.coming_eps_display_paused:
                    <%
                        cur_series_provider_id = cur_result['series_provider_id']

                        run_time = int(cur_result['runtime'] or 0)
                        cur_ep_airdate = cur_result['localtime'].date()

                        if run_time:
                            cur_ep_enddate = cur_result['localtime'] + datetime.timedelta(minutes = run_time)
                        else:
                            cur_ep_enddate = cur_result['localtime']
                    %>

                    % if sickrage.app.config.gui.coming_eps_sort == ComingEpsSortBy.NETWORK:
                        <% show_network = ('no network', cur_result['network'])[bool(cur_result['network'])] %>
                        % if cur_segment != show_network:
                            <div>
                                <br/>
                                <h2 class="network">${show_network}</h2>
                            </div>

                        <% cur_segment = cur_result['network'] %>
                        % endif

                        % if cur_ep_enddate < today:
                            <% show_div = 'ep_listing listing-overdue' %>
                        % elif cur_ep_airdate >= next_week.date():
                            <% show_div = 'ep_listing listing-toofar' %>
                        % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                            % if cur_ep_airdate == today.date():
                                <% show_div = 'ep_listing listing-current' %>
                            % else:
                                <% show_div = 'ep_listing listing-default' %>
                            % endif
                        % endif
                    % elif sickrage.app.config.gui.coming_eps_sort == ComingEpsSortBy.DATE:
                        % if cur_segment != cur_ep_airdate:
                            % if cur_ep_enddate < today and cur_ep_airdate != today.date() and not missed_header:
                            <% missed_header = True %>
                                <h2 class="day">Missed</h2>
                            % elif cur_ep_airdate >= next_week.date() and not too_late_header:
                            <% too_late_header = True %>
                                <h2 class="day">Later</h2>
                            % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                                % if cur_ep_airdate == today.date():
                                    <br/>
                                    <h2 class="day">${cur_ep_airdate.strftime('%A').capitalize()}
                                        <span style="font-size: 14px; vertical-align: top;">[Today]</span>
                                    </h2>
                                <% today_header = True %>
                                % else:
                                    <br/>
                                    <h2 class="day">${cur_ep_airdate.strftime('%A').capitalize()}</h2>
                                % endif
                            % endif
                            <% cur_segment = cur_ep_airdate %>
                        % endif

                        % if cur_ep_airdate == today.date() and not today_header:
                            <div>
                                <br/>
                                <h2 class="day">${cur_ep_airdate.strftime('%A').capitalize()}
                                    <span style="font-size: 14px; vertical-align: top;">[Today]</span>
                                </h2>
                            </div>
                        <% today_header = True %>
                        % endif

                        % if cur_ep_enddate < today:
                            <% show_div = 'ep_listing listing-overdue' %>
                        % elif cur_ep_airdate >= next_week.date():
                            <% show_div = 'ep_listing listing-toofar' %>
                        % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                            % if cur_ep_airdate == today.date():
                                <% show_div = 'ep_listing listing-current' %>
                            % else:
                                <% show_div = 'ep_listing listing-default'%>
                            % endif
                        % endif

                    % elif sickrage.app.config.gui.coming_eps_sort == ComingEpsSortBy.SHOW:
                        % if cur_ep_enddate < today:
                            <% show_div = 'ep_listing listing-overdue listingradius' %>
                        % elif cur_ep_airdate >= next_week.date():
                            <% show_div = 'ep_listing listing-toofar listingradius' %>
                        % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                            % if cur_ep_airdate == today.date():
                                <% show_div = 'ep_listing listing-current listingradius' %>
                            % else:
                                <% show_div = 'ep_listing listing-default listingradius' %>
                            % endif
                        % endif
                    % endif
                        <div class="card mb-3" id="listing-${cur_result['series_id']}">
                            <div class="card-body rounded ${show_div} m-1">
                                <div class="row">
                                    <div class="col-auto justify-content-center align-self-center">
                                        <a href="${srWebRoot}/home/displayShow?show=${cur_result['series_id']}">
                                            <img class="rounded shadow ${('', 'img-poster')[layout == ComingEpsLayout.POSTER]}"
                                                 src="${srWebRoot}${series_image(cur_result['series_id'], cur_result['series_provider_id'], SeriesImageType[layout.name]).url}"/>
                                        </a>
                                    </div>
                                    <div class="col text-dark font-weight-bold">
                                        <div class="clearfix">
                                            <span>
                                                <a href="${srWebRoot}/home/displayShow?show=${cur_result['series_id']}">${cur_result['show_name']}
                                                    ${('', '<span class="pause">[paused]</span>')[int(cur_result['paused'])]}
                                                </a>
                                                % if cur_result['imdb_id']:
                                                    <a href="${anon_url('http://www.imdb.com/title/', cur_result['imdb_id'])}"
                                                       rel="noreferrer"
                                                       onclick="window.open(this.href, '_blank'); return false"
                                                       title="http://www.imdb.com/title/${cur_result['imdb_id']}">
                                                        <i class="sickrage-core sickrage-core-imdb"></i>
                                                    </a>
                                                % endif
                                                <a href="${anon_url(sickrage.app.series_providers[cur_series_provider_id].show_url, cur_result['series_id'])}"
                                                   rel="noreferrer"
                                                   onclick="window.open(this.href, '_blank'); return false"
                                                   title="${sickrage.app.series_providers[cur_series_provider_id].show_url}">
                                                    <i class="sickrage-core sickrage-core-${cur_series_provider_id.name.lower()}"></i>
                                                </a>
                                                <a href="${srWebRoot}/home/searchEpisode?show=${cur_result['series_id']}&seriesProviderID=${cur_result['series_provider_id'].name}&season=${cur_result['season']}&episode=${cur_result['episode']}"
                                                   class="epSearch" title="${_('Manual Search')}"
                                                   id="${cur_result['series_id']}x${cur_result['season']}x${cur_result['episode']}"
                                                   name="${cur_result['series_id']}x${cur_result['season']}x${cur_result['episode']}">
                                                    <i class="fas fa-search"></i>
                                                </a>
                                            </span>
                                        </div>

                                        <span class="title">
                                            Next Episode:
                                        </span>

                                        <span>${'S{:02d}E{:02d}'.format(int(cur_result['season']), int(cur_result['episode']))}
                                            - ${cur_result['name']}
                                        </span>

                                        <div class="clearfix">
                                            <span class="title">
                                                Airs:
                                            </span>
                                            <span class="airdate">
                                                ${srdatetime.SRDateTime(cur_result['localtime']).srfdatetime()}
                                            </span>
                                            ${('', '<span> on %s</span>' % cur_result['network'])[bool(cur_result['network'])]}
                                        </div>

                                        <div class="clearfix">
                                            <span class="title">
                                                Quality:
                                            </span>
                                            ${renderQualityPill(cur_result['quality'], showTitle=True)}
                                        </div>
                                        <div class="clearfix">
                                            % if cur_result['description']:
                                                <span class="title" style="vertical-align:middle;">
                                                            Plot:
                                                        </span>
                                                <i class="fas fa-plus-square ep_summaryTrigger"
                                                   title="${_('Toggle Summary')}"></i>
                                                <div class="ep_summary">
                                                    ${cur_result['description']}
                                                </div>
                                            % else:
                                                <span class="title ep_summaryTriggerNone"
                                                      style="vertical-align:middle;">Plot:</span>
                                                <i class="fas fa-plus ep_summaryTriggerNone"
                                                   title="${_('Toggle Summary')}"></i>
                                            % endif
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endif
                % endfor
            % elif ComingEpsLayout.CALENDAR == layout:
            <% dates = [today.date() + datetime.timedelta(days = i) for i in range(7)] %>
            <% tbl_day = 0 %>
                <div class="table-responsive justify-content-center d-flex">
                    % for day in dates:
                        <table class="table w-auto text-center">
                            <thead>
                            <tr>
                                <th>${day.strftime('%A %d').capitalize()}</th>
                            </tr>
                            </thead>

                            <tbody>
                                <% day_has_show = False %>
                                % for cur_result in results:
                                    % if not int(cur_result['paused']) or sickrage.app.config.gui.coming_eps_display_paused:
                                        <% run_time = int(cur_result['runtime'] or 0) %>
                                        <% airday = cur_result['localtime'].date() %>

                                        % if airday == day:
                                            % try:
                                            <% day_has_show = True %>
                                            <% airtime = srdatetime.SRDateTime(datetime.datetime.fromtimestamp(time.mktime(cur_result['localtime'].timetuple()))).srftime() %>
                                            % if sickrage.app.config.gui.trim_zero:
                                                <% airtime = re.sub(r'0(\d:\d\d)', r'\1', airtime, 0, re.IGNORECASE | re.MULTILINE) %>
                                            % endif
                                            % except OverflowError:
                                            <% airtime = "Invalid" %>
                                            % endtry

                                            <tr>
                                                <td>
                                                    <a title="${cur_result['show_name']}"
                                                       href="${srWebRoot}/home/displayShow?show=${cur_result['series_id']}">
                                                        <img class="rounded shadow img-poster"
                                                             src="${srWebRoot}${series_image(cur_result['series_id'], cur_result['series_provider_id'], SeriesImageType.POSTER).url}"/>
                                                    </a>
                                                    <div class="small">
                                                    <span class="airtime">
                                                        ${airtime} on ${cur_result["network"]}
                                                    </span>
                                                        <br/>
                                                        <span class="episode-title" title="${cur_result['name']}">
                                                        ${'S{:02d}E{:02d}'.format(int(cur_result['season']), int(cur_result['episode']))}
                                                            - ${cur_result['name']}
                                                    </span>
                                                    </div>
                                                </td>
                                            </tr>
                                        % endif
                                    % endif
                                % endfor
                                % if not day_has_show:
                                    <tr>
                                        <td>
                                            <span class="show-status">
                                                No shows for this day
                                            </span>
                                        </td>
                                    </tr>
                                % endif
                            </tbody>
                        </table>
                    % endfor
                </div>
            </div>
            </div>
            % endif
        </div>
    </div>
</%block>