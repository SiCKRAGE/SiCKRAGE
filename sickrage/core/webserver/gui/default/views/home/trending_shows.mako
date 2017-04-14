<%inherit file="../layouts/main.mako"/>
<%!
    import re
    import datetime

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings
    from sickrage.core.helpers import anon_url, srdatetime
%>
<%block name="metas">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.srCore.srConfig.SORT_ARTICLE}">
</%block>
<%block name="content">
    <div id="container">
        % if not trending_shows:
            <div class="trakt_show" style="width:100%; margin-top:20px">
                <p class="red-text">Trakt API did not return any results, please check your config settings.
            </div>
        % else:
            % for cur_show in trending_shows:
            <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show['show']['ids']['slug'] %>
                <div class="trakt_show" data-name="${cur_show['show']['title']}"
                     data-rating="${cur_show['show']['rating']}" data-votes="${cur_show['show']['votes']}">
                    <div class="traktContainer">
                        <div class="trakt-image">
                            <a class="trakt-image" href="${anon_url(show_url)}" target="_blank">
                                <img alt="" class="trakt-image" src="${cur_show['show']['images']['poster']['thumb']}"/>
                            </a>
                        </div>

                        <div class="show-title">
                            ${(cur_show['show']['title'], '<span>&nbsp;</span>')['' == cur_show['show']['title']]}
                        </div>

                        <div class="clearfix">
                            <p>${int(cur_show['show']['rating']*10)}% <img src="${parent.web_root()}/images/heart.png"></p>
                            <i>${cur_show['show']['votes']} votes</i>
                            <div class="traktShowTitleIcons">
                                <a href="${parent.web_root()}/home/addShows/addTraktShow?indexer_id=${cur_show['show']['ids']['tvdb']}&amp;showName=${cur_show['show']['title']}"
                                   class="btn btn-xs">Add Show</a>
                                % if blacklist:
                                    <a href="${parent.web_root()}/home/addShows/addShowToBlacklist?indexer_id=${cur_show['show']['ids']['tvdb'] or cur_show['show']['ids']['tvrage']}"
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
