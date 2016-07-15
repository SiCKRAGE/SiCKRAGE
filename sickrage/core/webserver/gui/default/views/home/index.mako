<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import calendar

    import sickrage
    from sickrage.core.helpers import srdatetime
    from sickrage.core.updaters import tz_updater
    from sickrage.core.media.util import showImage
%>
<%block name="metas">
    <meta data-var="max_download_count" data-content="${max_download_count}">
</%block>
<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>

    <div class="h2footer pull-right">
        % if sickrage.srCore.srConfig.HOME_LAYOUT != 'poster':
            <button id="popover" type="button" class="btn btn-inline">Select Columns <b class="caret"></b></button>
        % endif

        % if sickrage.srCore.srConfig.HOME_LAYOUT == 'poster':
            <span class="badge" style="background-color: #333333;">Sort By:
                <select id="postersort" class="form-control form-control-inline input-sm">
                    <option value="name"
                            data-sort="/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTBY == 'name']}>
                        Name
                    </option>
                    <option value="date"
                            data-sort="/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTBY == 'date']}>
                        Next Episode
                    </option>
                    <option value="network"
                            data-sort="/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTBY == 'network']}>
                        Network
                    </option>
                    <option value="progress"
                            data-sort="/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTBY == 'progress']}>
                        Progress
                    </option>
                </select>
            </span>

            <span class="badge" style="background-color: #333333;">Sort Order:
                <select id="postersortdirection" class="form-control form-control-inline input-sm">
                    <option value="true"
                            data-sort="/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTDIR == 1]}>
                        Asc
                    </option>
                    <option value="false"
                            data-sort="/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[sickrage.srCore.srConfig.POSTER_SORTDIR == 0]}>
                        Desc
                    </option>
                </select>
            </span>
        % endif

        <span class="badge" style="background-color: #333333;">Layout:
            <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
                <option value="/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[sickrage.srCore.srConfig.HOME_LAYOUT == 'poster']}>
                    Poster
                </option>
                <option value="/setHomeLayout/?layout=small" ${('', 'selected="selected"')[sickrage.srCore.srConfig.HOME_LAYOUT == 'small']}>
                    Small Poster
                </option>
                <option value="/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[sickrage.srCore.srConfig.HOME_LAYOUT == 'banner']}>
                    Banner
                </option>
                <option value="/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[sickrage.srCore.srConfig.HOME_LAYOUT == 'simple']}>
                    Simple
                </option>
            </select>
        </span>
    </div>

    % if sickrage.srCore.srConfig.HOME_LAYOUT != 'poster':
        <div class="pull-right">
            <span>
                <input class="form-control form-control-inline input-sm input200" type="search" data-column="2" placeholder="Search Show Name">
                <button type="button" class="resetsorting btn btn-inline">Reset Search</button>
            </span>
        </div>
    % endif

    % for curShowlist in showlists:
        <% curListType = curShowlist[0] %>
        <% myShowList = list(curShowlist[1]) %>
        % if curListType == "Anime":
            <h1 class="header">Anime List</h1>
        % endif
        % if sickrage.srCore.srConfig.HOME_LAYOUT == 'poster':
            <div id="${('container', 'container-anime')[curListType == 'Anime' and sickrage.srCore.srConfig.HOME_LAYOUT == 'poster']}" class="clearfix">
                <div class="posterview">
                    % for curLoadingShow in sickrage.srCore.SHOWQUEUE.loadingShowList:
                        % if not curLoadingShow.show:
                            <div class="show" data-name="0" data-date="010101" data-network="0" data-progress="101">
                                <img alt="" title="${curLoadingShow.show_name}" class="show-image"
                                     style="border-bottom: 1px solid #111;" src="/images/poster.png"/>
                                <div class="show-details">
                                    <div class="show-add">Loading... (${curLoadingShow.show_name})</div>
                                </div>
                            </div>

                        % endif
                    % endfor

                    <% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
                    % for curShow in myShowList:
                        <%
                            cur_airs_next = ''
                            cur_snatched = 0
                            cur_downloaded = 0
                            cur_total = 0
                            download_stat_tip = ''
                            display_status = curShow.status

                            if display_status:
                                if re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
                                    display_status = 'Continuing'
                                elif re.search(r'(?i)(?:nded)', curShow.status):
                                    display_status = 'Ended'

                            if curShow.indexerid in show_stat:
                                cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']

                                cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
                                if not cur_snatched:
                                    cur_snatched = 0

                                cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
                                if not cur_downloaded:
                                    cur_downloaded = 0

                                cur_total = show_stat[curShow.indexerid]['ep_total']
                                if not cur_total:
                                    cur_total = 0

                            if cur_total != 0:
                                download_stat = str(cur_downloaded)
                                download_stat_tip = "Downloaded: " + str(cur_downloaded)
                                if cur_snatched > 0:
                                    download_stat = download_stat
                                    download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

                                download_stat = download_stat + " / " + str(cur_total)
                                download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
                            else:
                                download_stat = '?'
                                download_stat_tip = "no data"

                            nom = cur_downloaded
                            den = cur_total
                            if den == 0:
                                den = 1

                            progressbar_percent = nom * 100 / den

                            data_date = '6000000000.0'
                            if cur_airs_next:
                                data_date = calendar.timegm(srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network)).timetuple())
                            elif display_status:
                                if 'nded' not in display_status and 1 == int(curShow.paused):
                                    data_date = '5000000500.0'
                                elif 'ontinu' in display_status:
                                    data_date = '5000000000.0'
                                elif 'nded' in display_status:
                                    data_date = '5000000100.0'
                        %>
                        <div class="show" id="show${curShow.indexerid}" data-name="${curShow.name}" data-date="${data_date}" data-network="${curShow.network}" data-progress="${progressbar_percent}">
                            <div class="show-image">
                                <a href="/home/displayShow?show=${curShow.indexerid}"><img alt="" class="show-image" src="${showImage(curShow.indexerid, 'poster_thumb')}" /></a>
                            </div>

                            <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}"></div>

                            <div class="show-title">
                                ${curShow.name}
                            </div>

                            <div class="show-date">
                                % if cur_airs_next:
                                    <% ldatetime = srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
                                    <%
                                        try:
                                            out = srdatetime.srDateTime.srfdate(ldatetime)
                                        except ValueError:
                                            out = 'Invalid date'
                                            pass
                                    %>
                                        ${out}
                                % else:
                                    <%
                                    output_html = '?'
                                    display_status = curShow.status
                                    if display_status:
                                        if 'nded' not in display_status and 1 == int(curShow.paused):
                                          output_html = 'Paused'
                                        elif display_status:
                                            output_html = display_status
                                    %>
                                    ${output_html}
                                % endif
                            </div>

                            <table width="100%" cellspacing="1" border="0" cellpadding="0">
                                <tr>
                                    <td class="show-table">
                                        <span class="show-dlstats" title="${download_stat_tip}">${download_stat}</span>
                                    </td>

                                    <td class="show-table">
                                        % if sickrage.srCore.srConfig.HOME_LAYOUT != 'simple':
                                            % if curShow.network:
                                                <span title="${curShow.network}"><img class="show-network-image" src="${showImage(curShow.indexerid, 'network')}" alt="${curShow.network}" title="${curShow.network}" /></span>
                                            % else:
                                                <span title="No Network"><img class="show-network-image" src="/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                                            % endif
                                        % else:
                                            <span title="${curShow.network}">${curShow.network}</span>
                                        % endif
                                    </td>

                                    <td class="show-table">
                                        ${renderQualityPill(curShow.quality, showTitle=True, overrideClass="show-quality")}
                                    </td>
                                </tr>
                            </table>
                        </div>
                    % endfor
                </div>
            </div>
        % else:
            <br><br>
            <table id="showListTable${curListType}" class="sickrageTable tablesorter" cellspacing="1" border="0" cellpadding="0">
                <thead>
                    <tr>
                        <th class="nowrap">Next Ep</th>
                        <th class="nowrap">Prev Ep</th>
                        <th>Show</th>
                        <th>Network</th>
                        <th>Quality</th>
                        <th>Downloads</th>
                        <th>Active</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tfoot class="hidden-print">
                    <tr>
                        <th rowspan="1" colspan="1" align="center"><a href="/home/addShows/">Add ${('Show', 'Anime')[curListType == 'Anime']}</a></th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                        <th>&nbsp;</th>
                    </tr>
                </tfoot>

                % if sickrage.srCore.SHOWQUEUE.loadingShowList:
                    <tbody class="tablesorter-infoOnly">
                        % for curLoadingShow in sickrage.srCore.SHOWQUEUE.loadingShowList:
                            % if curLoadingShow.show is not None and curLoadingShow.show in sickrage.srCore.SHOWLIST:
                                continue
                            % endif

                            <tr>
                                <td align="center">(loading)</td>
                                <td></td>
                                <td>
                                    % if curLoadingShow.show is None:
                                        <span title="">Loading... (${curLoadingShow.show_name})</span>
                                    % else:
                                        <a href="displayShow?show=${curLoadingShow.show.indexerid}">${curLoadingShow.show.name}</a>
                                    % endif
                                </td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                        % endfor
                    </tbody>
                % endif

                <tbody>
                    <% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
                    % for curShow in myShowList:
                        <%
                            cur_airs_next = ''
                            cur_airs_prev = ''
                            cur_snatched = 0
                            cur_downloaded = 0
                            cur_total = 0
                            download_stat_tip = ''

                            if curShow.indexerid in show_stat:
                                cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']
                                cur_airs_prev = show_stat[curShow.indexerid]['ep_airs_prev']

                                cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
                                if not cur_snatched:
                                    cur_snatched = 0

                                cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
                                if not cur_downloaded:
                                    cur_downloaded = 0

                                cur_total = show_stat[curShow.indexerid]['ep_total']
                                if not cur_total:
                                    cur_total = 0

                            if cur_total != 0:
                                download_stat = str(cur_downloaded)
                                download_stat_tip = "Downloaded: " + str(cur_downloaded)
                                if cur_snatched > 0:
                                    download_stat = download_stat + "+" + str(cur_snatched)
                                    download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

                                download_stat = download_stat + " / " + str(cur_total)
                                download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
                            else:
                                download_stat = '?'
                                download_stat_tip = "no data"

                            nom = cur_downloaded
                            den = cur_total
                            if den == 0:
                                den = 1

                            progressbar_percent = nom * 100 / den
                        %>
                        <tr>
                            % if cur_airs_next:
                                <% airDate = srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
                                % try:
                                    <td align="center" class="nowrap">
                                        <time datetime="${airDate.isoformat()}" class="date">${srdatetime.srDateTime.srfdate(airDate)}</time>
                                    </td>
                                % except ValueError:
                                    <td align="center" class="nowrap"></td>
                                % endtry
                            % else:
                                <td align="center" class="nowrap"></td>
                            % endif

                            % if cur_airs_prev:
                                <% airDate = srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(cur_airs_prev, curShow.airs, curShow.network)) %>
                                % try:
                                    <td align="center" class="nowrap">
                                        <time datetime="${airDate.isoformat()}" class="date">${srdatetime.srDateTime.srfdate(airDate)}</time>
                                    </td>
                                % except ValueError:
                                    <td align="center" class="nowrap"></td>
                                % endtry
                            % else:
                                <td align="center" class="nowrap"></td>
                            % endif

                            % if sickrage.srCore.srConfig.HOME_LAYOUT == 'small':
                                <td class="tvShow">
                                    <div class="imgsmallposter ${sickrage.srCore.srConfig.HOME_LAYOUT}">
                                        <a href="/home/displayShow?show=${curShow.indexerid}" title="${curShow.name}">
                                            <img src="${showImage(curShow.indexerid, 'poster_thumb')}" class="${sickrage.srCore.srConfig.HOME_LAYOUT}"
                                                 alt="${curShow.indexerid}"/>
                                        </a>
                                        <a href="/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
                                    </div>
                                </td>
                            % elif sickrage.srCore.srConfig.HOME_LAYOUT == 'banner':
                                <td>
                                    <span style="display: none;">${curShow.name}</span>
                                    <div class="imgbanner ${sickrage.srCore.srConfig.HOME_LAYOUT}">
                                        <a href="/home/displayShow?show=${curShow.indexerid}">
                                            <img src="${showImage(curShow.indexerid, 'banner')}" class="${sickrage.srCore.srConfig.HOME_LAYOUT}"
                                                 alt="${curShow.indexerid}" title="${curShow.name}"/>
                                        </a>
                                    </div>
                                </td>
                            % elif sickrage.srCore.srConfig.HOME_LAYOUT == 'simple':
                                <td class="tvShow"><a href="/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                            % endif

                            % if sickrage.srCore.srConfig.HOME_LAYOUT != 'simple':
                                <td align="center">
                                    % if curShow.network:
                                        <span title="${curShow.network}" class="hidden-print"><img id="network" width="54" height="27" src="${showImage(curShow.indexerid, 'network')}" alt="${curShow.network}" title="${curShow.network}" /></span>
                                        <span class="visible-print-inline">${curShow.network}</span>
                                    % else:
                                        <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                                        <span class="visible-print-inline">No Network</span>
                                    % endif
                                </td>
                            % else:
                                <td>
                                    <span title="${curShow.network}">${curShow.network}</span>
                                </td>
                            % endif

                            <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>

                            <td align="center">
                                <span style="display: none;">${download_stat}</span>
                                <div class="progressbar hidden-print" style="position:relative" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}" data-progress-text="${download_stat}" data-progress-tip="${download_stat_tip}"></div>
                                ## <span class="visible-print-inline">${download_stat}</span>
                            </td>

                            <td align="center">
                                <% paused = int(curShow.paused) == 0 and curShow.status == 'Continuing' %>
                                <img src="/images/${('no16.png', 'yes16.png')[bool(paused)]}" alt="${('No', 'Yes')[bool(paused)]}" width="16" height="16" />
                            </td>

                            <td align="center">
                                <% display_status = curShow.status %>
                                % if display_status and re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
                                        <% display_status = 'Continuing' %>
                                % elif display_status and re.search('(?i)(?:nded)', curShow.status):
                                        <% display_status = 'Ended' %>
                                % endif
                                ${display_status}
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        % endif
    % endfor
</%block>
