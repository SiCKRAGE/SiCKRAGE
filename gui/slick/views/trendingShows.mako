<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import datetime
    import re
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
    from sickbeard import sbdatetime
    from sickbeard.helpers import anon_url
%>
<%block name="metas">
<meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
</%block>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/trendingShows.js"></script>
</%block>
<%block name="content">
<div id="container">
% if not trending_shows:
    <div class="trakt_show" style="width:100%; margin-top:20px">
        <p class="red-text">Trakt API did not return any results, please check your config.
    </div>
% else:
% for cur_show in trending_shows:
    <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show[b'show'][b'ids'][b'slug'] %>

    <div class="trakt_show" data-name="${cur_show[b'show'][b'title']}" data-rating="${cur_show[b'show'][b'rating']}" data-votes="${cur_show[b'show'][b'votes']}">
        <div class="traktContainer">
            <div class="trakt-image">
                <a class="trakt-image" href="${anon_url(show_url)}" target="_blank"><img alt="" class="trakt-image" src="${cur_show[b'show'][b'images'][b'poster'][b'thumb']}" /></a>
            </div>

            <div class="show-title">
                ${(cur_show[b'show'][b'title'], '<span>&nbsp;</span>')['' == cur_show[b'show'][b'title']]}
            </div>

        <div class="clearfix">
            <p>${int(cur_show[b'show'][b'rating']*10)}% <img src="${srRoot}/images/heart.png"></p>
            <i>${cur_show[b'show'][b'votes']} votes</i>
            <div class="traktShowTitleIcons">
                <a href="${srRoot}/home/addShows/addTraktShow?indexer_id=${cur_show[b'show'][b'ids'][b'tvdb']}&amp;showName=${cur_show[b'show'][b'title']}" class="btn btn-xs">Add Show</a>
                % if blacklist:
                <a href="${srRoot}/home/addShows/addShowToBlacklist?indexer_id=${cur_show[b'show'][b'ids'][b'tvdb'] or cur_show[b'show'][b'ids'][b'tvrage']}" class="btn btn-xs">Remove Show</a>
                % endif
            </div>
        </div>
        </div>
    </div>
% endfor
% endif
</div>
</%block>
