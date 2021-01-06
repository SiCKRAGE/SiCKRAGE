<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import calendar
    import unidecode
    import datetime
    from functools import cmp_to_key

    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.helpers import srdatetime, pretty_file_size
    from sickrage.core.media.util import series_image, SeriesImageType
    from sickrage.core.enums import HomeLayout, PosterSortBy, PosterSortDirection
%>

<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col text-left">
            <div class="form-inline m-2">
                % if sickrage.app.config.gui.home_layout == HomeLayout.POSTER:
                    <div class="px-1">
                        <select id="postersort" class="form-control bg-secondary text-white-50" style="border: none;">
                            <option value="${PosterSortBy.NAME.name}"
                                    data-sort="${srWebRoot}/setPosterSortBy/?sort=${PosterSortBy.NAME.name}" ${('', 'selected')[sickrage.app.config.gui.poster_sort_by == PosterSortBy.NAME]}>
                                ${PosterSortBy.NAME.display_name}
                            </option>
                        </select>
                    </div>

                    <div class="px-1">
                        <select id="postersortdirection" class="form-control bg-secondary text-white-50"
                                style="border: none;">
                            <option value="${PosterSortDirection.ASCENDING.name}"
                                    data-sort="${srWebRoot}/setPosterSortDir/?direction=${PosterSortDirection.ASCENDING.name}" ${('', 'selected')[sickrage.app.config.gui.poster_sort_dir == PosterSortDirection.ASCENDING]}>
                                ${PosterSortDirection.ASCENDING.display_name}
                            </option>
                            <option value="${PosterSortDirection.DESCENDING.name}"
                                    data-sort="${srWebRoot}/setPosterSortDir/?direction=${PosterSortDirection.DESCENDING.name}" ${('', 'selected')[sickrage.app.config.gui.poster_sort_dir == PosterSortDirection.DESCENDING]}>
                                ${PosterSortDirection.DESCENDING.display_name}
                            </option>
                        </select>
                    </div>
                % endif
            </div>
        </div>
        <div class="col text-right">
            <div class="form-inline d-inline-flex">
                % if sickrage.app.config.gui.home_layout != HomeLayout.POSTER:
                    <div class="dropdown ml-4">
                        <button id="popover" type="button" class="btn bg-transparent dropdown-toggle"
                                style="border: none;">
                            <i class="fas fa-2x fa-columns"></i>
                        </button>
                    </div>
                % endif
                % if sickrage.app.config.gui.home_layout == HomeLayout.POSTER:
                    <div style="width: 100px" id="posterSizeSlider"></div>
                % endif
                <div class="dropdown ml-4">
                    <a type="button" class="btn bg-transparent dropdown-toggle" href="#" data-toggle="dropdown" style="border: none;">
                        % if sickrage.app.config.gui.home_layout == HomeLayout.POSTER:
                            <i class="fas fa-2x fa-th-large"></i>
                        % elif sickrage.app.config.gui.home_layout == HomeLayout.SMALL:
                            <i class="fas fa-2x fa-th"></i>
                        % elif sickrage.app.config.gui.home_layout == HomeLayout.BANNER:
                            <i class="fas fa-2x fa-image"></i>
                        % elif sickrage.app.config.gui.home_layout == HomeLayout.DETAILED:
                            <i class="fas fa-2x fa-list"></i>
                        % elif sickrage.app.config.gui.home_layout == HomeLayout.SIMPLE:
                            <i class="fas fa-2x fa-list"></i>
                        % endif
                    </a>
                    <div class="dropdown-menu dropdown-menu-right">
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=${HomeLayout.POSTER.name}">Poster</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=${HomeLayout.SMALL.name}">Small Poster</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=${HomeLayout.BANNER.name}">Banner</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=${HomeLayout.DETAILED.name}">Detailed</a>
                        <a class="dropdown-item" href="${srWebRoot}/setHomeLayout/?layout=${HomeLayout.SIMPLE.name}">Simple</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>

