<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime

    import sickrage
    from sickrage.core.helpers import anon_url, srdatetime
    from sickrage.core.media.util import indexerImage
%>

<%block name="metas">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.app.config.sort_article}">
</%block>
<%block name="content">
    <div class="row bg-dark mb-3 px-4">
        <div class="col text-left">
            <div class="form-inline m-2">
                <span>${_('Sort By:')}</span>
                <select id="showsort" class="form-control form-control-inline input-sm">
                    <option value="name">${_('Name')}</option>
                    <option value="original" selected>${_('Original')}</option>
                    <option value="votes">${_('Votes')}</option>
                    <option value="rating">${_('% Rating')}</option>
                    <option value="rating_votes">${_('% Rating > Votes')}</option>
                </select>

                <span style="margin-left:12px">${_('Sort Order:')}</span>
                <select id="showsortdirection" class="form-control form-control-inline input-sm">
                    <option value="asc" selected>${_('Asc')}</option>
                    <option value="desc">${_('Desc')}</option>
                </select>

                <span style="margin-left:12px">${_('Select Trakt List:')}</span>
                <select id="traktlist" class="form-control form-control-inline input-sm"
                        title="Trakt List Selection">
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

                <span style="margin-left:12px">${_('Limit:')}</span>
                <select id="limit" class="form-control form-control-inline input-sm">
                    <option value="10" ${('', ' selected')[limit == "10"]}>10</option>
                    <option value="25" ${('', ' selected')[limit == "25"]}>25</option>
                    <option value="50" ${('', ' selected')[limit == "50"]}>50</option>
                    <option value="100" ${('', ' selected')[limit == "100"]}>100</option>
                </select>
            </div>
        </div>
        <div class="col text-right">
            <div class="form-inline m-1 d-inline-flex">
                <div style="width: 100px" id="posterSizeSlider"></div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-8 mx-auto">
            <div class="sickrage-card m-1">
                <div class="sickrage-card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    % if not trakt_shows:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">${_('Trakt API did not return any results, please check your config.')}
                        </div>
                    % else:
                        <div class="loading-spinner text-center">
                            <i class="fas fa-10x fa-spinner fa-spin fa-fw"></i>
                        </div>
                        <div class="show-grid mx-auto d-none">
                            % for cur_show in trakt_shows:
                            <% indexer_id = cur_show.ids['tvdb'] %>
                            <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show.ids['slug'] %>
                                <div class="show-container" data-name="${cur_show.title}"
                                     data-rating="${cur_show.rating.value}" data-votes="${cur_show.votes}">
                                    <div class="card card-block text-white bg-dark m-1 shadow">
                                        <div class="card-header p-0">
                                            <a href="${anon_url(show_url)}" target="_blank">
                                                <img class="card-img-top trakt-image" src="" data-image-loaded=""
                                                     data-indexerid="${indexer_id}"/>
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
                                            <a href="${srWebRoot}/home/addShows/addShowByID/?indexer_id=${indexer_id}&showName=${cur_show.title}"
                                               class="sickrage-btn btn-sm" data-no-redirect>${_('Add Show')}</a>
                                            % if black_list:
                                                <a href="${srWebRoot}/addShows/addShowToBlacklist?indexer_id=${indexer_id}"
                                                   class="sickrage-btn btn-sm">${_('Remove Show')}</a>
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