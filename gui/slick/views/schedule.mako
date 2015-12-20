<%inherit file="/layouts/main.mako"/>
<%!
    import re
    import time
    import datetime

    import sickbeard
    from sickbeard.helpers import anon_url
    from sickbeard import sbdatetime
    from sickrage.media import showImage
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/ajaxEpSearch.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/schedule.js"></script>
</%block>
<%block name="css">
<style type="text/css">
#SubMenu {display:none;}
#contentWrapper {padding-top:30px;}
</style>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
<h1 class="header">${header}</h1>
<div class="h2footer pull-right">
% if layout == 'list':
    <button id="popover" type="button" class="btn btn-inline">Select Columns <b class="caret"></b></button>
% else:
    <span>Sort By:
        <select name="sort" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${srRoot}/setScheduleSort/?sort=date" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'date']} >Date</option>
            <option value="${srRoot}/setScheduleSort/?sort=network" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'network']} >Network</option>
            <option value="${srRoot}/setScheduleSort/?sort=show" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'show']} >Show</option>
        </select>
    </span>
% endif
    &nbsp;

    <span>View Paused:
        <select name="viewpaused" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${srRoot}/toggleScheduleDisplayPaused" ${('', 'selected="selected"')[not bool(sickbeard.COMING_EPS_DISPLAY_PAUSED)]}>Hidden</option>
            <option value="${srRoot}/toggleScheduleDisplayPaused" ${('', 'selected="selected"')[bool(sickbeard.COMING_EPS_DISPLAY_PAUSED)]}>Shown</option>
        </select>
    </span>
    &nbsp;

    <span>Layout:
        <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${srRoot}/setScheduleLayout/?layout=poster" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'poster']} >Poster</option>
            <option value="${srRoot}/setScheduleLayout/?layout=calendar" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'calendar']} >Calendar</option>
            <option value="${srRoot}/setScheduleLayout/?layout=banner" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'banner']} >Banner</option>
            <option value="${srRoot}/setScheduleLayout/?layout=list" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'list']} >List</option>
        </select>
    </span>
</div>

<div class="key pull-right">
% if 'calendar' != layout:
    <b>Key:</b>
    <span class="listing-key listing-overdue">Missed</span>
    <span class="listing-key listing-current">Today</span>
    <span class="listing-key listing-default">Soon</span>
    <span class="listing-key listing-toofar">Later</span>
% endif
    <a class="btn btn-inline forceBacklog" href="webcal://${sbHost}:${sbHttpPort}/calendar">
    <i class="icon-calendar icon-white"></i>Subscribe</a>
</div>

<br>

% if 'list' == layout:
<!-- start list view //-->
<% show_div = 'listing-default' %>

<input type="hidden" id="srRoot" value="${srRoot}" />

<table id="showListTable" class="sickbeardTable tablesorter seasonstyle" cellspacing="1" border="0" cellpadding="0">

    <thead>
        <tr>
            <th>Airdate (${('local', 'network')[sickbeard.TIMEZONE_DISPLAY == 'network']})</th>
            <th>Ends</th>
            <th>Show</th>
            <th>Next Ep</th>
            <th>Next Ep Name</th>
            <th>Network</th>
            <th>Run time</th>
            <th>Quality</th>
            <th>Indexers</th>
            <th>Search</th>
        </tr>
    </thead>

    <tbody style="text-shadow:none;">

