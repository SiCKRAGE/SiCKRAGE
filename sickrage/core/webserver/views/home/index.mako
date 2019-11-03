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
    <%include file="../includes/loading.mako"/>
    % if sickrage.app.config.home_layout == 'poster':
        <div id="container" class="show-grid clearfix mx-auto d-none"></div>
    % else:
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <table class="table d-none" id="showListTableShows">
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
                    <tbody></tbody>
                </table>
            </div>
        </div>
    % endif
</%block>
