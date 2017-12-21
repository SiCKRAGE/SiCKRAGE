<%inherit file="../layouts/main.mako"/>
<%!
    import os
    import datetime
    import urllib
    import ntpath

    import sickrage
    import sickrage.subtitles
    from sickrage.core.updaters import tz_updater
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, FAILED, DOWNLOADED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, Overview
    from sickrage.core.helpers import anon_url, srdatetime, pretty_filesize, get_size
    from sickrage.core.media.util import showImage
    from sickrage.indexers import IndexerApi
%>
<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
    <%namespace file="../includes/modals.mako" import="displayShowModals"/>
    <div class="row">
        <div class="col-md-12">
            <div class="row">
                <div class="col-md-12">
                    <h1 class="title" id="showtitle" data-showname="${show.name}">
                        <div class="input-group input350 input-group-sm">
                            <div class="input-group-addon">
                                <a href="#" id="prevShow" class="glyphicon glyphicon-arrow-left"></a>
                            </div>
                            <select id="pickShow" class="form-control form-control-inline" title="Change Show">
                                % for curShowList in sortedShowLists:
                                    % if len(sortedShowLists) > 1:
                                        <optgroup label="${curShowList[0]}">
                                    % endif
                                    % for curShow in curShowList[1]:
                                        <option value="${curShow.indexerid}" ${('', 'selected')[curShow == show]}>${curShow.name}</option>
                                    % endfor
                                    % if len(sortedShowLists) > 1:
                                        </optgroup>
                                    % endif
                                % endfor
                            </select>
                            <div class="input-group-addon">
                                <a href="#" id="nextShow" class="glyphicon glyphicon-arrow-right"></a>
                            </div>
                        </div>
                        <br/>
                        ${show.name}
                    </h1>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    % if seasonResults:
                    % if int(seasonResults[-1]) == 0:
                        <% season_special = 1 %>
                    % else:
                        <% season_special = 0 %>
                    % endif
                    % if not sickrage.app.config.display_show_specials and season_special:
                        <% lastSeason = seasonResults.pop(-1) %>
                    % endif
                        <span class="h2footer pull-right">
                            % if season_special:
                            ${_('Display Specials:')}
                                <a class="inner"
                                   href="${srWebRoot}/toggleDisplayShowSpecials/?show=${show.indexerid}">${('Show', 'Hide')[bool(sickrage.app.config.display_show_specials)]}</a>
                            % endif
                        </span>
                        <div class="h2footer pull-right">
                            <span>
                                % if (len(seasonResults) > 14):
                                    <select id="seasonJump" class="form-control input-sm" title="Jump to Season"
                                            style="position: relative; top: -4px;">
                                        <option value="jump">Jump to Season</option>
                                        % for seasonNum in seasonResults:
                                            <option value="#season-${seasonNum}"
                                                    data-season="${seasonNum}">${('Specials', 'Season ' + str(seasonNum))[int(seasonNum) > 0]}</option>
                                        % endfor
                                    </select>
                                % else:
                                    ${_('Season:')}
                                    % for seasonNum in seasonResults:
                                        % if int(seasonNum) == 0:
                                            <a href="#season-${seasonNum}">Specials</a>
                                        % else:
                                            <a href="#season-${seasonNum}">${str(seasonNum)}</a>
                                        % endif
                                        % if seasonNum != seasonResults[-1]:
                                            <span class="separator">|</span>
                                        % endif
                                    % endfor
                                % endif
                            </span>
                        </div>
                    % endif
                </div>
            </div>
            <!-- Alert -->
            % if show_message:
                <div class="row">
                    <div class="col-md-12">
                        <div class="alert alert-info">
                            ${show_message}
                        </div>
                    </div>
                </div>
            % endif

            <div class="row">
                <div class="col-md-12">
                    <div class="panel panel-default panel-body"
                         style="background-image:linear-gradient(to bottom, rgba(0,0,0,0.6) 0%,rgba(0,0,0,0.6) 100%),
                                 url(${srWebRoot}${showImage(show.indexerid, 'banner').url});
                                 background-size: 100% 100%;">
                        % if show.overview:
                            <div class="row">
                                <div class="col-xs-12">
                                    <i>${show.overview}</i>
                                </div>
                            </div>
                            <hr>
                        % endif

                        <div class="row">
                            <div class="col-xs-12 col-md-8">
                                <table class="pull-left">
                                    <tr>
                                        <td class="showLegend">${_('Rating:')}</td>
                                        <td>
                                            % if 'rating' in show.imdb_info:
                                            <% rating_tip = str(show.imdb_info['rating']) + " / 10" + " Stars" + "<br />" + str(show.imdb_info['votes']) + " Votes" %>
                                                <span class="imdbstars" title="${rating_tip}">
                                                    ${show.imdb_info['rating']}
                                                </span>
                                            % endif
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Quality:')}</td>
                                        <td>
                                            <% anyQualities, bestQualities = Quality.splitQuality(int(show.quality)) %>
                                            % if show.quality in qualityPresets:
                                                ${renderQualityPill(show.quality)}
                                            % else:
                                                % if anyQualities:
                                                    <i>Allowed:</i> ${", ".join([capture(renderQualityPill, x) for x in sorted(anyQualities)])}${("", "<br>")[bool(bestQualities)]}
                                                % endif
                                                % if bestQualities:
                                                    <i>Preferred:</i> ${", ".join([capture(renderQualityPill, x) for x in sorted(bestQualities)])}
                                                % endif
                                            % endif
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Show Status:')}</td>
                                        <td>${show.status}</td>
                                    </tr>
                                    % if show.network and show.airs:
                                        <tr>
                                            <td class="showLegend">${_('Originally Airs:')}</td>
                                            <td>${show.airs} ${("<font color='#FF0000'><b>(invalid Timeformat)</b></font> ", "")[tz_updater.test_timeformat(show.airs)]}
                                                on ${show.network}</td>
                                        </tr>
                                    % elif show.network:
                                        <tr>
                                            <td class="showLegend">${_('Originally Airs:')}</td>
                                            <td>${show.network}</td>
                                        </tr>
                                    % elif show.airs:
                                        <tr>
                                            <td class="showLegend">${_('Originally Airs:')}</td>
                                            <td>${show.airs} ${("<font color='#FF0000'><b>(invalid Timeformat)</b></font>", "")[tz_updater.test_timeformat(show.airs)]}</td>
                                        </tr>
                                    % endif
                                    <tr>
                                        <td class="showLegend">${_('Start Year:')}</td>
                                        <td>
                                            <span>${show.startyear}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Runtime:')}</td>
                                        <td>
                                            <span>${show.runtime} ${_('minutes')}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Info Sites:')}</td>
                                        <td>
                                            % if show.imdbid:
                                                <a href="${anon_url('http://www.imdb.com/title/', show.imdbid)}"
                                                   rel="noreferrer"
                                                   onclick="window.open(this.href, '_blank'); return false;"
                                                   title="http://www.imdb.com/title/${show.imdbid}">
                                                    <img alt="[imdb]" height="16" width="16"
                                                         src="${srWebRoot}/images/imdb.png"
                                                         style="margin-top: -1px; vertical-align:middle;"/>
                                                </a>
                                            % endif
                                            <a href="${anon_url(IndexerApi(show.indexer).config['show_url'], show.indexerid)}"
                                               onclick="window.open(this.href, '_blank'); return false;"
                                               title="<% IndexerApi(show.indexer).config["show_url"] + str(show.indexerid) %>"><img
                                                    alt="${IndexerApi(show.indexer).name}" height="16" width="16"
                                                    src="${srWebRoot}/images/${IndexerApi(show.indexer).config["icon"]}"
                                                    style="margin-top: -1px; vertical-align:middle;"/></a>
                                            % if xem_numbering or xem_absolute_numbering:
                                                <a href="${anon_url('http://thexem.de/search?q=', show.name)}"
                                                   rel="noreferrer"
                                                   onclick="window.open(this.href, '_blank'); return false;"
                                                   title="http://thexem.de/search?q-${show.name}">
                                                    <img alt="[xem]"
                                                         height="16"
                                                         width="16"
                                                         src="${srWebRoot}/images/xem.png"
                                                         style="margin-top: -1px; vertical-align:middle;"/></a>
                                            % endif
                                        </td>
                                    </tr>

                                    <tr>
                                        <td class="showLegend">${_('Genre:')}</td>
                                        <td>
                                            <ul class="tags">
                                                % if not show.imdbid and show.genre:
                                                    % for genre in show.genre[1:-1].split('|'):
                                                        <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', genre.lower())}"
                                                           target="_blank"
                                                           title="View other popular ${genre} shows on trakt.tv.">
                                                            <li>${genre}</li>
                                                        </a>
                                                    % endfor
                                                % endif
                                                % if 'year' in show.imdb_info:
                                                    % for imdbgenre in show.imdb_info['genres'].replace('Sci-Fi','Science-Fiction').split('|'):
                                                        <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', imdbgenre.lower())}"
                                                           target="_blank"
                                                           title="View other popular ${imdbgenre} shows on trakt.tv.">
                                                            <li>${imdbgenre}</li>
                                                        </a>
                                                    % endfor
                                                % endif
                                            </ul>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Default EP Status:')}</td>
                                        <td>${statusStrings[show.default_ep_status]}</td>
                                    </tr>
                                    % if os.path.isdir(showLoc):
                                        <tr>
                                            <td class="showLegend">${_('Location:')}</td>
                                            <td>${showLoc}</td>
                                        </tr>
                                    % else:
                                        <tr>
                                            <td class="showLegend"><span style="color: red;">${_('Location:')} </span>
                                            </td>
                                            <td><span style="color: red;">${showLoc}</span> (${_('Missing')})</td>
                                        </tr>
                                    % endif
                                    % if os.path.isdir(showLoc):
                                        <tr>
                                            <td class="showLegend">${_('Size:')}</td>
                                            <td>${pretty_filesize(get_size(showLoc.encode('utf-8')))}</td>
                                        </tr>
                                    % endif
                                    <tr>
                                        <td class="showLegend">${_('Scene Name:')}</td>
                                        <td>${(show.name, " | ".join(show.exceptions))[show.exceptions != 0]}</td>
                                    </tr>
                                    % if show.rls_require_words:
                                        <tr>
                                            <td class="showLegend">${_('Required Words:')}</td>
                                            <td>${show.rls_require_words}</td>
                                        </tr>
                                    % endif
                                    % if show.rls_ignore_words:
                                        <tr>
                                            <td class="showLegend">${_('Ignored Words:')}</td>
                                            <td>${show.rls_ignore_words}</td>
                                        </tr>
                                    % endif
                                    % if bwl and bwl.whitelist:
                                        <tr>
                                            <td class="showLegend">${_('Wanted Group')}${("", "s")[len(bwl.whitelist) > 1]}
                                                :
                                            </td>
                                            <td>${', '.join(bwl.whitelist)}</td>
                                        </tr>
                                    % endif
                                    % if bwl and bwl.blacklist:
                                        <tr>
                                            <td class="showLegend">${_('Unwanted Group')}${("", "s")[len(bwl.blacklist) > 1]}
                                                :
                                            </td>
                                            <td>${', '.join(bwl.blacklist)}</td>
                                        </tr>
                                    % endif
                                </table>
                            </div>

                            <div class="col-xs-12 col-md-4">
                                <table class="pull-xs-left pull-md-right">
                                    <% info_flag = sickrage.subtitles.code_from_code(show.lang) if show.lang else '' %>
                                    <tr>
                                        <td class="showLegend">${_('Info Language:')}</td>
                                        <td><img src="${srWebRoot}/images/subtitles/flags/${info_flag}.png" width="16"
                                                 height="11"
                                                 alt="${show.lang}" title="${show.lang}"
                                                 onError="this.onerror=null;this.src='${srWebRoot}/images/flags/unknown.png';"/>
                                        </td>
                                    </tr>
                                    % if sickrage.app.config.use_subtitles:
                                        <tr>
                                            <td class="showLegend">${_('Subtitles:')}</td>
                                            <td><img
                                                    src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.subtitles)]}"
                                                    alt="${("N", "Y")[bool(show.subtitles)]}" width="16" height="16"/>
                                            </td>
                                        </tr>
                                    % endif
                                    <tr>
                                        <td class="showLegend">${_('Subtitles Metadata:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.subtitles_sr_metadata)]}"
                                                alt="${("N", "Y")[bool(show.subtitles_sr_metadata)]}" width="16"
                                                height="16"/>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Season Folders:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(not show.flatten_folders or sickrage.app.config.naming_force_folders)]}"
                                                alt=="${("N", "Y")[bool(not show.flatten_folders or sickrage.app.config.naming_force_folders)]}"
                                                width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Paused:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.paused)]}"
                                                alt="${("N", "Y")[bool(show.paused)]}" width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Air-by-Date:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.air_by_date)]}"
                                                alt="${("N", "Y")[bool(show.air_by_date)]}" width="16" height="16"/>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Sports:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.is_sports)]}"
                                                alt="${("N", "Y")[bool(show.is_sports)]}" width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Anime:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.is_anime)]}"
                                                alt="${("N", "Y")[bool(show.is_anime)]}" width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('DVD Order:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.dvdorder)]}"
                                                alt="${("N", "Y")[bool(show.dvdorder)]}" width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Scene Numbering:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.scene)]}"
                                                alt="${("N", "Y")[bool(show.scene)]}" width="16" height="16"/></td>
                                    </tr>
                                    <tr>
                                        <td class="showLegend">${_('Archive First Match:')}</td>
                                        <td><img
                                                src="${srWebRoot}/images/${("no16.png", "yes16.png")[bool(show.archive_firstmatch)]}"
                                                alt="${("N", "Y")[bool(show.archive_firstmatch)]}" width="16"
                                                height="16"/></td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div style="padding-bottom: 5px;">
                        <div class="input-group input350 input-group-sm">
                            <select id="statusSelect" title="Change selected episode statuses" class="form-control">
                                <% availableStatus = [WANTED, SKIPPED, IGNORED, FAILED] %>
                                % if sickrage.app.developer:
                                    <% availableStatus.append(UNAIRED) %>
                                % endif
                                % for curStatus in availableStatus + sorted(Quality.DOWNLOADED) + sorted(Quality.ARCHIVED):
                                    % if curStatus not in [DOWNLOADED, ARCHIVED]:
                                        <option value="${curStatus}">${statusStrings[curStatus]}</option>
                                    % endif
                                % endfor
                            </select>
                            <div class="input-group-addon">
                                <a href="#" id="changeStatus" class="glyphicon glyphicon-play"></a>
                            </div>
                        </div>
                        <input type="hidden" id="showID" value="${show.indexerid}"/>
                        <input type="hidden" id="indexer" value="${show.indexer}"/>
                    </div>
                </div>
                <div class="col-md-6 pull-right">
                    <div class="pull-right" id="checkboxControls">
                        <div>
                            <label class="pull-right" for="missed" style="padding-bottom: 5px;">
                            <span class="missed">
                                <input type="checkbox" id="missed" checked/>
                                ${_('Missed:')} <b>${epCounts[Overview.MISSED]}</b>
                            </span>
                            </label>
                            <label class="pull-right" for="wanted" style="padding-bottom: 5px;">
                            <span class="wanted">
                                <input type="checkbox" id="wanted" checked/>
                                ${_('Wanted:')} <b>${epCounts[Overview.WANTED]}</b>
                            </span>
                            </label>
                            <label class="pull-right" for="qual" style="padding-bottom: 5px;">
                            <span class="qual">
                                <input type="checkbox" id="qual" checked/>
                                ${_('Low Quality:')} <b>${epCounts[Overview.QUAL]}</b>
                            </span>
                            </label>
                            <label class="pull-right" for="good" style="padding-bottom: 5px;">
                            <span class="good">
                                <input type="checkbox" id="good" checked/>
                                ${_('Downloaded:')} <b>${epCounts[Overview.GOOD]}</b>
                            </span>
                            </label>
                            <label class="pull-right" for="skipped" style="padding-bottom: 5px;">
                            <span class="skipped">
                            <input type="checkbox" id="skipped" checked/>
                                ${_('Skipped:')} <b>${epCounts[Overview.SKIPPED]}</b>
                            </span>
                            </label>
                            <label class="pull-right" for="snatched" style="padding-bottom: 5px;">
                            <span class="snatched"><input type="checkbox" id="snatched" checked/>
                                ${_('Snatched:')} <b>${epCounts[Overview.SNATCHED]}</b>
                            </span>
                            </label>
                        </div>
                        <div class="pull-right">
                            <button class="btn seriesCheck pull-right">
                                ${_('Select Filtered Episodes')}
                            </button>
                            <button class="btn clearAll pull-right">
                                ${_('Clear All')}
                            </button>
                            <button class="btn pull-right" id="popover" type="button">
                                ${_('Select Columns')} <b class="caret"></b>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
    <div class="col-md-12">
    <% curSeason = -1 %>
    <% odd = 0 %>
    % for epResult in episodeResults:
        <%
            epStr = str(epResult["season"]) + "x" + str(epResult["episode"])
            if not epStr in epCats:
                        next

            if not sickrage.app.config.display_show_specials and int(epResult["season"]) == 0:
                        next

            scene = False
            scene_anime = False
            if not show.air_by_date and not show.is_sports and not show.is_anime and show.is_scene:
                        scene = True
            elif not show.air_by_date and not show.is_sports and show.is_anime and show.is_scene:
                        scene_anime = True

            (dfltSeas, dfltEpis, dfltAbsolute) = (0, 0, 0)
            if (epResult["season"], epResult["episode"]) in xem_numbering:
                        (dfltSeas, dfltEpis) = xem_numbering[(epResult["season"], epResult["episode"])]

            if epResult["absolute_number"] in xem_absolute_numbering:
                        dfltAbsolute = xem_absolute_numbering[epResult["absolute_number"]]

            if epResult["absolute_number"] in scene_absolute_numbering:
                        scAbsolute = scene_absolute_numbering[epResult["absolute_number"]]
                        dfltAbsNumbering = False
            else:
                        scAbsolute = dfltAbsolute
                        dfltAbsNumbering = True

            if (epResult["season"], epResult["episode"]) in scene_numbering:
                        (scSeas, scEpis) = scene_numbering[(epResult["season"], epResult["episode"])]
                        dfltEpNumbering = False
            else:
                        (scSeas, scEpis) = (dfltSeas, dfltEpis)
                        dfltEpNumbering = True

            epLoc = epResult["location"]
            if epLoc and show._location and epLoc.lower().startswith(show._location.lower()):
                        epLoc = epLoc[len(show._location)+1:]
        %>

        % if int(epResult["season"]) != curSeason:
        <% curSeason = int(epResult["season"]) %>
        % if epResult["season"] != episodeResults[0]["season"]:
            </tbody>
            </table>
        </div>
        </div>
        </div>
        % endif

        <div class="row">
            <div class="col-md-12">
                <br/>
                <h3 style="display: inline;"><a
                        name="season-${epResult["season"]}"></a>${(_("Specials"), _("Season") + ' ' + str(epResult["season"]))[int
                (epResult["season"]) > 0]}</h3>
                % if not sickrage.app.config.display_all_seasons:
                    % if curSeason == -1:
                        <button id="showseason-${epResult['season']}" type="button" class="btn btn-xs pull-right"
                                data-toggle="collapse" data-target="#collapseSeason-${epResult['season']}"
                                aria-expanded="true">${_('Hide Episodes')}</button>
                    %else:
                        <button id="showseason-${epResult['season']}" type="button" class="btn btn-xs pull-right"
                                data-toggle="collapse"
                                data-target="#collapseSeason-${epResult['season']}">${_('Show Episodes')}</button>
                    %endif
                % endif
            </div>
        </div>
        <div class="row">
        <div class="col-md-12">
        <div class="horizontal-scroll">
        <table id="${("showTable", "animeTable")[bool(show.is_anime)]}" class="displayShowTable display_show"
               cellspacing="0" border="0" cellpadding="0">
            <thead>
            <tr class="seasoncols">
                <th data-sorter="false" data-priority="critical" class="col-checkbox">
                    <input type="checkbox" class="seasonCheck" id="${epResult["season"]}"/>
                </th>
                <th data-sorter="false" class="col-metadata">${_('NFO')}</th>
                <th data-sorter="false" class="col-metadata">${_('TBN')}</th>
                <th data-sorter="false" class="col-ep episode">${_('Episode')}</th>
                <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(show.is_anime)]}>${_('Absolute')}</th>
                <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene)]}>${_('Scene')}</th>
                <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene_anime)]}>${_('Scene Absolute')}</th>
                <th data-sorter="false" class="col-name">${_('Name')}</th>
                <th data-sorter="false" class="col-ep columnSelector-false size">${_('Size')}</th>
                <th data-sorter="false" class="col-airdate">${_('Airdate')}</th>
                <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickrage.app.config.download_url)]}>${_('Download')}</th>
                <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickrage.app.config.use_subtitles)]}>${_('Subtitles')}</th>
                <th data-sorter="false" class="col-status">${_('Status')}</th>
                <th data-sorter="false" class="col-search">${_('Search')}</th>
            </tr>
            </thead>

        <tbody
            % if sickrage.app.config.display_all_seasons == False:
                class="collapse${("", " in")[curSeason == -1]}"
                id="collapseSeason-${epResult['season']}"
            % endif
        >
        % endif
        <tr class="${Overview.overviewStrings[epCats[epStr]]} season-${curSeason} seasonstyle"
            id="S${str(epResult["season"])}E${str(epResult["episode"])}">

            <td class="col-checkbox">
                % if int(epResult["status"]) != UNAIRED:
                    <input type="checkbox" class="epCheck"
                           id="${str(epResult["season"])}x${str(epResult["episode"])}"
                           name="${str(epResult["season"])}x${str(epResult["episode"])}" title=""/>
                % endif
            </td>

            <td align="center">
                <img src="${srWebRoot}/images/${("nfo-no.gif", "nfo.gif")[epResult["hasnfo"]]}"
                     alt="${("N", "Y")[epResult["hasnfo"]]}" width="23" height="11"/>
            </td>

            <td align="center">
                <img src="${srWebRoot}/images/${("tbn-no.gif", "tbn.gif")[epResult["hastbn"]]}"
                     alt="${("N", "Y")[epResult["hastbn"]]}" width="23" height="11"/>
            </td>

            <td align="center">
                <%
                    text = str(epResult['episode'])
                    if epLoc != '' and epLoc is not None:
                                    text = '<span title="' + epLoc + '" class="addQTip badge">' + text + "</span>"
                %>
            ${text}
            </td>

            <td align="center">${epResult["absolute_number"]}</td>

            <td align="center">
                <input placeholder="${str(dfltSeas)}x${str(dfltEpis)}" size="6"
                       maxlength="8"
                       class="sceneSeasonXEpisode form-control input-scene"
                       data-for-season="${epResult["season"]}"
                       data-for-episode="${epResult["episode"]}"
                       id="sceneSeasonXEpisode_${show.indexerid}_${str(epResult["season"])}_${str(epResult["episode"])}"
                       title="Change the value here if scene numbering differs from the indexer episode numbering"
                    % if dfltEpNumbering:
                       value=""
                    % else:
                       value="${str(scSeas)}x${str(scEpis)}"
                    % endif
                       style="padding: 0; text-align: center; max-width: 60px;"/>
            </td>

            <td align="center">
                <input placeholder="${str(dfltAbsolute)}" size="6" maxlength="8"
                       class="sceneAbsolute form-control input-scene"
                       data-for-absolute="${epResult["absolute_number"]}"
                       id="sceneAbsolute_${show.indexerid}_${str(epResult["absolute_number"])}"
                       title="Change the value here if scene absolute numbering differs from the indexer absolute numbering"
                    % if dfltAbsNumbering:
                       value=""
                    % else:
                       value="${str(scAbsolute)}"
                    % endif
                       style="padding: 0; text-align: center; max-width: 60px;"/>
            </td>

            <td class="col-name">
                <img src="${srWebRoot}/images/info32.png" width="16" height="16" alt=""
                     id="plot_info_${str(show.indexerid)}_${str(epResult["season"])}_${str(epResult["episode"])}"
                    % if epResult["description"]:
                     class="plotInfo"
                     title="${epResult["description"]}"
                    % else:
                     class="plotInfoNone"
                     title=""
                    % endif
                />
                ${epResult["name"]}
            </td>

            <td class="col-ep">
                % if epResult["file_size"]:
                            <% file_size = pretty_filesize(epResult["file_size"]) %>
                ${file_size}
                % endif
            </td>

            <td class="col-airdate">
                % if int(epResult['airdate']) != 1:
                <% airDate = datetime.datetime.fromordinal(epResult['airdate']) %>

                % if airDate.year >= 1970 or show.network:
                    <% airDate = srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(epResult['airdate'], show.airs, show.network)) %>
                % endif
                    <time datetime="${airDate.isoformat()}"
                          class="date">${srdatetime.srDateTime.srfdatetime(airDate)}</time>
                % else:
                    ${_('Never')}
                % endif
            </td>

            <td>
                % if sickrage.app.config.download_url and epResult['location']:
                <%
                    filename = epResult['location']
                    for rootDir in sickrage.app.config.root_dirs.split('|'):
                                    if rootDir.startswith('/'):
                                        filename = filename.replace(rootDir, "")
                    filename = sickrage.app.config.download_url + urllib.quote(filename.encode('utf8'))
                %>
                    <div style="text-align: center;"><a href="${filename}">${_('Download')}</a></div>
                % endif
            </td>

            <td class="col-subtitles" align="center">
                % for flag in (epResult["subtitles"] or '').split(','):
                    % if flag.strip() != 'und':
                        <img src="${srWebRoot}/images/subtitles/flags/${flag}.png"
                             data-image-url="${srWebRoot}/images/subtitles/flags/${flag}.png"
                             width="16" height="11"
                             alt="${sickrage.subtitles.name_from_code(flag)}"
                             title="${sickrage.subtitles.name_from_code(flag)}"
                             onError="this.onerror=null;this.src='${srWebRoot}/images/flags/unknown.png';"/>
                    % else:
                        <img src="${srWebRoot}/images/subtitles/flags/${flag}.png" width="16" height="11"
                             alt="${sickrage.subtitles.name_from_code(flag)}"
                             onError="this.onerror=null;this.src='${srWebRoot}/images/flags/unknown.png';"/>
                    % endif
                % endfor
            </td>

            <% curStatus, curQuality = Quality.splitCompositeStatus(int(epResult["status"])) %>
            % if curQuality != Quality.NONE:
                <td class="col-status">${statusStrings[curStatus]} ${renderQualityPill(curQuality)}</td>
            % else:
                <td class="col-status">${statusStrings[curStatus]}</td>
            % endif

            <td class="col-search">
                % if int(epResult["season"]) != 0:
                    % if ( int(epResult["status"]) in Quality.SNATCHED + Quality.DOWNLOADED ):
                        <a class="epRetry"
                           id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                           name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                           href="retryEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                            <img src="${srWebRoot}/images/search16.png" height="16" alt="retry"
                                 title="${_('Retry Download')}"/>
                        </a>
                    % else:
                        <a class="epSearch"
                           id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                           name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                           href="searchEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                            <img src="${srWebRoot}/images/search16.png" width="16" height="16" alt="search"
                                 title="${_('Manual Search')}"/>
                        </a>
                    % endif
                % endif
                % if sickrage.app.config.use_subtitles and show.subtitles and epResult["location"] and frozenset(sickrage.subtitles.wanted_languages()).difference(epResult["subtitles"].split(',')):
                    <a class="epSubtitlesSearch"
                       href="searchEpisodeSubtitles?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                        <img src="${srWebRoot}/images/closed_captioning.png" height="16" alt="search subtitles"
                             title="${_('Search Subtitles')}"/>
                    </a>
                % endif
            </td>
        </tr>
    % endfor
    </tbody>
    </table>
    </div>
    </div>
    </div>
    ${displayShowModals()}
</%block>
