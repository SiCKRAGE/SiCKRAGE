<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime

    import sickrage
    from sickrage.core.helpers import anon_url, srdatetime
    from sickrage.core.media.util import indexerImage
%>

<%block name="metas">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.srCore.srConfig.SORT_ARTICLE}">
</%block>
<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="text-center">
                <span>Sort By:</span>
                <select id="showsort" class="form-control form-control-inline input-sm">
                    <option value="name">Name</option>
                    <option value="original" selected>Original</option>
                    <option value="votes">Votes</option>
                    <option value="rating">% Rating</option>
                    <option value="rating_votes">% Rating > Votes</option>
                </select>

                <span style="margin-left:12px">Sort Order:</span>
                <select id="showsortdirection" class="form-control form-control-inline input-sm">
                    <option value="asc" selected>Asc</option>
                    <option value="desc">Desc</option>
                </select>

                <span style="margin-left:12px">Select Trakt List:</span>
                <select id="traktlist" class="form-control form-control-inline input-sm" title="Trakt List Selection">
                    <option value="anticipated" ${('', ' selected')[trakt_list == "anticipated"]}>
                        Most Anticipated
                    </option>
                    <option value="trending" ${('', ' selected')[trakt_list == "trending"]}>
                        Trending
                    </option>
                    <option value="popular" ${('', ' selected')[trakt_list == "popular"]}>
                        Popular
                    </option>
                    <option value="watched" ${('', ' selected')[trakt_list == "watched"]}>
                        Most Watched
                    </option>
                    <option value="played" ${('', ' selected')[trakt_list == "played"]}>
                        Most Played
                    </option>
                    <option value="collected" ${('', ' selected')[trakt_list == "collected"]}>
                        Most Collected
                    </option>
                </select>
            </div>
        </div>
    </div>


    <div class="clearfix"></div>
    <div id="container">
        % if not trakt_shows:
            <div class="trakt_show" style="width:100%; margin-top:20px">
                <p class="red-text">Trakt API did not return any results, please check your config.}
            </div>
        % else:
            % for cur_show in trakt_shows:
            <% indexer_id = cur_show.ids['tvdb'] %>
            <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show.ids['slug'] %>

                <div class="trakt_show" data-name="${cur_show.title}"
                     data-rating="${cur_show.rating.value}" data-votes="${cur_show.votes}">
                    <div class="traktContainer">
                        <div class="trakt-image">
                            <a class="trakt-image" href="${anon_url(show_url)}" target="_blank">
                                <img alt="" class="trakt-image" src="" data-image-loaded=""
                                     data-indexerid="${indexer_id}"
                                     height="273px" width="186px"/>
                            </a>
                        </div>

                        <div class="show-title">
                            ${(cur_show.title, '<span>&nbsp;</span>')['' == cur_show.title]}
                        </div>

                        <div class="clearfix">
                            <p>${int(cur_show.rating.value*10)}% <span class="fa fa-heart red-text"></span></p>
                            <i>${cur_show.votes} votes</i>
                            <div class="traktShowTitleIcons">
                                <a href="${srWebRoot}/home/addShows/addShowByID/?indexer_id=${indexer_id}&showName=${cur_show.title}"
                                   class="btn btn-xs" data-no-redirect>Add Show</a>
                                % if black_list:
                                    <a href="${srWebRoot}/addShows/addShowToBlacklist?indexer_id=${indexer_id}"
                                       class="btn btn-xs">Remove Show</a>
                                % endif
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        % endif
    </div>
</%block>