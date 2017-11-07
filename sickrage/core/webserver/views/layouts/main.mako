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
    <title>${_('SiCKRAGE')} - ${title}</title>

    <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <meta charset="utf-8">
    <meta name="robots" content="noindex, nofollow">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=0.5, user-scalable=no">

    % if sickrage.app.srConfig.THEME_NAME == "dark":
        <meta name="theme-color" content="#15528F">
    % elif sickrage.app.srConfig.THEME_NAME == "light":
        <meta name="theme-color" content="#333333">
    % endif

    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="${srWebRoot}/images/ico/ms-icon-144x144.png">
    <meta name="msapplication-config" content="${srWebRoot}/images/ico/browserconfig.xml">

    <meta data-var="srPID" data-content="${srPID}">
    <meta data-var="srDefaultPage" data-content="${srDefaultPage}">
    <meta data-var="srWebRoot" data-content="${srWebRoot}">
    <meta data-var="themeSpinner" data-content="${('', '-dark')[sickrage.app.srConfig.THEME_NAME == 'dark']}">
    <meta data-var="anonURL" data-content="${sickrage.app.srConfig.ANON_REDIRECT}">
    <meta data-var="sickrage.ANIME_SPLIT_HOME" data-content="${sickrage.app.srConfig.ANIME_SPLIT_HOME}">
    <meta data-var="sickrage.COMING_EPS_LAYOUT" data-content="${sickrage.app.srConfig.COMING_EPS_LAYOUT}">
    <meta data-var="sickrage.COMING_EPS_SORT" data-content="${sickrage.app.srConfig.COMING_EPS_SORT}">
    <meta data-var="sickrage.DATE_PRESET" data-content="${sickrage.app.srConfig.DATE_PRESET}">
    <meta data-var="sickrage.FILTER_ROW" data-content="${sickrage.app.srConfig.FILTER_ROW}">
    <meta data-var="sickrage.FUZZY_DATING" data-content="${sickrage.app.srConfig.FUZZY_DATING}">
    <meta data-var="sickrage.HISTORY_LAYOUT" data-content="${sickrage.app.srConfig.HISTORY_LAYOUT}">
    <meta data-var="sickrage.HOME_LAYOUT" data-content="${sickrage.app.srConfig.HOME_LAYOUT}">
    <meta data-var="sickrage.POSTER_SORTBY" data-content="${sickrage.app.srConfig.POSTER_SORTBY}">
    <meta data-var="sickrage.POSTER_SORTDIR" data-content="${sickrage.app.srConfig.POSTER_SORTDIR}">
    <meta data-var="sickrage.ROOT_DIRS" data-content="${sickrage.app.srConfig.ROOT_DIRS}">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.app.srConfig.SORT_ARTICLE}">
    <meta data-var="sickrage.TIME_PRESET" data-content="${sickrage.app.srConfig.TIME_PRESET}">
    <meta data-var="sickrage.TRIM_ZERO" data-content="${sickrage.app.srConfig.TRIM_ZERO}">
    <meta data-var="sickrage.FANART_BACKGROUND" data-content="${sickrage.app.srConfig.FANART_BACKGROUND}">
    <meta data-var="sickrage.FANART_BACKGROUND_OPACITY"
          data-content="${sickrage.app.srConfig.FANART_BACKGROUND_OPACITY}">
    <%block name="metas" />

    <link rel="icon" type="image/png" sizes="32x32" href="${srWebRoot}/images/favicon.png">

    % if sickrage.app.srConfig.GUI_LANG:
        <link rel="gettext" type="application/json" href="${srWebRoot}/messages.json">
    % endif

    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/bower.min.css"/>
    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css"/>
    <link rel="stylesheet" type="text/css"
          href="${srWebRoot}/css/themes/${sickrage.app.srConfig.THEME_NAME}.min.css"/>
    <%block name="css" />
