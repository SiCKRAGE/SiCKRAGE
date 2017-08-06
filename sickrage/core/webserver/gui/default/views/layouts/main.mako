<%!
    import datetime
    import re

    from time import time

    import sickrage
    from sickrage.core.updaters import tz_updater
    from sickrage.core.tv.show import TVShow
    from sickrage.core.helpers import pretty_filesize, overall_stats

    # resource module is unix only
    has_resource_module = True
    try:
        import resource
    except ImportError:
        has_resource_module = False
%>
<!DOCTYPE html>
<html>
<head>
    <title>SickRage - ${title}</title>

    <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <meta charset="utf-8">
    <meta name="robots" content="noindex, nofollow">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=0.5, user-scalable=no">

    % if sickrage.srCore.srConfig.THEME_NAME == "dark":
        <meta name="theme-color" content="#15528F">
    % elif sickrage.srCore.srConfig.THEME_NAME == "light":
        <meta name="theme-color" content="#333333">
    % endif

    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="${srWebRoot}/images/ico/ms-icon-144x144.png">
    <meta name="msapplication-config" content="${srWebRoot}/images/ico/browserconfig.xml">

    <meta data-var="srPID" data-content="${srPID}">
    <meta data-var="srDefaultPage" data-content="${srDefaultPage}">
    <meta data-var="srWebRoot" data-content="${srWebRoot}">
    <meta data-var="themeSpinner" data-content="${('', '-dark')[sickrage.srCore.srConfig.THEME_NAME == 'dark']}">
    <meta data-var="anonURL" data-content="${sickrage.srCore.srConfig.ANON_REDIRECT}">
    <meta data-var="sickrage.ANIME_SPLIT_HOME" data-content="${sickrage.srCore.srConfig.ANIME_SPLIT_HOME}">
    <meta data-var="sickrage.COMING_EPS_LAYOUT" data-content="${sickrage.srCore.srConfig.COMING_EPS_LAYOUT}">
    <meta data-var="sickrage.COMING_EPS_SORT" data-content="${sickrage.srCore.srConfig.COMING_EPS_SORT}">
    <meta data-var="sickrage.DATE_PRESET" data-content="${sickrage.srCore.srConfig.DATE_PRESET}">
    <meta data-var="sickrage.FILTER_ROW" data-content="${sickrage.srCore.srConfig.FILTER_ROW}">
    <meta data-var="sickrage.FUZZY_DATING" data-content="${sickrage.srCore.srConfig.FUZZY_DATING}">
    <meta data-var="sickrage.HISTORY_LAYOUT" data-content="${sickrage.srCore.srConfig.HISTORY_LAYOUT}">
    <meta data-var="sickrage.HOME_LAYOUT" data-content="${sickrage.srCore.srConfig.HOME_LAYOUT}">
    <meta data-var="sickrage.POSTER_SORTBY" data-content="${sickrage.srCore.srConfig.POSTER_SORTBY}">
    <meta data-var="sickrage.POSTER_SORTDIR" data-content="${sickrage.srCore.srConfig.POSTER_SORTDIR}">
    <meta data-var="sickrage.ROOT_DIRS" data-content="${sickrage.srCore.srConfig.ROOT_DIRS}">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.srCore.srConfig.SORT_ARTICLE}">
    <meta data-var="sickrage.TIME_PRESET" data-content="${sickrage.srCore.srConfig.TIME_PRESET}">
    <meta data-var="sickrage.TRIM_ZERO" data-content="${sickrage.srCore.srConfig.TRIM_ZERO}">
    <meta data-var="sickrage.FANART_BACKGROUND" data-content="${sickrage.srCore.srConfig.FANART_BACKGROUND}">
    <meta data-var="sickrage.FANART_BACKGROUND_OPACITY"
          data-content="${sickrage.srCore.srConfig.FANART_BACKGROUND_OPACITY}">
    <%block name="metas" />

    <link rel="apple-touch-icon" sizes="57x57" href="${srWebRoot}/images/ico/apple-icon-57x57.png">
    <link rel="apple-touch-icon" sizes="60x60" href="${srWebRoot}/images/ico/apple-icon-60x60.png">
    <link rel="apple-touch-icon" sizes="72x72" href="${srWebRoot}/images/ico/apple-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="76x76" href="${srWebRoot}/images/ico/apple-icon-76x76.png">
    <link rel="apple-touch-icon" sizes="114x114" href="${srWebRoot}/images/ico/apple-icon-114x114.png">
    <link rel="apple-touch-icon" sizes="120x120" href="${srWebRoot}/images/ico/apple-icon-120x120.png">
    <link rel="apple-touch-icon" sizes="144x144" href="${srWebRoot}/images/ico/apple-icon-144x144.png">
    <link rel="apple-touch-icon" sizes="152x152" href="${srWebRoot}/images/ico/apple-icon-152x152.png">
    <link rel="apple-touch-icon" sizes="180x180" href="${srWebRoot}/images/ico/apple-icon-180x180.png">
    <link rel="icon" type="image/png" sizes="192x192" href="${srWebRoot}/images/ico/android-icon-192x192.png">
    <link rel="icon" type="image/png" sizes="32x32" href="${srWebRoot}/images/ico/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="${srWebRoot}/images/ico/favicon-96x96.png">
    <link rel="icon" type="image/png" sizes="16x16" href="${srWebRoot}/images/ico/favicon-16x16.png">
    <link rel="manifest" href="${srWebRoot}/images/ico/manifest.json">

    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/bower.min.css"/>
    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css"/>
    <link rel="stylesheet" type="text/css"
          href="${srWebRoot}/css/themes/${sickrage.srCore.srConfig.THEME_NAME}.min.css"/>
    <%block name="css" />

    <script src="${srWebRoot}/js/bower.min.js"></script>
    <script src="${srWebRoot}/js/core.min.js"></script>
    <%block name="scripts" />