<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>

    % if sickrage.app.loading_shows:
        <div class="text-center">
            ... LoAdInG ShOwS ...
        </div>
    % else:
        % for curListType, curShowlist in showlists.items():
            % if curListType == "Anime" and len(curShowlist):
                <div class="row">
                    <div class="col mx-auto">
                        <div class="h4 card" style="text-align: center;">${_('Anime List')}</div>
                    </div>
                </div>
            % endif
            % if sickrage.app.config.gui.home_layout == HomeLayout.POSTER:
                <div id="${('container', 'container-anime')[curListType == 'Anime' and sickrage.app.config.gui.home_layout == HomeLayout.POSTER]}"
                     class="show-grid clearfix mx-auto d-none">
                    <div class="posterview">
                        % for curShow in curShowlist:
                            <div class="show-container" id="show${curShow.series_id}" data-name="${curShow.name}">
                                <div class="card card-block text-white bg-dark m-1 shadow">
                                    <a href="${srWebRoot}/home/displayShow?show=${curShow.series_id}">
                                        <img alt="" class="card-img-top"
                                             src="${srWebRoot}${series_image(curShow.series_id, curShow.series_provider_id, SeriesImageType.POSTER).url}"/>
                                    </a>
                                    <div class="card-header bg-dark py-0 px-0">
                                        % if sickrage.app.show_queue.is_being_added(curShow.series_id):
                                            <div class="bg-dark progress shadow rounded-0"></div>
                                        % else:
                                            <div class="bg-dark progress shadow rounded-0">
                                                <div class="progress-bar d-print-none"
                                                     data-show-id="${curShow.series_id}">
                                                </div>
                                            </div>
                                        % endif
                                    </div>
                                    <div class="card-body text-truncate py-1 px-1 small">
                                        <div class="show-title">
                                            ${curShow.name}
                                        </div>
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
                                    % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                        <th>${_('Next Ep')}</th>
                                        <th>${_('Prev Ep')}</th>
                                    % endif
                                    <th>${_('Show')}</th>
                                    % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                        <th>${_('Network')}</th>
                                        <th>${_('Quality')}</th>
                                        <th>${_('Downloads')}</th>
                                        <th>${_('Size')}</th>
                                        <th>${_('Active')}</th>
                                    % endif
                                    <th>${_('Status')}</th>
                                </tr>
                                </thead>

                                <tbody class="">
                                    % for curShow in curShowlist:
                                        % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                            <%
                                                cur_airs_next = curShow.airs_next
                                                cur_airs_prev = curShow.airs_prev
                                                show_size = curShow.total_size

                                                network_class_name = None
                                                if curShow.network:
                                                    network_class_name = re.sub(r'(?!\w|\s).', '', unidecode.unidecode(curShow.network))
                                                    network_class_name = re.sub(r'\s+', '-', network_class_name)
                                                    network_class_name = re.sub(r'^(\s*)([\W\w]*)(\b\s*$)', '\\2', network_class_name)
                                                    network_class_name = network_class_name.lower()
                                            %>
                                        % endif
                                        <tr>
                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                % if cur_airs_next > datetime.date.min:
                                                <% airDate = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, curShow.airs, curShow.network), convert=True).dt %>
                                                % try:
                                                    <td class="table-fit align-middle">
                                                        <time datetime="${airDate.isoformat()}"
                                                              class="date">${srdatetime.SRDateTime(airDate).srfdate()}</time>
                                                    </td>
                                                % except ValueError:
                                                    <td class="table-fit"></td>
                                                % endtry
                                                % else:
                                                    <td class="table-fit"></td>
                                                % endif
                                            % endif

                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                % if cur_airs_prev > datetime.date.min:
                                                <% airDate = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_prev, curShow.airs, curShow.network), convert=True).dt %>
                                                % try:
                                                    <td class="table-fit align-middle">
                                                        <time datetime="${airDate.isoformat()}" class="date">
                                                            ${srdatetime.SRDateTime(airDate).srfdate()}
                                                        </time>
                                                    </td>
                                                % except ValueError:
                                                    <td class="table-fit"></td>
                                                % endtry
                                                % else:
                                                    <td class="table-fit"></td>
                                                % endif
                                            % endif

                                            % if sickrage.app.config.gui.home_layout == HomeLayout.SMALL:
                                                <td class="tvShow">
                                                    <a href="${srWebRoot}/home/displayShow?show=${curShow.series_id}"
                                                       title="${curShow.name}">
                                                        <img src="${srWebRoot}${series_image(curShow.series_id, curShow.series_provider_id, SeriesImageType.POSTER_THUMB).url}"
                                                             class="img-smallposter rounded shadow"
                                                             alt="${curShow.series_id}"/>
                                                        ${curShow.name}
                                                    </a>
                                                </td>
                                            % elif sickrage.app.config.gui.home_layout == HomeLayout.BANNER:
                                                <td class="table-fit tvShow">
                                                    <span class="d-none">${curShow.name}</span>
                                                    <a href="${srWebRoot}/home/displayShow?show=${curShow.series_id}">
                                                        <img src="${srWebRoot}${series_image(curShow.series_id, curShow.series_provider_id, SeriesImageType.BANNER).url}"
                                                             class="img-banner rounded shadow"
                                                             alt="${curShow.series_id}"
                                                             title="${curShow.name}"/>
                                                    </a>
                                                </td>
                                            % elif sickrage.app.config.gui.home_layout in [HomeLayout.DETAILED, HomeLayout.SIMPLE]:
                                                <td class="tvShow">
                                                    <a href="${srWebRoot}/home/displayShow?show=${curShow.series_id}">
                                                        ${curShow.name}
                                                    </a>
                                                </td>
                                            % endif

                                            % if sickrage.app.config.gui.home_layout not in [HomeLayout.DETAILED, HomeLayout.SIMPLE]:
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
                                            % elif sickrage.app.config.gui.home_layout == HomeLayout.DETAILED:
                                                <td class="table-fit">
                                                    <span title="${curShow.network}">${curShow.network}</span>
                                                </td>
                                            % endif

                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                <td class="table-fit align-middle">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                                            % endif

                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                <td class="align-middle">
                                                    % if sickrage.app.show_queue.is_being_added(curShow.series_id):
                                                        <div class="bg-dark progress shadow"></div>
                                                    % else:
                                                        <div class="bg-dark progress shadow">
                                                            <div class="progress-bar d-print-none"
                                                                 data-show-id="${curShow.series_id}">
                                                            </div>
                                                        </div>
                                                    % endif
                                                </td>
                                            % endif

                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                <td class="table-fit align-middle" data-show-size="${show_size}">
                                                    ${pretty_file_size(show_size)}
                                                </td>
                                            % endif

                                            % if sickrage.app.config.gui.home_layout != HomeLayout.SIMPLE:
                                                <td class="table-fit align-middle">
                                                    <i class="fa ${("fa-times text-danger", "fa-check text-success")[not bool(curShow.paused)]}"></i>
                                                    <span class="d-none d-print-inline">${('No', 'Yes')[not bool(curShow.paused)]}</span>
                                                </td>
                                            % endif

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
    % endif
</%block>
