<%!
    import sickbeard
    import datetime
    from sickbeard import db, network_timezones
    from sickbeard.common import Quality, SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import qualityPresets, qualityPresetStrings
    import calendar
    from time import time
    import re

    # resource module is unix only
    has_resource_module = True
    try:
        import resource
    except ImportError:
        has_resource_module = False
%>
<%
    srRoot = sickbeard.WEB_ROOT
%>
<!DOCTYPE html>
<html lang="en">
    <head>
        <!-- Required meta tags always come first -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="x-ua-compatible" content="ie=edge">

        <meta data-var="srRoot" data-content="${srRoot}">
        <meta data-var="themeSpinner" data-content="${('', '-dark')[sickbeard.THEME_NAME == 'dark']}">
        <meta data-var="anonURL" data-content="${sickbeard.ANON_REDIRECT}">

        <meta data-var="sickbeard.ANIME_SPLIT_HOME" data-content="${sickbeard.ANIME_SPLIT_HOME}">
        <meta data-var="sickbeard.COMING_EPS_LAYOUT" data-content="${sickbeard.COMING_EPS_LAYOUT}">
        <meta data-var="sickbeard.COMING_EPS_SORT" data-content="${sickbeard.COMING_EPS_SORT}">
        <meta data-var="sickbeard.DATE_PRESET" data-content="${sickbeard.DATE_PRESET}">
        <meta data-var="sickbeard.FILTER_ROW" data-content="${sickbeard.FILTER_ROW}">
        <meta data-var="sickbeard.FUZZY_DATING" data-content="${sickbeard.FUZZY_DATING}">
        <meta data-var="sickbeard.HISTORY_LAYOUT" data-content="${sickbeard.HISTORY_LAYOUT}">
        <meta data-var="sickbeard.HOME_LAYOUT" data-content="${sickbeard.HOME_LAYOUT}">
        <meta data-var="sickbeard.POSTER_SORTBY" data-content="${sickbeard.POSTER_SORTBY}">
        <meta data-var="sickbeard.POSTER_SORTDIR" data-content="${sickbeard.POSTER_SORTDIR}">
        <meta data-var="sickbeard.ROOT_DIRS" data-content="${sickbeard.ROOT_DIRS}">
        <meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
        <meta data-var="sickbeard.TIME_PRESET" data-content="${sickbeard.TIME_PRESET}">
        <meta data-var="sickbeard.TRIM_ZERO" data-content="${sickbeard.TRIM_ZERO}">
        <%block name="metas" />

        <!-- Bootstrap CSS -->
        <link rel="stylesheet" type="text/css" href="https://v4-alpha.getbootstrap.com/dist/css/bootstrap.min.css">

        <!-- Library CSS -->
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/browser.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/pnotify.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/country-flags.css?${sbPID}"/>

        <!-- Custom CSS -->
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/style.css?${sbPID}"/><!-- This will be faded out as we move to core.css -->
        <link rel="stylesheet" type="text/css" href="/css/b4/core.css?${sbPID}">
        <link rel="stylesheet" type="text/css" href="/css/b4/overrides/bootstrap.css?${sbPID}">
        <link rel="stylesheet" type="text/css" href="/css/b4/overrides/browser.css?${sbPID}">

        <!-- Theme CSS -->
        <link rel="stylesheet" type="text/css" href="/css/b4/themes/${sickbeard.THEME_NAME}.css">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-inverse navbar-static-top">
            <a class="navbar-brand" href="#">SickRage</a>
            % if sbLogin:
            <ul class="nav nav-pills pull-right">
                <li id="home" class="nav-item dropdown${('', ' active')[topmenu == 'home']}">
                    <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">Shows <span class="sr-only">(current)</span></a>
                    <div class="dropdown-menu">
                        <a class="dropdown-item" href="${srRoot}/home/"><i class="menu-icon-home"></i>&nbsp;Show List</a>
                        <a class="dropdown-item" href="${srRoot}/home/addShows/"><i class="menu-icon-addshow"></i>&nbsp;Add Shows</a>
                        <a class="dropdown-item" href="${srRoot}/home/postprocess/"><i class="menu-icon-postprocess"></i>&nbsp;Manual Post-Processing</a>
                        % if sickbeard.SHOWS_RECENT:
                            <div class="dropdown-divider"></div>
                            % for recentShow in sickbeard.SHOWS_RECENT:
                                <a class="dropdown-item" href="${srRoot}/home/displayShow/?show=${recentShow['indexerid']}"><i class="menu-icon-addshow"></i>&nbsp;${recentShow['name']|trim,h}</a>
                            % endfor
                        % endif
                    </div>
                </li>
                <li id="schedule" class="nav-item${('', ' active')[topmenu == 'comingEpisodes']}">
                    <a class="nav-link" href="${srRoot}/comingEpisodes/">Schedule</a>
                </li>
                <li id="history" class="nav-item${('', ' active')[topmenu == 'history']}">
                    <a class="nav-link" href="${srRoot}/history/">History</a>
                </li>
                <li id="manage" class="nav-item dropdown${('', ' active')[topmenu == 'manage']}">
                    <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">Manage</a>
                    <div class="dropdown-menu">
                        <a class="dropdown-item" href="${srRoot}/manage/"><i class="menu-icon-manage"></i>&nbsp;Mass Update</a>
                        <a class="dropdown-item" href="${srRoot}/manage/backlogOverview/"><i class="menu-icon-backlog-view"></i>&nbsp;Backlog Overview</a>
                        <a class="dropdown-item" href="${srRoot}/manage/manageSearches/"><i class="menu-icon-manage-searches"></i>&nbsp;Manage Searches</a>
                        <a class="dropdown-item" href="${srRoot}/manage/postprocess/"><i class="menu-icon-backlog"></i>&nbsp;Episode Status Management</a>

                        % if sickbeard.USE_PLEX and sickbeard.PLEX_SERVER_HOST != "":
                            <a class="dropdown-item" href="${srRoot}/manage/updatePLEX/"><i class="menu-icon-backlog-view"></i>&nbsp;Update PLEX</a>
                        % endif
                        % if sickbeard.USE_KODI and sickbeard.KODI_HOST != "":
                            <a class="dropdown-item" href="${srRoot}/manage/updateKODI/"><i class="menu-icon-kodi"></i>&nbsp;Update KODI</a>
                        % endif
                        % if sickbeard.USE_EMBY and sickbeard.EMBY_HOST != "" and sickbeard.EMBY_APIKEY != "":
                            <a class="dropdown-item" href="${srRoot}/manage/updateEMBY/"><i class="menu-icon-backlog-view"></i>&nbsp;Update Emby</a>
                        % endif
                        % if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
                            <a class="dropdown-item" href="${srRoot}/manage/manageTorrents/"><i class="menu-icon-bittorrent"></i>&nbsp;Manage Torrents</a>
                        % endif
                        % if sickbeard.USE_FAILED_DOWNLOADS:
                            <a class="dropdown-item" href="${srRoot}/manage/failedDownloads/"><i class="menu-icon-failed-download"></i>&nbsp;Failed Downloads</a>
                        % endif
                        % if sickbeard.USE_SUBTITLES:
                            <a class="dropdown-item" href="${srRoot}/home/subtitleMissed/"><i class="menu-icon-backlog"></i>&nbsp;Missed Subtitle Management</a>
                        % endif
                    </div>
                </li>
                <li id="config" class="nav-item dropdown${('', ' active')[topmenu == 'config']}">
                    <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">Config</a>
                    <div class="dropdown-menu">
                        <a class="dropdown-item" href="${srRoot}/config/"><i class="menu-icon-help"></i>&nbsp;Help &amp; Info</a>
                        <a class="dropdown-item" href="${srRoot}/config/general/"><i class="menu-icon-config"></i>&nbsp;General</a>
                        <a class="dropdown-item" href="${srRoot}/config/backuprestore/"><i class="menu-icon-config"></i>&nbsp;Backup &amp; Restore</a>
                        <a class="dropdown-item" href="${srRoot}/config/search/"><i class="menu-icon-config"></i>&nbsp;Search Settings</a>
                        <a class="dropdown-item" href="${srRoot}/config/providers/"><i class="menu-icon-config"></i>&nbsp;Search Providers</a>
                        <a class="dropdown-item" href="${srRoot}/config/subtitles/"><i class="menu-icon-config"></i>&nbsp;Subtitles Settings</a>
                        <a class="dropdown-item" href="${srRoot}/config/postProcessing/"><i class="menu-icon-config"></i>&nbsp;Post Processing</a>
                        <a class="dropdown-item" href="${srRoot}/config/notifications/"><i class="menu-icon-config"></i>&nbsp;Notifications</a>
                        <a class="dropdown-item" href="${srRoot}/config/anime/"><i class="menu-icon-config"></i>&nbsp;Anime</a>
                    </div>
                </li>
                <%
                    if sickbeard.NEWS_UNREAD:
                        newsBadge = ' <span class="badge">'+str(sickbeard.NEWS_UNREAD)+'</span>'
                    else:
                        newsBadge = ''

                    numCombined = numErrors + numWarnings + sickbeard.NEWS_UNREAD
                    if numCombined:
                        if numErrors:
                            toolsBadgeClass = ' btn-danger'
                        elif numWarnings:
                            toolsBadgeClass = ' btn-warning'
                        else:
                            toolsBadgeClass = ''

                        toolsBadge = ' <span class="badge'+toolsBadgeClass+'">'+str(numCombined)+'</span>'
                    else:
                        toolsBadge = ''
                %>
                <li id="system" class="nav-item dropdown${('', ' active')[topmenu == 'system']}">
                    <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">Tools&nbsp;${toolsBadge}</a>
                    <div class="dropdown-menu">
                        <a class="dropdown-item" href="${srRoot}/news/"><i class="menu-icon-help"></i>&nbsp;News${newsBadge}</a>
                        <a class="dropdown-item" href="${srRoot}/IRC/"><i class="menu-icon-help"></i>&nbsp;IRC</a>
                        <a class="dropdown-item" href="${srRoot}/changes/"><i class="menu-icon-help"></i>&nbsp;Changelog</a>
                        <a class="dropdown-item" href="${srRoot}/IRC/"><i class="menu-icon-help"></i>&nbsp;IRC</a>
                        <a class="dropdown-item" href="https://github.com/SiCKRAGETV/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;"><i class="menu-icon-help"></i>&nbsp;Support SickRage</a>
                        <div class="dropdown-divider"></div>
                        %if numErrors:
                            <a class="dropdown-item" href="${srRoot}/errorlogs/"><i class="menu-icon-viewlog-errors"></i>&nbsp;View Errors <span class="badge btn-danger">${numErrors}</span></a>
                        %endif
                        %if numWarnings:
                            <a class="dropdown-item" href="${srRoot}/errorlogs/?level=${sickbeard.logger.WARNING}"><i class="menu-icon-viewlog-errors"></i>&nbsp;View Warnings <span class="badge btn-warning">${numWarnings}</span></a>
                        %endif
                        <a class="dropdown-item" href="${srRoot}/viewlog/"><i class="menu-icon-viewlog"></i>&nbsp;View Log</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="${srRoot}/home/updateCheck?pid=${sbPID}"><i class="menu-icon-update"></i>&nbsp;Check For Updates</a>
                        <a class="dropdown-item" href="${srRoot}/home/restart/?pid=${sbPID}" class="confirm restart"><i class="menu-icon-restart"></i>&nbsp;Restart</a>
                        <a class="dropdown-item" href="${srRoot}/home/shutdown/?pid=${sbPID}" class="confirm shutdown"><i class="menu-icon-shutdown"></i>&nbsp;Shutdown</a>
                        <a class="dropdown-item" href="${srRoot}/logout" class="confirm logout"><i class="menu-icon-shutdown"></i>&nbsp;Logout</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="${srRoot}/home/status/"><i class="menu-icon-help"></i>&nbsp;Server Status</a>
                    </div>
                </li>
            </ul>
            % endif
        </nav>
        <div class="container-fluid">
            % if not submenu is UNDEFINED:
            <div id="SubMenu" class="hidden-print">
                <span>
                <% first = True %>
                % for menuItem in submenu:
                    % if 'requires' not in menuItem or menuItem['requires']:
                        <% icon_class = '' if 'icon' not in menuItem else ' ' + menuItem['icon'] %>
                          % if type(menuItem['path']) == dict:
                              ${("</span><span>", "")[bool(first)]}<b>${menuItem['title']}</b>
                              <%
                                  first = False
                                  inner_first = True
                              %>
                              % for cur_link in menuItem['path']:
                                  ${("&middot; ", "")[bool(inner_first)]}<a class="inner" href="${srRoot}/${menuItem['path'][cur_link]}">${cur_link}</a>
                                  <% inner_first = False %>
                              % endfor
                          % else:
                              <a href="${srRoot}/${menuItem['path']}" class="btn${('', (' confirm ' + menuItem.get('class', '')))['confirm' in menuItem]}">${('', '<span class="pull-left ' + icon_class + '"></span> ')[bool(icon_class)]}${menuItem['title']}</a>
                              <% first = False %>
                          % endif
                    % endif
                % endfor
                </span>
            </div>
            % endif
            % if sickbeard.BRANCH and sickbeard.BRANCH != 'master' and not sickbeard.DEVELOPER and sbLogin:
            <div class="alert alert-danger upgrade-notification hidden-print" role="alert">
                <span>You're using the ${sickbeard.BRANCH} branch. Please use 'master' unless specifically asked</span>
            </div>
            % endif

            % if sickbeard.NEWEST_VERSION_STRING and sbLogin:
            <div class="alert alert-success upgrade-notification hidden-print" role="alert">
                <span>${sickbeard.NEWEST_VERSION_STRING}</span>
            </div>
            % endif
        </div>
        <div class="container-fluid">
            <%block name="content" />
        </div><!-- /.container -->

        <!-- Use Bower for library loading -->
        <script type="text/javascript" src="${srRoot}/js/_bower.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.cookie.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.cookiejar.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.json-2.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.selectboxes.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter-2.17.7.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter.widgets-2.17.7.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter.widget-columnSelector-2.17.7.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.qtip-2.2.1.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.ui.touch-punch-0.2.2.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/isotope.pkgd.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.confirm.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/formwizard.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/pnotify.custom.min.js?${sbPID}"></script><!-- Needs to be removed -->
        <script type="text/javascript" src="${srRoot}/js/new/parsers.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/new/meta.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/script.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.scrolltopcontrol-1.1.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/browser.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/ajaxNotifications.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/confirmations.js?${sbPID}"></script>
        <%block name="scripts" />
    </body>
</html>