</head>
<body data-controller="${controller}" data-action="${action}">
    % if current_user:
        <nav class="navbar navbar-default navbar-fixed-top">
            <div class="container-fluid">
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse"
                            data-target="#navbar-collapse-1" aria-expanded="false">
                        <span class="sr-only">${_('Toggle navigation')}</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                    <a class="navbar-brand" href="${srWebRoot}/home/">
                        <img alt="SiCKRAGE"
                             src="${srWebRoot}/images/logo.png"
                             style="width: 400px;height: 50px;"
                             class="img-responsive pull-left"/>
                    </a>
                </div>
                <div class="collapse navbar-collapse" id="navbar-collapse-1">
                    <ul class="nav navbar-nav navbar-right">
                        <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                            <a href="${srWebRoot}/home/" class="dropdown-toggle" aria-haspopup="true"
                               data-toggle="dropdown" data-hover="dropdown"><span>${_('Shows')}</span>
                            </a>
                            <ul class="dropdown-menu">
                                <li>
                                    <a href="${srWebRoot}/home/">
                                        <i class="menu-icon-home"></i>&nbsp;${_('Show List')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/home/addShows/">
                                        <i class="menu-icon-addshow"></i>&nbsp;${_('Add Shows')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/home/postprocess/">
                                        <i class="menu-icon-postprocess"></i>&nbsp;${_('Manual Post-Processing')}
                                    </a>
                                </li>
                                % if sickrage.app.srConfig.SHOWS_RECENT:
                                    <li class="divider"></li>
                                % for recentShow in sickrage.app.srConfig.SHOWS_RECENT:
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
                            <a href="${srWebRoot}/manage/episodeStatuses/" class="dropdown-toggle"
                               aria-haspopup="true"
                               data-toggle="dropdown" data-hover="dropdown">
                                <span>Manage</span>
                            </a>
                            <ul class="dropdown-menu">
                                <li>
                                    <a href="${srWebRoot}/manage/">
                                        <i class="menu-icon-manage"></i>&nbsp;${_('Mass Update')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/manage/backlogOverview/">
                                        <i class="menu-icon-backlog-view"></i>&nbsp;${_('Backlog Overview')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/manage/manageQueues/">
                                        <i class="menu-icon-manage-searches"></i>&nbsp;${_('Manage Queues')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/manage/episodeStatuses/">
                                        <i class="menu-icon-backlog"></i>&nbsp;${_('Episode Status Management')}
                                    </a>
                                </li>
                                % if sickrage.app.srConfig.USE_TRAKT and sickrage.app.srConfig.TRAKT_OAUTH_TOKEN != "":
                                    <li>
                                        <a href="${srWebRoot}/home/syncTrakt/">
                                            <i class="menu-icon-backlog-view"></i>&nbsp;${_('Sync Trakt')}
                                        </a>
                                    </li>
                                % endif
                                % if sickrage.app.srConfig.USE_PLEX and sickrage.app.srConfig.PLEX_SERVER_HOST != "":
                                    <li>
                                        <a href="${srWebRoot}/home/updatePLEX/">
                                            <i class="menu-icon-backlog-view"></i>&nbsp;${_('Update PLEX')}
                                        </a>
                                    </li>
                                % endif
                                % if sickrage.app.srConfig.USE_KODI and sickrage.app.srConfig.KODI_HOST != "":
                                    <li>
                                        <a href="${srWebRoot}/home/updateKODI/">
                                            <i class="menu-icon-kodi"></i>&nbsp;${_('Update KODI')}
                                        </a>
                                    </li>
                                % endif
                                % if sickrage.app.srConfig.USE_EMBY and sickrage.app.srConfig.EMBY_HOST != "" and sickrage.app.srConfig.EMBY_APIKEY != "":
                                    <li>
                                        <a href="${srWebRoot}/home/updateEMBY/">
                                            <i class="menu-icon-backlog-view"></i>&nbsp;${_('Update Emby')}
                                        </a>
                                    </li>
                                % endif
                                % if torrent_webui_url:
                                    <li>
                                        <a href="${torrent_webui_url}" target="_blank">
                                            <i class="menu-icon-bittorrent"></i>&nbsp;${_('Manage Torrents')}
                                        </a>
                                    </li>
                                % endif
                                % if sickrage.app.srConfig.USE_FAILED_DOWNLOADS:
                                    <li>
                                        <a href="${srWebRoot}/manage/failedDownloads/">
                                            <i class="menu-icon-failed-download"></i>&nbsp;${_('Failed Downloads')}
                                        </a>
                                    </li>
                                % endif
                                % if sickrage.app.srConfig.USE_SUBTITLES:
                                    <li>
                                        <a href="${srWebRoot}/manage/subtitleMissed/">
                                            <i class="menu-icon-backlog"></i>&nbsp;${_('Missed Subtitle Management')}
                                        </a>
                                    </li>
                                % endif
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <li id="NAVschedule"${('', ' class="active"')[topmenu == 'schedule']}>
                            <a href="${srWebRoot}/schedule/">${_('Schedule')}</a>
                        </li>

                        <li id="NAVhistory"${('', ' class="active"')[topmenu == 'history']}>
                            <a href="${srWebRoot}/history/">${_('History')}</a>
                        </li>

                        <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                            <a href="${srWebRoot}/config/" class="dropdown-toggle" aria-haspopup="true"
                               data-toggle="dropdown"
                               data-hover="dropdown"><span class="visible-xs">${_('Config')}</span><img
                                    src="${srWebRoot}/images/menu/system18.png" class="navbaricon hidden-xs"/>
                            </a>
                            <ul class="dropdown-menu">
                                <li>
                                    <a href="${srWebRoot}/config/">
                                        <i class="fa fa-info"></i>&nbsp;${_('Help and Info')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/general/">
                                        <i class="fa fa-cogs"></i>&nbsp;${_('General')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/backuprestore/">
                                        <i class="fa fa-upload"></i>&nbsp;${_('Backup and Restore')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/search/">
                                        <i class="fa fa-binoculars"></i>&nbsp;${_('Search Clients')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/providers/">
                                        <i class="fa fa-share-alt"></i>&nbsp;${_('Search Providers')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/subtitles/">
                                        <i class="fa fa-cc"></i>&nbsp;${_('Subtitles Settings')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/qualitySettings/">
                                        <i class="fa fa-wrench"></i>&nbsp;${_('Quality Settings')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/postProcessing/">
                                        <i class="fa fa-refresh"></i>&nbsp;${_('Post Processing')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/notifications/">
                                        <i class="fa fa-bell"></i>&nbsp;${_('Notifications')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/config/anime/">
                                        <i class="fa fa-eye"></i>&nbsp;${_('Anime')}
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
                               data-hover="dropdown"><span class="visible-xs">${_('Tools')}</span><img
                                    src="${srWebRoot}/images/menu/system18-2.png"
                                    class="navbaricon hidden-xs"/>${toolsBadge}
                            </a>
                            <ul class="dropdown-menu">
                                <li>
                                    <a href="${srWebRoot}/IRC/">
                                        <i class="fa fa-hashtag"></i>&nbsp;${_('IRC')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/changes/">
                                        <i class="fa fa-globe"></i>&nbsp;${_('Changelog')}
                                    </a>
                                </li>
                                <li>
                                    <a href="https://www.gofundme.com/sickrage/donate" rel="noreferrer"
                                       onclick="window.open('${sickrage.app.srConfig.ANON_REDIRECT}' + this.href); return false;">
                                        <i class="fa fa-money"></i>&nbsp;${_('Donate')}
                                    </a>
                                </li>
                                <li class="divider"></li>
                                %if numErrors:
                                    <li>
                                        <a href="${srWebRoot}/logs/">
                                            <i class="fa fa-exclamation-circle"></i>&nbsp;${_('View Errors')}
                                            <span class="badge btn-danger">${numErrors}</span>
                                        </a>
                                    </li>
                                %endif
                                %if numWarnings:
                                    <li>
                                        <a href="${srWebRoot}/logs/?level=${sickrage.app.log.WARNING}">
                                            <i class="fa fa-exclamation-triangle"></i>&nbsp;${_('View Warnings')}
                                            <span class="badge btn-warning">${numWarnings}</span>
                                        </a>
                                    </li>
                                %endif
                                <li>
                                    <a href="${srWebRoot}/logs/viewlog/">
                                        <i class="fa fa-file-text-o"></i>&nbsp;${_('View Log')}
                                    </a>
                                </li>
                                <li class="divider"></li>
                                <li>
                                    <a href="${srWebRoot}/home/updateCheck?pid=${srPID}">
                                        <i class="fa fa-check-square"></i>&nbsp;${_('Check For Updates')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/home/restart/?pid=${srPID}" class="confirm restart">
                                        <i class="fa fa-repeat"></i>&nbsp;${_('Restart')}
                                    </a>
                                </li>
                                <li>
                                    <a href="${srWebRoot}/home/shutdown/?pid=${srPID}" class="confirm shutdown">
                                        <i class="fa fa-power-off"></i>&nbsp;${_('Shutdown')}
                                    </a>
                                </li>
                                % if current_user != True:
                                    <li>
                                        <a href="${srWebRoot}/logout" class="confirm logout">
                                            <i class="fa fa-sign-out"></i>&nbsp;${_('Logout')}
                                        </a>
                                    </li>
                                % endif
                                <li class="divider"></li>
                                <li>
                                    <a href="${srWebRoot}/home/status/">
                                        <i class="fa fa-server"></i>&nbsp;${_('Server Status')}
                                    </a>
                                </li>
                            </ul>
                            <div style="clear:both;"></div>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    % endif

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

    % if current_user and sickrage.app.NEWEST_VERSION_STRING:
        <div class="row">
            <div class="col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                <div class="alert alert-success upgrade-notification text-center">
                    <span>${sickrage.app.NEWEST_VERSION_STRING}</span>
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
                    total_size = pretty_filesize(stats['total_size'])
                    ep_downloaded = stats['episodes']['downloaded']
                    ep_snatched = stats['episodes']['snatched']
                    ep_total = stats['episodes']['total']
                    ep_percentage = '' if ep_total == 0 else '(<span class="footer-highlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
                %>
                <div>
                    <span class="footer-highlight">${stats['shows']['total']}</span> ${_('Shows')} (<span
                        class="footer-highlight">${stats['shows']['active']}</span> ${_('Active')})
                    | <span class="footer-highlight">${ep_downloaded}</span>

                    % if ep_snatched:
                        <span class="footer-highlight">
                            <a href="${srWebRoot}/manage/episodeStatuses?whichStatus=2">+${ep_snatched}</a>
                        </span>
                    ${_('Snatched')}
                    % endif

                    &nbsp;/&nbsp;<span
                        class="footer-highlight">${ep_total}</span> ${_('Episodes Downloaded')} ${ep_percentage}
                    &nbsp;/&nbsp;<span class="footer-highlight">${total_size}</span> ${_('Overall Downloaded')}
                    | ${_('Daily Search:')} <span
                        class="footer-highlight">${str(sickrage.app.srScheduler.get_job('DAILYSEARCHER').next_run_time).split('.')[0]}</span>
                    | ${_('Backlog Search:')} <span
                        class="footer-highlight">${str(sickrage.app.srScheduler.get_job('BACKLOG').next_run_time).split('.')[0]}</span>
                </div>

                <div>
                    % if has_resource_module:
                    ${_('Memory used:')}
                        <span class="footer-highlight">
                            ${pretty_filesize(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
                        </span> |
                    % endif
                    ${_('Load time:')}
                    <span class="footer-highlight">
                        ${"{:10.4f}".format(time() - srStartTime)}s
                    </span> / Mako:
                    <span class="footer-highlight">
                        ${"{:10.4f}".format(time() - makoStartTime)}s
                    </span> |
                    ${_('Now:')}
                    <span class="footer-highlight">
                        ${str(datetime.datetime.now(tz_updater.sr_timezone)).split('.')[0]}
                    </span>
                </div>
            </div>
        </div>
    % endif

    <script src="${srWebRoot}/js/bower.min.js"></script>
    <script src="${srWebRoot}/js/core.min.js"></script>
    <%block name="scripts" />
</div>
</body>
</html>
