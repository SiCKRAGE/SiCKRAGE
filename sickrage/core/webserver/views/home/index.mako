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
    from sickrage.core.media.util import showImage
%>
## <%block name="metas">
##     <meta data-var="max_download_count" data-content="${overall_stats['episodes']['total'] * 100}">
## </%block>

<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col text-left">
            <div class="form-inline m-2">
                % if sickrage.app.config.home_layout == 'poster':
                    <div class="px-1">
                        <select id="postersort" class="form-control bg-secondary text-white-50" style="border: none;">
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
    <% loading_show_list_ids = [] %>

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
                % for curLoadingShow in sickrage.app.show_queue.loading_show_list:
                <% loading_show_list_ids.append(curLoadingShow['indexer_id']) %>
                    <div class="show-container" data-name="0" data-date="010101" data-network="0"
                         data-progress="101">
                        <div class="card card-block text-white bg-dark m-1 shadow">
                            <img alt="" title="${curLoadingShow['name']}" class="card-img-top"
                                 src="${srWebRoot}/images/poster.png"/>
                            <div class="card-body text-truncate py-1 px-1 small">
                                <div class="show-title">
                                    ${curLoadingShow['name']}
                                </div>
                            </div>
                            <div class="card-footer show-details p-1">
                                <div class="show-details">
                                    <div class="show-add text-center">${_('... Loading ...')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                % endfor
            </div>
            <div class="show-grid-loading-status text-center m-3">
                <i class="fas fa-spinner fa-spin fa-fw fa-10x"></i>
            </div>
        % else:
            <div class="row">
                <div class="col-lg-10 mx-auto">
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
                                    <% loading_show_list_ids.append(curLoadingShow['indexer_id']) %>
                                    <tr>
                                        <td class="table-fit">(${_('loading')})</td>
                                        <td></td>
                                        <td>
                                            <a data-fancybox
                                               href="displayShow?show=${curLoadingShow['indexer_id']}">${curLoadingShow['name']}</a>
                                        </td>
                                        <td></td>
                                        <td></td>
                                        <td></td>
                                        <td></td>
                                        <td></td>
                                    </tr>
                                % endfor
                            </tbody>
                        % endif
                        <tbody>
                        <tr class="show-list-loading-status">
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                            <td>
                                <i class="fas fa-spinner fa-spin fa-fw"></i>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        % endif
    % endfor
</%block>