% for cur_result in results:
<%
    cur_indexer = int(cur_result[b'indexer'])
    run_time = cur_result[b'runtime']

    if int(cur_result[b'paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
        continue

    cur_ep_airdate = cur_result[b'localtime'].date()

    if run_time:
        cur_ep_enddate = cur_result[b'localtime'] + datetime.timedelta(minutes = run_time)
        if cur_ep_enddate < today:
            show_div = 'listing-overdue'
        elif cur_ep_airdate >= next_week.date():
            show_div = 'listing-toofar'
        elif cur_ep_airdate >= today.date() and cur_ep_airdate < next_week.date():
            if cur_ep_airdate == today.date():
                show_div = 'listing-current'
            else:
                show_div = 'listing-default'
%>

        <tr class="${show_div}">
            <td align="center" nowrap="nowrap">
                <% airDate = sbdatetime.sbdatetime.convert_to_setting(cur_result[b'localtime']) %>
                <time datetime="${airDate.isoformat()}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
            </td>

            <td align="center" nowrap="nowrap">
                <% ends = sbdatetime.sbdatetime.convert_to_setting(cur_ep_enddate) %>
                <time datetime="${ends.isoformat()}" class="date">${sbdatetime.sbdatetime.sbfdatetime(ends)}</time>
            </td>

            <td class="tvShow" nowrap="nowrap"><a href="${srRoot}/home/displayShow?show=${cur_result[b'showid']}">${cur_result[b'show_name']}</a>
% if int(cur_result[b'paused']):
                <span class="pause">[paused]</span>
% endif
            </td>

            <td nowrap="nowrap" align="center">
                ${'S%02iE%02i' % (int(cur_result[b'season']), int(cur_result[b'episode']))}
            </td>

            <td>
% if cur_result[b'description']:
                <img alt="" src="${srRoot}/images/info32.png" height="16" width="16" class="plotInfo" id="plot_info_${'%s_%s_%s' % (cur_result[b'showid'], cur_result[b'season'], cur_result[b'episode'])}" />
% else:
                <img alt="" src="${srRoot}/images/info32.png" width="16" height="16" class="plotInfoNone"  />
% endif
                ${cur_result[b'name']}
            </td>

            <td align="center">
                ${cur_result[b'network']}
            </td>

            <td align="center">
            ${run_time}min
            </td>

            <td align="center">
                ${renderQualityPill(cur_result[b'quality'], showTitle=True)}
            </td>

            <td align="center" style="vertical-align: middle;">
                % if cur_result[b'imdb_id']:
                    <a href="${anon_url('http://www.imdb.com/title/', cur_result[b'imdb_id'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="http://www.imdb.com/title/${cur_result[b'imdb_id']}"><img alt="[imdb]" height="16" width="16" src="${srRoot}/images/imdb.png" /></a>
                % endif
                <a href="${anon_url(sickbeard.indexerApi(cur_indexer).config[b'show_url'], cur_result[b'showid'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="${sickbeard.indexerApi(cur_indexer).config[b'show_url']}${cur_result[b'showid']}">
                    <img alt="${sickbeard.indexerApi(cur_indexer).name}" height="16" width="16" src="${srRoot}/images/${sickbeard.indexerApi(cur_indexer).config[b'icon']}" />
                </a>
            </td>

            <td align="center">
                <a href="${srRoot}/home/searchEpisode?show=${cur_result[b'showid']}&amp;season=${cur_result[b'season']}&amp;episode=${cur_result[b'episode']}" title="Manual Search" id="forceUpdate-${cur_result[b'showid']}x${cur_result[b'season']}x${cur_result[b'episode']}" class="forceUpdate epSearch">
                    <img alt="[search]" height="16" width="16" src="${srRoot}/images/search16.png" id="forceUpdateImage-${cur_result[b'showid']}" />
                </a>
            </td>
        </tr>
% endfor
    </tbody>

    <tfoot>
        <tr>
            <th rowspan="1" colspan="10" align="center">&nbsp</th>
        </tr>
    </tfoot>

</table>
<!-- end list view //-->


% elif layout in ['banner', 'poster']:
    <!-- start non list view //-->
    <%
        cur_segment = None
        too_late_header = False
        missed_header = False
        today_header = False
        show_div = 'ep_listing listing-default'
    %>
% if sickbeard.COMING_EPS_SORT == 'show':
    <br><br>
% endif

% for cur_result in results:
    <%
        cur_indexer = int(cur_result[b'indexer'])

        if int(cur_result[b'paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
            continue

        run_time = cur_result[b'runtime']
        cur_ep_airdate = cur_result[b'localtime'].date()

        if run_time:
            cur_ep_enddate = cur_result[b'localtime'] + datetime.timedelta(minutes = run_time)
        else:
            cur_ep_enddate = cur_result[b'localtime']
    %>
    % if sickbeard.COMING_EPS_SORT == 'network':
        <% show_network = ('no network', cur_result[b'network'])[bool(cur_result[b'network'])] %>
        % if cur_segment != show_network:
            <div>
               <br><h2 class="network">${show_network}</h2>

            <% cur_segment = cur_result[b'network'] %>
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

    % elif sickbeard.COMING_EPS_SORT == 'date':
        % if cur_segment != cur_ep_airdate:
            % if cur_ep_enddate < today and cur_ep_airdate != today.date() and not missed_header:
                <br><h2 class="day">Missed</h2>
                <% missed_header = True %>
            % elif cur_ep_airdate >= next_week.date() and not too_late_header:
                <br><h2 class="day">Later</h2>
                <% too_late_header = True %>
            % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                % if cur_ep_airdate == today.date():
                    <br><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}<span style="font-size: 14px; vertical-align: top;">[Today]</span></h2>
                    <% today_header = True %>
                % else:
                    <br><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}</h2>
                % endif
            % endif
            <% cur_segment = cur_ep_airdate %>
        % endif

        % if cur_ep_airdate == today.date() and not today_header:
            <div>
            <br><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()} <span style="font-size: 14px; vertical-align: top;">[Today]</span></h2>
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

    % elif sickbeard.COMING_EPS_SORT == 'show':
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

<div class="${show_div}" id="listing-${cur_result[b'showid']}">
    <div class="tvshowDiv">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <th ${('class="nobg"', 'rowspan="2"')['banner' == layout]} valign="top">
                <a href="${srRoot}/home/displayShow?show=${cur_result[b'showid']}">
                    <img alt="" class="${('posterThumb', 'bannerThumb')[layout == 'banner']}" src="${showImage(cur_result[b'showid'], (layout, 'poster_thumb')[layout == 'poster'])}" />
                </a>
            </th>
% if 'banner' == layout:
        </tr>
        <tr>
% endif
            <td class="next_episode">
                <div class="clearfix">
                    <span class="tvshowTitle">
                        <a href="${srRoot}/home/displayShow?show=${cur_result[b'showid']}">${cur_result[b'show_name']}
                            ${('', '<span class="pause">[paused]</span>')[int(cur_result[b'paused'])]}
                        </a>
                    </span>

                    <span class="tvshowTitleIcons">
                        % if cur_result[b'imdb_id']:
                            <a href="${anon_url('http://www.imdb.com/title/', cur_result[b'imdb_id'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="http://www.imdb.com/title/${cur_result[b'imdb_id']}"><img alt="[imdb]" height="16" width="16" src="${srRoot}/images/imdb.png" /></a>
                        % endif
                        <a href="${anon_url(sickbeard.indexerApi(cur_indexer).config[b'show_url'], cur_result[b'showid'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="${sickbeard.indexerApi(cur_indexer).config[b'show_url']}"><img alt="${sickbeard.indexerApi(cur_indexer).name}" height="16" width="16" src="${srRoot}/images/${sickbeard.indexerApi(cur_indexer).config[b'icon']}" /></a>
                        <span><a href="${srRoot}/home/searchEpisode?show=${cur_result[b'showid']}&amp;season=${cur_result[b'season']}&amp;episode=${cur_result[b'episode']}" title="Manual Search" id="forceUpdate-${cur_result[b'showid']}" class="epSearch forceUpdate"><img alt="[search]" height="16" width="16" src="${srRoot}/images/search16.png" id="forceUpdateImage-${cur_result[b'showid']}" /></a></span>
                    </span>
                </div>

                <span class="title">Next Episode:</span> <span>${'S%02iE%02i' % (int(cur_result[b'season']), int(cur_result[b'episode']))} - ${cur_result[b'name']}</span>

                <div class="clearfix">
                    <span class="title">Airs: </span><span class="airdate">${sbdatetime.sbdatetime.sbfdatetime(cur_result[b'localtime'])}</span>${('', '<span> on %s</span>' % cur_result[b'network'])[bool(cur_result[b'network'])]}
                </div>

                <div class="clearfix">
                    <span class="title">Quality:</span>
                    ${renderQualityPill(cur_result[b'quality'], showTitle=True)}
                </div>
            </td>
        </tr>
        <tr>
            <td style="vertical-align: top;">
                <div>
                    % if cur_result[b'description']:
                        <span class="title" style="vertical-align:middle;">Plot:</span>
                        <img class="ep_summaryTrigger" src="${srRoot}/images/plus.png" height="16" width="16" alt="" title="Toggle Summary" /><div class="ep_summary">${cur_result[b'description']}</div>
                    % else:
                        <span class="title ep_summaryTriggerNone" style="vertical-align:middle;">Plot:</span>
                        <img class="ep_summaryTriggerNone" src="${srRoot}/images/plus.png" height="16" width="16" alt="" />
                    % endif
                </div>
            </td>
        </tr>
        </table>
    </div>
</div>

<!-- end ${cur_result[b'show_name']} //-->
% endfor

<!-- end non list view //-->
% endif

% if 'calendar' == layout:
<% dates = [today.date() + datetime.timedelta(days = i) for i in range(7)] %>
<% tbl_day = 0 %>
<br>
<br>
<div class="calendarWrapper">
<input type="hidden" id="srRoot" value="${srRoot}" />
    % for day in dates:
    <% tbl_day += 1 %>
        <table class="sickbeardTable tablesorter calendarTable ${'cal-%s' % (('even', 'odd')[bool(tbl_day % 2)])}" cellspacing="0" border="0" cellpadding="0">
        <thead><tr><th>${day.strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}</th></tr></thead>
        <tbody>
        <% day_has_show = False %>
        % for cur_result in results:
            % if int(cur_result[b'paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
                <% continue %>
            % endif

            <% cur_indexer = int(cur_result[b'indexer']) %>
            <% run_time = cur_result[b'runtime'] %>
            <% airday = cur_result[b'localtime'].date() %>

            % if airday == day:
                % try:
                    <% day_has_show = True %>
                    <% airtime = sbdatetime.sbdatetime.fromtimestamp(time.mktime(cur_result[b'localtime'].timetuple())).sbftime().decode(sickbeard.SYS_ENCODING) %>
                    % if sickbeard.TRIM_ZERO:
                        <% airtime = re.sub(r'0(\d:\d\d)', r'\1', airtime, 0, re.IGNORECASE | re.MULTILINE) %>
                    % endif
                % except OverflowError:
                    <% airtime = "Invalid" %>
                % endtry

                <tr>
                    <td class="calendarShow">
                        <div class="poster">
                            <a title="${cur_result[b'show_name']}" href="${srRoot}/home/displayShow?show=${cur_result[b'showid']}"><img alt="" src="${srRoot}${showImage(cur_result[b'showid'], 'poster_thumb')}" /></a>
                        </div>
                        <div class="text">
                            <span class="airtime">
                                ${airtime} on ${cur_result["network"]}
                            </span>
                            <span class="episode-title" title="${cur_result[b'name']}">
                                ${'S%02iE%02i' % (int(cur_result[b'season']), int(cur_result[b'episode']))} - ${cur_result[b'name']}
                            </span>
                        </div>
                    </td> <!-- end ${cur_result[b'show_name']} -->
                </tr>
            % endif

        % endfor
        % if not day_has_show:
            <tr><td class="calendarShow"><span class="show-status">No shows for this day</span></td></tr>
        % endif
        </tbody>
        </table>
    % endfor

<!-- end calender view //-->
</div>
% endif

<div class="clearfix"></div>
</%block>