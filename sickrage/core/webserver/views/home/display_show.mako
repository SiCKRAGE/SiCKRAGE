<%inherit file="../layouts/main.mako"/>
<%!
    import os
    import datetime
    import urllib
    import ntpath

    import sickrage
    import sickrage.subtitles
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, FAILED, DOWNLOADED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, Overview
    from sickrage.core.helpers import anon_url, srdatetime, pretty_filesize, get_size
    from sickrage.core.media.util import showImage
    from sickrage.indexers import IndexerApi
%>

<%namespace file="../includes/modals.mako" import="displayShowModals"/>
<%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>

<%block name="modals">
    ${displayShowModals()}
</%block>

<%block name="content">
    <div class="row">
        <div class="col-lg-12 mx-auto">
            <div class="row">
                <!-- Alert -->
                % if show_message:
                    <div class="col-md-12 p-0">
                        <div class="alert alert-info rounded-0 text-center">
                            <strong>${show_message}</strong>
                        </div>
                    </div>
                % endif

                <div class="col-lg-10 mx-auto">
                    <div class="input-group mx-auto" style="width: 30%">
                        <div class="input-group-prepend">
                            <button id="prevShow" class="btn fas fa-arrow-left"></button>
                        </div>
                        <select class="form-control" id="pickShow" title="Change Show">
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
                        <div class="input-group-append">
                            <button id="nextShow" class="btn fas fa-arrow-right"></button>
                        </div>
                    </div>
                    <br/>
                    <div class="row" id="showtitle" data-showname="${show.name}">
                        <div class="col">
                            <h1>
                                ${show.name}
                            </h1>
                        </div>
                        <div class="col">
                            % if seasonResults:
                            % if int(seasonResults[0]) == 0:
                                <% season_special = 1 %>
                            % else:
                                <% season_special = 0 %>
                            % endif
                            % if not sickrage.app.config.display_show_specials and season_special:
                                <% lastSeason = seasonResults.pop(-1) %>
                            % endif
                                <div class="float-right text-left">
                                    % if season_special:
                                    ${_('Display Specials:')}
                                        <a class="inner"
                                           href="${srWebRoot}/toggleDisplayShowSpecials/?show=${show.indexerid}">
                                            ${('Show', 'Hide')[bool(sickrage.app.config.display_show_specials)]}
                                        </a>
                                    % endif
                                    <br/>
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
                                                <span>|</span>
                                            % endif
                                        % endfor
                                    % endif
                                </div>
                            % endif
                        </div>
                    </div>
                    <hr class="bg-light mt-0"/>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-10 mx-auto">
                    <div class="row mb-1">
                        <div class="col-auto d-none d-lg-block">
                            <img class="shadow-lg rounded" style="margin-bottom: -400px"
                                 src="${srWebRoot}${showImage(show.indexerid, 'poster_thumb').url}"/>
                        </div>
                        <div class="col">
                            <div class="row">
                                <div class="col-auto">
                                    % if show.imdb_info and 'imdbRating' in show.imdb_info:
                                    <% rating_tip = str(show.imdb_info['imdbRating']) + " / 10" + " Stars and " + str(show.imdb_info['imdbVotes']) + " Votes" %>
                                        <span id="imdbstars"
                                              data-imdb-rating="${show.imdb_info['imdbRating']}"
                                              title="${rating_tip}"></span>
                                    % endif
                                </div>

                                <div class="col-auto">
                                    (<span>${show.startyear}</span>) -

                                    <span>
                                        % if show.runtime:
                                            ${show.runtime} ${_('minutes')}
                                        % else:
                                            <span style="color: red;"><b>${_('UNKNOWN')}</b></span>
                                        % endif
                                    </span>

                                    % if show.imdbid:
                                        <a href="${anon_url('http://www.imdb.com/title/', show.imdbid)}"
                                           rel="noreferrer"
                                           onclick="window.open(this.href, '_blank'); return false;"
                                           title="http://www.imdb.com/title/${show.imdbid}">
                                            <i class="sickrage-core sickrage-core-imdb"
                                               style="margin-top: -1px; vertical-align:middle;"></i>
                                        </a>
                                    % endif

                                    % if xem_numbering or xem_absolute_numbering:
                                        <a href="${anon_url('http://thexem.de/search?q=', show.name)}"
                                           rel="noreferrer"
                                           onclick="window.open(this.href, '_blank'); return false;"
                                           title="http://thexem.de/search?q-${show.name}">
                                            <i class="sickrage-core sickrage-core-xem"
                                               style="margin-top: -1px; vertical-align:middle;"></i>
                                        </a>
                                    % endif

                                    <a href="${anon_url(IndexerApi(show.indexer).config['show_url'], show.indexerid)}"
                                       onclick="window.open(this.href, '_blank'); return false;"
                                       title="<% IndexerApi(show.indexer).config["show_url"] + str(show.indexerid) %>">
                                        <i class="sickrage-core sickrage-core-${IndexerApi(show.indexer).name.lower()}"
                                           style="margin-top: -1px; vertical-align:middle;"></i>
                                    </a>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col">
                                    <ul class="list-group d-inline">
                                        % if not show.imdbid and show.genre:
                                            % for genre in show.genre.split(','):
                                                <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', genre.lower())}"
                                                   target="_blank"
                                                   title="View other popular ${genre} shows on trakt.tv.">
                                                    <li class="fas fa-tag fa-1x badge badge-primary p-2"> ${genre}</li>
                                                </a>
                                            % endfor
                                        % endif
                                        % if show.imdb_info and 'Year' in show.imdb_info:
                                            % for imdbgenre in show.imdb_info['Genre'].replace('Sci-Fi','Science-Fiction').split(','):
                                                <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', imdbgenre.lower())}"
                                                   target="_blank"
                                                   title="View other popular ${imdbgenre} shows on trakt.tv.">
                                                    <li class="fas fa-tag fa-1x badge badge-primary p-2"> ${imdbgenre}</li>
                                                </a>
                                            % endfor
                                        % endif
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-auto d-lg-none d-xl-flex">
                            <img class="rounded shadow-lg img-banner"
                                 src="${srWebRoot}${showImage(show.indexerid, 'banner').url}"/>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row bg-dark border border-white">
                <div class="col-lg-6 col-xl-7 offset-0 offset-lg-5 offset-xl-4 offset-xxxl-3">
                    <div class="row" style="margin-bottom: 100px">
                        <div class="col">
                            <div>
                                <i>${show.overview}</i>
                            </div>
                            <br/>
                            <table>
                                <tr>
                                    <td class="show-legend">${_('Quality:')}</td>
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
                                    <td class="show-legend">${_('Show Status:')}</td>
                                    <td>${show.status}</td>
                                </tr>

                                % if show.network and show.airs:
                                    <tr>
                                        <td class="show-legend">${_('Originally Airs:')}</td>
                                        <td>${show.airs} ${("<span style='color: red;'><b>(invalid Timeformat)</b></span> ", "")[sickrage.app.tz_updater.test_timeformat(show.airs)]}
                                            on ${show.network}</td>
                                    </tr>
                                % elif show.network:
                                    <tr>
                                        <td class="show-legend">${_('Originally Airs:')}</td>
                                        <td>${show.network}</td>
                                    </tr>
                                % elif show.airs:
                                    <tr>
                                        <td class="show-legend">${_('Originally Airs:')}</td>

                                        <td>${show.airs} ${("<span style='color: red;'><b>(invalid Timeformat)</b></span>", "")[sickrage.app.tz_updater.test_timeformat(show.airs)]}</td>
                                    </tr>
                                % endif

                                <tr>
                                    <td class="show-legend">${_('Default EP Status:')}</td>
                                    <td>${statusStrings[show.default_ep_status]}</td>
                                </tr>

                                <tr>
                                    <td class="show-legend">${_('Location:')}</td>
                                    % if os.path.isdir(showLoc):
                                        <td>${showLoc}</td>
                                    % else:
                                        <td><span style="color: red;">${showLoc}</span> (${_('Missing')})</td>
                                    % endif
                                </tr>

                                <tr>
                                    <td class="show-legend">${_('Size:')}</td>
                                    <td>${pretty_filesize(show.show_size)}</td>
                                </tr>

                                <tr>
                                    <td class="show-legend">${_('Scene Name:')}</td>
                                    <td>${(show.name, " | ".join(show.exceptions))[show.exceptions != 0]}</td>
                                </tr>

                                <tr>
                                    <td class="show-legend">${_('Search Delay:')}</td>
                                    <td>${show.search_delay} day(s)</td>
                                </tr>

                                % if show.rls_require_words:
                                    <tr>
                                        <td class="show-legend">${_('Required Words:')}</td>
                                        <td>${show.rls_require_words}</td>
                                    </tr>
                                % endif

                                % if show.rls_ignore_words:
                                    <tr>
                                        <td class="show-legend">${_('Ignored Words:')}</td>
                                        <td>${show.rls_ignore_words}</td>
                                    </tr>
                                % endif

                                % if bwl and bwl.whitelist:
                                    <tr>
                                        <td class="show-legend">${_('Wanted Group')}${("", "s")[len(bwl.whitelist) > 1]}
                                            :
                                        </td>
                                        <td>${', '.join(bwl.whitelist)}</td>
                                    </tr>
                                % endif

                                % if bwl and bwl.blacklist:
                                    <tr>
                                        <td class="show-legend">${_('Unwanted Group')}${("", "s")[len(bwl.blacklist) > 1]}
                                            :
                                        </td>
                                        <td>${', '.join(bwl.blacklist)}</td>
                                    </tr>
                                % endif
                            </table>
                        </div>

                        <div class="col-auto">
                            <table>
                                <% info_flag = sickrage.subtitles.code_from_code(show.lang) if show.lang else '' %>
                                <tr>
                                    <td class="show-legend">${_('Info Language:')}</td>
                                    <td>
                                        <i class="sickrage-flags sickrage-flags-${info_flag}"></i>
                                    </td>
                                </tr>
                                % if sickrage.app.config.use_subtitles:
                                    <tr>
                                        <td class="show-legend">${_('Subtitles:')}</td>
                                        <td>
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.subtitles)]}"></i>
                                        </td>
                                    </tr>
                                % endif
                                <tr>
                                    <td class="show-legend">${_('Subtitles Metadata:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.subtitles_sr_metadata)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Season Folders:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(not show.flatten_folders or sickrage.app.config.naming_force_folders)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Paused:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.paused)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Air-by-Date:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.air_by_date)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Sports:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.is_sports)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Anime:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.is_anime)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('DVD Order:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.dvdorder)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Scene Numbering:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.scene)]}"></i>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="show-legend">${_('Skip Downloaded:')}</td>
                                    <td>
                                        <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(show.skip_downloaded)]}"></i>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="row bg-dark border border-white">
        <div class="col-lg-10 mx-auto m-1">
            <div class="row">
                <div class="col-md-auto my-auto">
                    <div class="input-group float-md-left">
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
                        <div class="input-group-append">
                            <button id="changeStatus" class="btn fas fa-play"></button>
                        </div>
                    </div>
                    <input type="hidden" id="showID" value="${show.indexerid}"/>
                    <input type="hidden" id="indexer" value="${show.indexer}"/>
                </div>
                <div class="col">
                    <div class="d-inline-flex float-md-right">
                        <h5 class="my-auto mr-2">
                                    <span class="badge missed">
                                        <input type="checkbox" id="missed" checked/>
                                        ${_('Missed:')} <b>${epCounts[Overview.MISSED]}</b>
                                    </span>
                            <span class="badge wanted">
                                        <input type="checkbox" id="wanted" checked/>
                                ${_('Wanted:')} <b>${epCounts[Overview.WANTED]}</b>
                                    </span>
                            <span class="badge qual">
                                        <input type="checkbox" id="qual" checked/>
                                ${_('Low Quality:')} <b>${epCounts[Overview.QUAL]}</b>
                                    </span>
                            <span class="badge good">
                                        <input type="checkbox" id="good" checked/>
                                ${_('Downloaded:')} <b>${epCounts[Overview.GOOD]}</b>
                                    </span>
                            <span class="badge skipped">
                                        <input type="checkbox" id="skipped" checked/>
                                ${_('Skipped:')} <b>${epCounts[Overview.SKIPPED]}</b>
                                    </span>
                            <span class="badge snatched">
                                        <input type="checkbox" id="snatched" checked/>
                                <% total_snatched = epCounts[Overview.SNATCHED] + epCounts[Overview.SNATCHED_PROPER] + epCounts[Overview.SNATCHED_BEST] %>
                                ${_('Snatched:')} <b>${total_snatched}</b>
                                    </span>
                        </h5>
                        <div class="btn-group-md d-sm-inline-flex d-md-inline-block my-auto">
                            <button class="btn" id="popover">
                                ${_('Columns')} <b class="fas fa-caret-down"></b>
                            </button>
                            <button class="btn seriesCheck">
                                ${_('Select Episodes')}
                            </button>
                            <button class="btn clearAll">
                                ${_('Clear All')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </div>
    </div>

    <div class="row">
    <div class="col-lg-10 mx-auto">
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
                                <button id="showseason-${epResult['season']}" type="button"
                                        class="btn btn-xs text-right"
                                        data-toggle="collapse" data-target="#collapseSeason-${epResult['season']}"
                                        aria-expanded="true">${_('Hide Episodes')}</button>
                            %else:
                                <button id="showseason-${epResult['season']}" type="button"
                                        class="btn btn-xs text-right"
                                        data-toggle="collapse"
                                        data-target="#collapseSeason-${epResult['season']}">${_('Show Episodes')}</button>
                            %endif
                        % endif
                    </div>
                </div>
            <div class="row">
            <div class="col-md-12">
            <div class="table-responsive">
            <table id="${("showTable", "animeTable")[bool(show.is_anime)]}" class="table displayShowTable">
                <thead class="thead-dark">
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
                    % if len(sickrage.app.search_providers.enabled()):
                        <th data-sorter="false" class="col-search">${_('Search')}</th>
                    % endif
                </tr>
                </thead>

            <tbody
                % if sickrage.app.config.display_all_seasons == False:
                    class="collapse${("", " in")[curSeason == -1]}"
                    id="collapseSeason-${epResult['season']}"
                % endif
            >
            % endif
            <tr class="${Overview.overviewStrings[epCats[epStr]]} season-${curSeason} seasonstyle font-weight-bold text-dark"
                id="S${str(epResult["season"])}E${str(epResult["episode"])}">

                <td class="table-fit col-checkbox">
                    % if int(epResult["status"]) != UNAIRED:
                        <input type="checkbox" class="epCheck"
                               id="${str(epResult["season"])}x${str(epResult["episode"])}"
                               name="${str(epResult["season"])}x${str(epResult["episode"])}" title=""/>
                    % endif
                </td>

                <td class="table-fit">
                    <i class="fas ${("fa-times", "fa-check")[epResult["hasnfo"]]}"></i>
                </td>

                <td class="table-fit">
                    <i class="fas ${("fa-times", "fa-check")[epResult["hastbn"]]}"></i>
                </td>

                <td class="table-fit">
                    <%
                        text = str(epResult['episode'])
                        if epLoc != '' and epLoc is not None:
                                    text = '<span title="' + epLoc + '" class="badge badge-dark">' + text + "</span>"
                    %>
                        ${text}
                </td>

                <td class="table-fit">${epResult["absolute_number"]}</td>

                <td class="table-fit">
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

                <td class="table-fit">
                    <input placeholder="${str(dfltAbsolute)}" size="6" maxlength="8"
                           class="sceneAbsolute form-control d-inline input-scene"
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
                    <i id="plot_info_${str(show.indexerid)}_${str(epResult["season"])}_${str(epResult["episode"])}"
                       class="fas fa-info-circle" title="${epResult["description"]}"></i>
                    ${epResult["name"]}
                </td>

                <td class="table-fit text-nowrap col-ep">
                    ${pretty_filesize(epResult["file_size"])}
                </td>

                <td class="table-fit col-airdate">
                    % if int(epResult['airdate']) != 1:
                    <% airDate = datetime.datetime.fromordinal(epResult['airdate']) %>

                    % if airDate.year >= 1970 or show.network:
                        <% airDate = srdatetime.srDateTime(sickrage.app.tz_updater.parse_date_time(epResult['airdate'], show.airs, show.network), convert=True).dt %>
                    % endif
                        <time datetime="${airDate.isoformat()}" class="date text-nowrap">
                            ${srdatetime.srDateTime(airDate).srfdatetime()}
                        </time>
                    % else:
                        ${_('Never')}
                    % endif
                </td>

                <td class="table-fit">
                    % if sickrage.app.config.download_url and epResult['location']:
                    <%
                        filename = epResult['location']
                        for rootDir in sickrage.app.config.root_dirs.split('|'):
                                                if rootDir.startswith('/'):
                                                    filename = filename.replace(rootDir, "")
                        filename = sickrage.app.config.download_url + urllib.quote(filename.encode('utf8'))
                    %>
                        <div style="text-align: center;">
                            <a href="${filename}">${_('Download')}</a>
                        </div>
                    % endif
                </td>

                <td class="table-fit col-subtitles">
                    % for flag in (epResult["subtitles"] or '').split(','):
                        % if sickrage.subtitles.name_from_code(flag).lower() != 'undetermined':
                            % if flag.strip() != 'und':
                                <i class="sickrage-flags sickrage-flags-${flag}"
                                   title="${sickrage.subtitles.name_from_code(flag)}"></i>
                            % else:
                                <i class="sickrage-flags sickrage-flags-${flag}"
                                   title="${sickrage.subtitles.name_from_code(flag)}"></i>
                            % endif
                        % else:
                            <i class="sickrage-flags sickrage-flags-unknown" title="${_('Unknown')}"></i>
                        % endif
                    % endfor
                </td>

                <% curStatus, curQuality = Quality.splitCompositeStatus(int(epResult["status"])) %>
                % if curQuality != Quality.NONE:
                    <td class="table-fit text-nowrap col-status">${statusStrings[curStatus]} ${renderQualityPill(curQuality)}</td>
                % else:
                    <td class="table-fit text-nowrap col-status">${statusStrings[curStatus]}</td>
                % endif

                % if len(sickrage.app.search_providers.enabled()):
                    <td class="table-fit col-search">
                        % if int(epResult["season"]) != 0:
                            % if ( int(epResult["status"]) in Quality.SNATCHED + Quality.DOWNLOADED ):
                                <a class="epRetry"
                                   id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                                   name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                                   href="retryEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                    <i class="fas fa-sync" title="${_('Retry Download')}"></i>
                                </a>
                            % else:
                                <a class="epSearch"
                                   id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                                   name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}"
                                   href="searchEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                    <i class="fas fa-search" title="${_('Manual Search')}"></i>
                                </a>
                            % endif
                        % endif
                        % if sickrage.app.config.use_subtitles and show.subtitles and epResult["location"] and frozenset(sickrage.subtitles.wanted_languages()).difference(epResult["subtitles"].split(',')):
                            <a class="epSubtitlesSearch"
                               href="searchEpisodeSubtitles?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                <i class="fas fa-comment" title="${_('Subtitles Search')}"></i>
                            </a>
                        % endif
                    </td>
                % endif
            </tr>
        % endfor
    </tbody>
    </table>
    </div>
    </div>
    </div>
    </div>
    </div>
</%block>