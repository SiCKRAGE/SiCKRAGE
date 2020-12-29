<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime

    import sickrage
    from sickrage.core.helpers import anon_url, srdatetime
    from sickrage.core.media.util import series_provider_image, SeriesImageType
    from sickrage.core.enums import SeriesProviderID
%>

<%block name="metas">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.app.config.general.sort_article}">
</%block>

<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col text-left">
            <div class="form-inline m-2">
                <select id="showsort" class="form-control form-control-inline m-1" title="${_('Sort By')}">
                    <option value="name">${_('Name')}</option>
                    <option value="original" selected>${_('Original')}</option>
                    <option value="votes">${_('Votes')}</option>
                    <option value="rating">${_('% Rating')}</option>
                    <option value="rating_votes">${_('% Rating > Votes')}</option>
                </select>

                <select id="showsortdirection" class="form-control form-control-inline m-1" title="${_('Sort Order')}">
                    <option value="asc" selected>${_('Asc')}</option>
                    <option value="desc">${_('Desc')}</option>
                </select>

                <select id="traktlist" class="form-control form-control-inline m-1" title="${_('Trakt List Selection')}">
                    <option value="anticipated" ${('', ' selected')[trakt_list == "anticipated"]}>
                        ${_('Most Anticipated')}
                    </option>
                    <option value="trending" ${('', ' selected')[trakt_list == "trending"]}>
                        ${_('Trending')}
                    </option>
                    <option value="popular" ${('', ' selected')[trakt_list == "popular"]}>
                        ${_('Popular')}
                    </option>
                    <option value="watched" ${('', ' selected')[trakt_list == "watched"]}>
                        ${_('Most Watched')}
                    </option>
                    <option value="played" ${('', ' selected')[trakt_list == "played"]}>
                        ${_('Most Played')}
                    </option>
                    <option value="collected" ${('', ' selected')[trakt_list == "collected"]}>
                        ${_('Most Collected')}
                    </option>
                </select>

                <select id="limit" class="form-control form-control-inline m-1" title="${_('Limit')}">
                    <option value="10" ${('', ' selected')[limit == "10"]}>10</option>
                    <option value="25" ${('', ' selected')[limit == "25"]}>25</option>
                    <option value="50" ${('', ' selected')[limit == "50"]}>50</option>
                    <option value="100" ${('', ' selected')[limit == "100"]}>100</option>
                </select>
            </div>
        </div>
        <div class="text-right pr-3">
            <div class="form-inline d-inline m-1">
                <div style="width: 100px" id="posterSizeSlider"></div>
            </div>
        </div>
    </div>
</%block>

<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    % if not trakt_shows:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">${_('Trakt API did not return any results, please check your config.')}
                        </div>
                    % else:
                        <div class="show-grid mx-auto">
                            % for cur_show in trakt_shows:
                            <% series_id = cur_show.ids['tvdb'] %>
                            <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show.ids['slug'] %>
                                <div class="show-container" data-name="${cur_show.title}"
                                     data-rating="${cur_show.rating.value}" data-votes="${cur_show.votes}">
                                    <div class="card card-block text-white bg-dark m-1 shadow">
                                        <div class="card-header p-0">
                                            <a href="${anon_url(show_url)}" target="_blank">
                                                <img class="card-img-top"
                                                     src="${srWebRoot}${series_provider_image(series_id=series_id, series_provider_id=SeriesProviderID.THETVDB, which=SeriesImageType.POSTER_THUMB).url}"/>
                                            </a>
                                        </div>
                                        <div class="card-body text-truncate py-1 px-1 small">
                                            <div class="show-title">
                                                ${(cur_show.title, '<span>&nbsp;</span>')['' == cur_show.title]}
                                            </div>
                                            <div class="show-votes">
                                                ${cur_show.votes} <i class="fas fa-thumbs-up text-success"></i>
                                            </div>
                                            <div class="show-ratings">
                                                ${int(cur_show.rating.value*10)}% <i class="fas fa-heart text-danger"></i>
                                            </div>
                                        </div>
                                        <div class="card-footer show-details p-1">
                                            <a href="${srWebRoot}/home/addShows/addShowByID/?series_id=${series_id}&showName=${cur_show.title}"
                                               class="btn btn-sm" data-no-redirect>${_('Add Show')}</a>
                                            % if black_list:
                                                <a href="${srWebRoot}/addShows/addShowToBlacklist?series_id=${series_id}"
                                                   class="btn btn-sm">${_('Remove Show')}</a>
                                            % endif
                                        </div>
                                    </div>
                                </div>
                            % endfor
                        </div>
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>