</head>
<body data-controller="${controller}" data-action="${action}">

<nav class="navbar navbar-default navbar-fixed-top">
    <div class="container-fluid">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse"
                    data-target="#navbar-collapse-1" aria-expanded="false">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="${srWebRoot}/home/">
                <img alt="SiCKRAGE"
                     src="${srWebRoot}/images/logo.png"
                     style="width: 200px;height: 50px;"
                     class="img-responsive pull-left"/>
            </a>
        </div>
        % if current_user:
            <div class="collapse navbar-collapse" id="navbar-collapse-1">
                <ul class="nav navbar-nav navbar-right">
                    <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                        <a href="${srWebRoot}/home/" class="dropdown-toggle" aria-haspopup="true"
                           data-toggle="dropdown"
                           data-hover="dropdown"><span>Shows</span>
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a href="${srWebRoot}/home/">
                                    <i class="menu-icon-home"></i>&nbsp;Show List
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/home/addShows/">
                                    <i class="menu-icon-addshow"></i>&nbsp;Add Shows
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/home/postprocess/">
                                    <i class="menu-icon-postprocess"></i>&nbsp;Manual Post-Processing
                                </a>
                            </li>
                            % if sickrage.srCore.srConfig.SHOWS_RECENT:
                                <li class="divider"></li>
                            % for recentShow in sickrage.srCore.srConfig.SHOWS_RECENT:
                                <li>
                                    <a href="${srWebRoot}/home/displayShow/?show=${recentShow['indexerid']}">
                                        <i class="menu-icon-addshow"></i>&nbsp;${recentShow['name']|trim,h}
                                    </a>
                                </li>
                            % endfor
                            % endif
                        </ul>
                        <div style="clear:both;"></div>
                    </li>

                    <li id="NAVmanage" class="navbar-split dropdown${('', ' active')[topmenu == 'manage']}">
                        <a href="${srWebRoot}/manage/episodeStatuses/" class="dropdown-toggle" aria-haspopup="true"
                           data-toggle="dropdown" data-hover="dropdown">
                            <span>Manage</span>
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a href="${srWebRoot}/manage/">
                                    <i class="menu-icon-manage"></i>&nbsp;Mass Update
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/manage/backlogOverview/">
                                    <i class="menu-icon-backlog-view"></i>&nbsp;Backlog Overview
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/manage/manageSearches/">
                                    <i class="menu-icon-manage-searches"></i>&nbsp;Manage Searches
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/manage/episodeStatuses/">
                                    <i class="menu-icon-backlog"></i>&nbsp;Episode Status Management
                                </a>
                            </li>
                            % if sickrage.srCore.srConfig.USE_PLEX and sickrage.srCore.srConfig.PLEX_SERVER_HOST != "":
                                <li>
                                    <a href="${srWebRoot}/home/updatePLEX/">
                                        <i class="menu-icon-backlog-view"></i>&nbsp;Update PLEX
                                    </a>
                                </li>
                            % endif
                            % if sickrage.srCore.srConfig.USE_KODI and sickrage.srCore.srConfig.KODI_HOST != "":
                                <li>
                                    <a href="${srWebRoot}/home/updateKODI/">
                                        <i class="menu-icon-kodi"></i>&nbsp;Update KODI
                                    </a>
                                </li>
                            % endif
                            % if sickrage.srCore.srConfig.USE_EMBY and sickrage.srCore.srConfig.EMBY_HOST != "" and sickrage.srCore.srConfig.EMBY_APIKEY != "":
                                <li>
                                    <a href="${srWebRoot}/home/updateEMBY/">
                                        <i class="menu-icon-backlog-view"></i>&nbsp;Update Emby
                                    </a>
                                </li>
                            % endif
                            % if sickrage.srCore.srConfig.USE_TORRENTS and sickrage.srCore.srConfig.TORRENT_METHOD != 'blackhole' and (sickrage.srCore.srConfig.ENABLE_HTTPS and sickrage.srCore.srConfig.TORRENT_HOST[:5] == 'https' or not sickrage.srCore.srConfig.ENABLE_HTTPS and sickrage.srCore.srConfig.TORRENT_HOST[:5] == 'http:'):
                                <li>
                                    <a href="${srWebRoot}/manage/manageTorrents/">
                                        <i class="menu-icon-bittorrent"></i>&nbsp;Manage Torrents
                                    </a>
                                </li>
                            % endif
                            % if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
                                <li>
                                    <a href="${srWebRoot}/manage/failedDownloads/">
                                        <i class="menu-icon-failed-download"></i>&nbsp;Failed Downloads
                                    </a>
                                </li>
                            % endif
                            % if sickrage.srCore.srConfig.USE_SUBTITLES:
                                <li>
                                    <a href="${srWebRoot}/manage/subtitleMissed/">
                                        <i class="menu-icon-backlog"></i>&nbsp;Missed Subtitle Management
                                    </a>
                                </li>
                            % endif
                        </ul>
                        <div style="clear:both;"></div>
                    </li>

                    <li id="NAVschedule"${('', ' class="active"')[topmenu == 'schedule']}>
                        <a href="${srWebRoot}/schedule/">Schedule</a>
                    </li>

                    <li id="NAVhistory"${('', ' class="active"')[topmenu == 'history']}>
                        <a href="${srWebRoot}/history/">History</a>
                    </li>

                    <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                        <a href="${srWebRoot}/config/" class="dropdown-toggle" aria-haspopup="true"
                           data-toggle="dropdown"
                           data-hover="dropdown"><span class="visible-xs">Config</span><img
                                src="${srWebRoot}/images/menu/system18.png" class="navbaricon hidden-xs"/>
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a href="${srWebRoot}/config/">
                                    <i class="menu-icon-help"></i>&nbsp;Help &amp; Info
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/general/">
                                    <i class="menu-icon-config"></i>&nbsp;General
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/backuprestore/">
                                    <i class="menu-icon-config"></i>&nbsp;Backup &amp; Restore
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/search/">
                                    <i class="menu-icon-config"></i>&nbsp;Search Clients
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/providers/">
                                    <i class="menu-icon-config"></i>&nbsp;Search Providers
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/subtitles/">
                                    <i class="menu-icon-config"></i>&nbsp;Subtitles Settings
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/qualitySettings/">
                                    <i class="menu-icon-config"></i>&nbsp;Quality Settings
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/postProcessing/">
                                    <i class="menu-icon-config"></i>&nbsp;Post Processing
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/notifications/">
                                    <i class="menu-icon-config"></i>&nbsp;Notifications
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/config/anime/">
                                    <i class="menu-icon-config"></i>&nbsp;Anime
                                </a>
                            </li>
                        </ul>
                        <div style="clear:both;"></div>
                    </li>

                    <%
                        numCombined = numErrors + numWarnings
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

                    <li id="NAVsystem" class="navbar-split dropdown${('', ' active')[topmenu == 'system']}">
                        <a href="${srWebRoot}/home/status/" class="dropdown-toggle" aria-haspopup="true"
                           data-toggle="dropdown"
                           data-hover="dropdown"><span class="visible-xs">Tools</span><img
                                src="${srWebRoot}/images/menu/system18-2.png"
                                class="navbaricon hidden-xs"/>${toolsBadge}
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a href="${srWebRoot}/IRC/">
                                    <i class="menu-icon-help"></i>&nbsp;IRC
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/changes/">
                                    <i class="menu-icon-help"></i>&nbsp;Changelog
                                </a>
                            </li>
                            <li>
                                <a href="https://www.gofundme.com/sickrage/donate" rel="noreferrer"
                                   onclick="window.open('${sickrage.srCore.srConfig.ANON_REDIRECT}' + this.href); return false;">
                                    <i class="menu-icon-help"></i>&nbsp;Support SickRage
                                </a>
                            </li>
                            <li class="divider"></li>
                            %if numErrors:
                                <li>
                                    <a href="${srWebRoot}/logs/">
                                        <i class="menu-icon-viewlog-errors"></i>&nbsp;View Errors
                                        <span class="badge btn-danger">${numErrors}</span>
                                    </a>
                                </li>
                            %endif
                            %if numWarnings:
                                <li>
                                    <a href="${srWebRoot}/logs/?level=${sickrage.srCore.srLogger.WARNING}">
                                        <i class="menu-icon-viewlog-errors"></i>&nbsp;View Warnings
                                        <span class="badge btn-warning">${numWarnings}</span>
                                    </a>
                                </li>
                            %endif
                            <li>
                                <a href="${srWebRoot}/logs/viewlog/">
                                    <i class="menu-icon-viewlog"></i>&nbsp;View Log
                                </a>
                            </li>
                            <li class="divider"></li>
                            <li>
                                <a href="${srWebRoot}/home/updateCheck?pid=${srPID}">
                                    <i class="menu-icon-update"></i>&nbsp;Check For Updates
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/home/restart/?pid=${srPID}" class="confirm restart">
                                    <i class="menu-icon-restart"></i>&nbsp;Restart
                                </a>
                            </li>
                            <li>
                                <a href="${srWebRoot}/home/shutdown/?pid=${srPID}" class="confirm shutdown">
                                    <i class="menu-icon-shutdown"></i>&nbsp;Shutdown
                                </a>
                            </li>
                            % if current_user != True:
                                <li>
                                    <a href="${srWebRoot}/logout" class="confirm logout">
                                        <i class="menu-icon-shutdown"></i>&nbsp;Logout
                                    </a>
                                </li>
                            % endif
                            <li class="divider"></li>
                            <li>
                                <a href="${srWebRoot}/home/status/">
                                    <i class="menu-icon-help"></i>&nbsp;Server Status
                                </a>
                            </li>
                        </ul>
                        <div style="clear:both;"></div>
                    </li>
                </ul>
            </div>
        % endif
    </div>
