<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import calendar
    import unidecode
    from functools import cmp_to_key

    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.helpers import srdatetime, pretty_filesize
    from sickrage.core.media.util import showImage
%>
<%block name="metas">
    <meta data-var="max_download_count" data-content="${max_download_count}">
</%block>

<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col text-left">
            <div class="form-inline m-2">
                % if sickrage.app.config.home_layout == 'poster':
                    <div class="px-1">
                        <select id="postersort" class="form-control bg-secondary text-white-50"
                                style="border: none;">
                            <option value="name"
                                    data-sort="${srWebRoot}/setPosterSortBy/?sort=name" ${('', 'selected')[sickrage.app.config.poster_sortby == 'name']}>
                                ${_('Name')}
                            </option>
                            <option value="date"
                                    data-sort="${srWebRoot}/setPosterSortBy/?sort=date" ${('', 'selected')[sickrage.app.config.poster_sortby == 'date']}>
                                ${_('Next Episode')}
                            </option>
                            <option value="network"
                                    data-sort="${srWebRoot}/setPosterSortBy/?sort=network" ${('', 'selected')[sickrage.app.config.poster_sortby == 'network']}>
                                ${_('Network')}
                            </option>
                            <option value="progress"
                                    data-sort="${srWebRoot}/setPosterSortBy/?sort=progress" ${('', 'selected')[sickrage.app.config.poster_sortby == 'progress']}>
                                ${_('Progress')}
                            </option>
                        </select>
                    </div>

                    <div class="px-1">
                        <select id="postersortdirection" class="form-control bg-secondary text-white-50"
                                style="border: none;">
                            <option value="true"
                                    data-sort="${srWebRoot}/setPosterSortDir/?direction=1" ${('', 'selected')[sickrage.app.config.poster_sortdir == 1]}>
                                ${_('Asc')}
                            </option>
                            <option value="false"
                                    data-sort="${srWebRoot}/setPosterSortDir/?direction=0" ${('', 'selected')[sickrage.app.config.poster_sortdir == 0]}>
                                ${_('Desc')}
                            </option>
                        </select>
                    </div>
                % endif
            </div>
        </div>
        <div class="col text-right">
            <div class="form-inline d-inline-flex">
                % if sickrage.app.config.home_layout != 'poster':
                    <div class="dropdown ml-4">
                        <button id="popover" type="button" class="btn bg-transparent dropdown-toggle"
                                style="border: none;">
                            <i class="fas fa-2x fa-columns"></i>
                        </button>
                    </div>
                % endif
                % if sickrage.app.config.home_layout == 'poster':
                    <div style="width: 100px" id="posterSizeSlider"></div>
                % endif
                <div class="dropdown ml-4">
                    <button type="button" class="btn bg-transparent dropdown-toggle" data-toggle="dropdown"
                            style="border: none;">
                        % if sickrage.app.config.home_layout == 'poster':
                            <i class="fas fa-2x fa-th-large"></i>
                        % elif sickrage.app.config.home_layout == 'small':
                            <i class="fas fa-2x fa-th"></i>
                        % elif sickrage.app.config.home_layout == 'banner':
                            <i class="fas fa-2x fa-image"></i>
                        % elif sickrage.app.config.home_layout == 'simple':
                            <i class="fas fa-2x fa-th-list"></i>
                        % endif
                    </button>
                    <div class="dropdown-menu dropdown-menu-right">
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=poster">Poster</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=small">Small Poster</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=banner">Banner</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=simple">Simple</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>