</nav>

<div class="container-fluid">
    <div id="sub-menu-container" class="row">
        % if submenu:
            <div id="sub-menu" class="hidden-print">
                <% first = True %>
                % for menuItem in reversed(submenu):
                    % if menuItem.get('requires', 1):
                        % if isinstance(menuItem['path'], dict):
                        ${("</span><span>", "")[bool(first)]}<b>${menuItem['title']}</b>
                        <%
                            first = False
                            inner_first = True
                        %>
                        % for cur_link in menuItem['path']:
                        ${("&middot;", "")[bool(inner_first)]}<a href="${srWebRoot}${menuItem['path'][cur_link]}"
                                                                 class="inner ${menuItem.get('class', '')}">${cur_link}</a>
                        <% inner_first = False %>
                        % endfor
                        % else:
                            <a href="${srWebRoot}${menuItem['path']}"
                               class="btn ${('', ' confirm ')['confirm' in menuItem]} ${menuItem.get('class', '')}">
                                <i class='${menuItem.get('icon', '')}'></i> ${menuItem['title']}
                            </a>
                        <% first = False %>
                        % endif
                    % endif
                % endfor
            </div>
        % endif
    </div>

    % if sickrage.srCore.NEWEST_VERSION_STRING and current_user:
        <div class="row">
            <div class="col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                <div class="alert alert-success upgrade-notification">
                    <span>${sickrage.srCore.NEWEST_VERSION_STRING}</span>
                </div>
            </div>
        </div>
    % endif

    <div class="row">
        <div class="col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                <%block name="content" />
        </div>
    </div>

    % if current_user:
        <div class="row">
            <div class="footer text-center clearfix col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                <%
                    stats = overall_stats()
                    ep_downloaded = stats['episodes']['downloaded']
                    ep_snatched = stats['episodes']['snatched']
                    ep_total = stats['episodes']['total']
                    ep_percentage = '' if ep_total == 0 else '(<span class="footer-highlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
                %>
                <div>
                    <span class="footer-highlight">${stats['shows']['total']}</span> Shows (<span
                        class="footer-highlight">${stats['shows']['active']}</span> Active)
                    | <span class="footer-highlight">${ep_downloaded}</span>

                    % if ep_snatched:
                        <span class="footer-highlight"><a
                                href="${srWebRoot}/manage/episodeStatuses?whichStatus=2">+${ep_snatched}</a></span>
                        Snatched
                    % endif

                    &nbsp;/&nbsp;<span class="footer-highlight">${ep_total}</span> Episodes Downloaded ${ep_percentage}
                    | Daily Search: <span
                        class="footer-highlight">${str(sickrage.srCore.srScheduler.get_job('DAILYSEARCHER').next_run_time).split('.')[0]}</span>
                    | Backlog Search: <span
                        class="footer-highlight">${str(sickrage.srCore.srScheduler.get_job('BACKLOG').next_run_time).split('.')[0]}</span>
                </div>

                <div>
                    % if has_resource_module:
                        Memory used: <span
                            class="footer-highlight">${pretty_filesize(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}</span>
                        |
                    % endif
                    Load time: <span class="footer-highlight">${"%.4f" % (time() - srStartTime)}s</span> / Mako:
                    <span
                            class="footer-highlight">${"%.4f" % (time() - makoStartTime)}s</span> |
                    Now: <span
                        class="footer-highlight">${str(datetime.datetime.now(tz_updater.sr_timezone)).split('.')[0]}</span>
                </div>
            </div>
        </div>
    % endif
</div>
</body>
</html>