<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
    % for curListType, curShowlist in showlists.items():
        % if curListType == "Anime":
            <div class="row">
                <div class="col mx-auto">
                    <div class="h4 card" style="text-align: center;">${_('Anime List')}</div>
                </div>
            </div>
        % endif
        % if sickrage.app.config.home_layout == 'poster':
            <div id="${('container', 'container-anime')[curListType == 'Anime' and sickrage.app.config.home_layout == 'poster']}"
                 class="show-grid clearfix mx-auto">
                <div class="posterview">
                    % for curLoadingShow in sickrage.app.show_queue.loading_show_list:
                        % if not curLoadingShow.show:
                            <div class="show-container" data-name="0" data-date="010101" data-network="0"
                                 data-progress="101">
                                <div class="card card-block text-white bg-dark m-1 shadow">
                                    <img alt="" title="${curLoadingShow.name}" class="card-img-top"
                                         src="${srWebRoot}/images/poster.png"/>
                                    <div class="card-body text-truncate py-1 px-1 small">
                                        <div class="show-title">
                                            ${curLoadingShow.name}
                                        </div>
                                    </div>
                                    <div class="card-footer show-details p-1">
                                        <div class="show-details">
                                            <div class="show-add text-center">${_('... Loading ...')}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        % endif
                    % endfor

                    % for curShow in sorted(curShowlist, key=cmp_to_key(lambda x, y: x.name < y.name)):
                    <%
                        cur_airs_next = ''
                        cur_snatched = 0
                        cur_downloaded = 0
                        cur_total = 0
                        download_stat_tip = ''
                        display_status = curShow.status

                        if display_status:
                            if re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
                                display_status = _('Continuing')
                            elif re.search(r'(?i)(?:nded)', curShow.status):
                                display_status = _('Ended')

                        if curShow.indexer_id in show_stat:
                            cur_airs_next = show_stat[curShow.indexer_id]['ep_airs_next']

                            cur_snatched = show_stat[curShow.indexer_id]['ep_snatched']
                            if not cur_snatched:
                                cur_snatched = 0

                            cur_downloaded = show_stat[curShow.indexer_id]['ep_downloaded']
                            if not cur_downloaded:
                                cur_downloaded = 0

                            cur_total = show_stat[curShow.indexer_id]['ep_total']
                            if not cur_total:
                                cur_total = 0

                        if cur_total != 0:
                            download_stat = str(cur_downloaded)
                            download_stat_tip = _("Downloaded: ") + str(cur_downloaded)
                            if cur_snatched > 0:
                                download_stat = download_stat
                                download_stat_tip = download_stat_tip + " " + _("Snatched: ") + str(cur_snatched)

                            download_stat = download_stat + " / " + str(cur_total)
                            download_stat_tip = download_stat_tip + " " + _("Total: ") + str(cur_total)
                        else:
                            download_stat = '?'
                            download_stat_tip = _("no data")

                        nom = cur_downloaded
                        den = cur_total
                        if den == 0:
                            den = 1

                        progressbar_percent = nom * 100 / den

                        data_date = '6000000000.0'
                        if cur_airs_next:
                            data_date = calendar.timegm(srdatetime.srDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network), convert=True).dt.timetuple())
                        elif display_status:
                            if 'nded' not in display_status and 1 == int(curShow.paused):
                                data_date = '5000000500.0'
                            elif 'ontinu' in display_status:
                                data_date = '5000000000.0'
                            elif 'nded' in display_status:
                                data_date = '5000000100.0'

                        network_class_name = None
                        if curShow.network:
                            network_class_name = re.sub(r'(?!\w|\s).', '', unidecode.unidecode(curShow.network))
                            network_class_name = re.sub(r'\s+', '-', network_class_name)
                            network_class_name = re.sub(r'^(\s*)([\W\w]*)(\b\s*$)', '\\2', network_class_name)
                            network_class_name = network_class_name.lower()
                    %>
                        <div class="show-container" id="show${curShow.indexer_id}" data-name="${curShow.name}"
                             data-date="${data_date}" data-network="${curShow.network}"
                             data-progress="${progressbar_percent}">
                            <div class="card card-block text-white bg-dark m-1 shadow">
                                <a href="${srWebRoot}/home/displayShow?show=${curShow.indexer_id}">
                                    <img alt="" class="card-img-top"
                                         src="${srWebRoot}${showImage(curShow.indexer_id, 'poster').url}"/>
                                </a>
                                <div class="card-header py-0 px-0">
                                    <div class="bg-dark rounded">
                                        <div class="progress progress-bar rounded d-print-none" role="progressbar"
                                             style="width: ${progressbar_percent}%;height: 5px;"
                                             data-progress-percentage="${progressbar_percent}"
                                             data-show-id="${curShow.indexer_id}">
                                        </div>
                                    </div>
                                    <div>
                                        <span class="d-block small show-dlstats badge"
                                              title="${download_stat_tip}">
                                            ${download_stat}
                                        </span>
                                    </div>
                                </div>
                                <div class="card-body text-truncate py-1 px-1 small">
                                    <div class="show-title">
                                        ${curShow.name}
                                    </div>

                                    <div class="show-date" style="color: grey">
                                        % if cur_airs_next:
                                            <% ldatetime = srdatetime.srDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network), convert=True).dt %>
                                            <%
                                                try:
                                                  out = srdatetime.srDateTime(ldatetime).srfdate()
                                                except ValueError:
                                                  out = _('Invalid date')
                                            %>
                                        % else:
                                            <% display_status = curShow.status %>
                                            <%
                                                out = 'UNKNOWN'
                                                if display_status:
                                                  out = display_status
                                                  if 'nded' not in display_status and 1 == int(curShow.paused):
                                                      out = _('Paused')
                                            %>
                                        % endif
                                      ${out}
                                    </div>
                                </div>
                                <div class="card-footer show-details p-1">
                                    <table class="show-details w-100" style="height:40px">
                                        <tr>
                                            <td class="text-left align-middle w-25">
                                                % if curShow.network:
                                                    <span>
                                                        <i class="show-network-image sickrage-network sickrage-network-${network_class_name}"
                                                           title="${curShow.network}"></i>
                                                    </span>
                                                % else:
                                                    <span>
                                                        <i class="show-network-image sickrage-network sickrage-network-unknown"
                                                           title="${_('No Network')}"></i>
                                                    </span>
                                                % endif
                                            </td>
                                            <td class="text-right align-middle w-25">
                                                ${renderQualityPill(curShow.quality, showTitle=True)}
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    % endfor
                </div>
            </div>
        % else:
            <div class="row">
                <div class="col-lg-10 mx-auto">
                    <div class="table-responsive">
                        <table class="table" id="showListTable${curListType}">
                            <thead class="thead-dark">
                            <tr>
                                <th>${_('Next Ep')}</th>
                                <th>${_('Prev Ep')}</th>
                                <th>${_('Show')}</th>
                                <th>${_('Network')}</th>
                                <th>${_('Quality')}</th>
                                <th>${_('Downloads')}</th>
                                <th>${_('Size')}</th>
                                <th>${_('Active')}</th>
                                <th>${_('Status')}</th>
                            </tr>
                            </thead>

                            % if sickrage.app.show_queue.loading_show_list:
                                <tbody>
                                    % for curLoadingShow in sickrage.app.show_queue.loading_show_list:
                                        % if not curLoadingShow.show or curLoadingShow.show not in get_show_list():
                                            <tr>
                                                <td class="table-fit">(${_('loading')})</td>
                                                <td></td>
                                                <td>
                                                    % if curLoadingShow.show is None:
                                                        <span title="">${_('Loading...')} ${curLoadingShow.name}</span>
                                                    % else:
                                                        <a data-fancybox
                                                           href="displayShow?show=${curLoadingShow.show.indexer_id}">${curLoadingShow.show.name}</a>
                                                    % endif
                                                </td>
                                                <td></td>
                                                <td></td>
                                                <td></td>
                                                <td></td>
                                                <td></td>
                                            </tr>
                                        % endif
                                    % endfor
                                </tbody>
                            % endif

                            <tbody class="">
                                % for curShow in sorted(curShowlist, key=cmp_to_key(lambda x, y: x.name < y.name)):
                                    <%
                                        cur_airs_next = ''
                                        cur_airs_prev = ''
                                        cur_snatched = 0
                                        cur_downloaded = 0
                                        cur_total = 0
                                        show_size = 0
                                        download_stat_tip = ''

                                        if curShow.indexer_id in show_stat:
                                            cur_airs_next = show_stat[curShow.indexer_id]['ep_airs_next']
                                            cur_airs_prev = show_stat[curShow.indexer_id]['ep_airs_prev']

                                            cur_snatched = show_stat[curShow.indexer_id]['ep_snatched']
                                            if not cur_snatched:
                                                cur_snatched = 0

                                            cur_downloaded = show_stat[curShow.indexer_id]['ep_downloaded']
                                            if not cur_downloaded:
                                                cur_downloaded = 0

                                            cur_total = show_stat[curShow.indexer_id]['ep_total']
                                            if not cur_total:
                                                cur_total = 0

                                            show_size = show_stat[curShow.indexer_id]['total_size']

                                        if cur_total != 0:
                                            download_stat = str(cur_downloaded)
                                            download_stat_tip = _("Downloaded: ") + str(cur_downloaded)
                                            if cur_snatched > 0:
                                                download_stat = download_stat + "+" + str(cur_snatched)
                                                download_stat_tip = download_stat_tip + "&#013;" + _("Snatched: ") + str(cur_snatched)

                                            download_stat = download_stat + " / " + str(cur_total)
                                            download_stat_tip = download_stat_tip + "&#013;" + _("Total: ") + str(cur_total)
                                        else:
                                            download_stat = '?'
                                            download_stat_tip = _("no data")

                                        nom = cur_downloaded
                                        den = cur_total
                                        if den == 0:
                                            den = 1

                                        progressbar_percent = nom * 100 / den

                                        network_class_name = None
                                        if curShow.network:
                                            network_class_name = re.sub(r'(?!\w|\s).', '', unidecode.unidecode(curShow.network))
                                            network_class_name = re.sub(r'\s+', '-', network_class_name)
                                            network_class_name = re.sub(r'^(\s*)([\W\w]*)(\b\s*$)', '\\2', network_class_name)
                                            network_class_name = network_class_name.lower()
                                    %>
                                    <tr>
                                        % if cur_airs_next:
                                        <% airDate = srdatetime.srDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network), convert=True).dt %>
                                        % try:
                                            <td class="table-fit align-middle">
                                                <time datetime="${airDate.isoformat()}"
                                                      class="date">${srdatetime.srDateTime(airDate).srfdate()}</time>
                                            </td>
                                        % except ValueError:
                                            <td class="table-fit"></td>
                                        % endtry
                                        % else:
                                            <td class="table-fit"></td>
                                        % endif

                                        % if cur_airs_prev:
                                        <% airDate = srdatetime.srDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_prev, curShow.airs, curShow.network), convert=True).dt %>
                                        % try:
                                            <td class="table-fit align-middle">
                                                <time datetime="${airDate.isoformat()}" class="date">
                                                    ${srdatetime.srDateTime(airDate).srfdate()}
                                                </time>
                                            </td>
                                        % except ValueError:
                                            <td class="table-fit"></td>
                                        % endtry
                                        % else:
                                            <td class="table-fit"></td>
                                        % endif

                                        % if sickrage.app.config.home_layout == 'small':
                                            <td class="tvShow">
                                                <a href="${srWebRoot}/home/displayShow?show=${curShow.indexer_id}"
                                                   title="${curShow.name}">
                                                    <img src="${srWebRoot}${showImage(curShow.indexer_id, 'poster_thumb').url}"
                                                         class="img-smallposter rounded shadow"
                                                         alt="${curShow.indexer_id}"/>
                                                    ${curShow.name}
                                                </a>
                                            </td>
                                        % elif sickrage.app.config.home_layout == 'banner':
                                            <td class="table-fit tvShow">
                                                <span class="d-none">${curShow.name}</span>
                                                <a href="${srWebRoot}/home/displayShow?show=${curShow.indexer_id}">
                                                    <img src="${srWebRoot}${showImage(curShow.indexer_id, 'banner').url}"
                                                         class="img-banner rounded shadow" alt="${curShow.indexer_id}"
                                                         title="${curShow.name}"/>
                                                </a>
                                            </td>
                                        % elif sickrage.app.config.home_layout == 'simple':
                                            <td class="tvShow">
                                                <a href="${srWebRoot}/home/displayShow?show=${curShow.indexer_id}">
                                                    ${curShow.name}
                                                </a>
                                            </td>
                                        % endif

                                        % if sickrage.app.config.home_layout != 'simple':
                                            <td class="table-fit align-middle">
                                                % if curShow.network:
                                                    <span title="${curShow.network}">
                                                        <i class="sickrage-network sickrage-network-${network_class_name}"></i>
                                                    </span>
                                                    <span class="d-none d-print-inline">${curShow.network}</span>
                                                % else:
                                                    <span title="${_('No Network')}">
                                                        <i class="sickrage-network sickrage-network-unknown"></i>
                                                    </span>
                                                    <span class="d-none d-print-inline">No Network</span>
                                                % endif
                                            </td>
                                        % else:
                                            <td class="table-fit">
                                                <span title="${curShow.network}">${curShow.network}</span>
                                            </td>
                                        % endif

                                        <td class="table-fit align-middle">${renderQualityPill(curShow.quality, showTitle=True)}</td>

                                        <td class="align-middle">
                                            <span style="display: none;">${download_stat}</span>
                                            <div class="bg-dark rounded shadow">
                                                <div class="progress-bar rounded "
                                                     style="width: ${progressbar_percent}%"
                                                     data-show-id="${curShow.indexer_id}"
                                                     data-progress-percentage="${progressbar_percent}"
                                                     data-progress-text="${download_stat}"
                                                     data-progress-tip="${download_stat_tip}"></div>
                                            </div>
                                        </td>

                                        <td class="table-fit align-middle" data-show-size="${show_size}">
                                            ${pretty_filesize(show_size)}
                                        </td>

                                        <td class="table-fit align-middle">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[not bool(curShow.paused)]}"></i>
                                            <span class="d-none d-print-inline">${('No', 'Yes')[not bool(curShow.paused)]}</span>
                                        </td>

                                        <td class="table-fit align-middle">
                                            % if curShow.status and re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
                                                ${_('Continuing')}
                                            % elif curShow.status and re.search('(?i)(?:nded)', curShow.status):
                                                ${_('Ended')}
                                            % else:
                                                ${curShow.status}
                                            % endif
                                        </td>
                                    </tr>
                                % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        % endif
    % endfor
</%block>
