<%!
    import datetime
    import re
    from hashlib import md5
    from time import time

    import sickrage
    from sickrage.core import API
    from sickrage.core.updaters import tz_updater
    from sickrage.core.helpers import pretty_filesize, memory_usage
%>

<%namespace file="../includes/modals.mako" import="mainModals"/>

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

    % if sickrage.app.config.theme_name == "dark":
        <meta name="theme-color" content="#15528F">
    % elif sickrage.app.config.theme_name == "light":
        <meta name="theme-color" content="#333333">
    % endif

    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="${srWebRoot}/images/ico/ms-icon-144x144.png">
    <meta name="msapplication-config" content="${srWebRoot}/images/ico/browserconfig.xml">

    <meta data-var="srPID" data-content="${srPID}">
    <meta data-var="srDefaultPage" data-content="${srDefaultPage}">
    <meta data-var="srWebRoot" data-content="${srWebRoot}">
    <meta data-var="themeSpinner" data-content="${('', '-dark')[sickrage.app.config.theme_name == 'dark']}">
    <meta data-var="anonURL" data-content="${sickrage.app.config.anon_redirect}">
    <meta data-var="srLocale" data-content="${srLocale}">
    <meta data-var="srLocaleDir" data-content="${srLocaleDir}">
    <meta data-var="sickrage.ANIME_SPLIT_HOME" data-content="${sickrage.app.config.anime_split_home}">
    <meta data-var="sickrage.COMING_EPS_LAYOUT" data-content="${sickrage.app.config.coming_eps_layout}">
    <meta data-var="sickrage.COMING_EPS_SORT" data-content="${sickrage.app.config.coming_eps_sort}">
    <meta data-var="sickrage.DATE_PRESET" data-content="${sickrage.app.config.date_preset}">
    <meta data-var="sickrage.FILTER_ROW" data-content="${sickrage.app.config.filter_row}">
    <meta data-var="sickrage.FUZZY_DATING" data-content="${sickrage.app.config.fuzzy_dating}">
    <meta data-var="sickrage.HISTORY_LAYOUT" data-content="${sickrage.app.config.history_layout}">
    <meta data-var="sickrage.HOME_LAYOUT" data-content="${sickrage.app.config.home_layout}">
    <meta data-var="sickrage.POSTER_SORTBY" data-content="${sickrage.app.config.poster_sortby}">
    <meta data-var="sickrage.POSTER_SORTDIR" data-content="${sickrage.app.config.poster_sortdir}">
    <meta data-var="sickrage.ROOT_DIRS" data-content="${sickrage.app.config.root_dirs}">
    <meta data-var="sickrage.SORT_ARTICLE" data-content="${sickrage.app.config.sort_article}">
    <meta data-var="sickrage.TIME_PRESET" data-content="${sickrage.app.config.time_preset}">
    <meta data-var="sickrage.TRIM_ZERO" data-content="${sickrage.app.config.trim_zero}">
    <meta data-var="sickrage.VIEW_CHANGELOG" data-content="${sickrage.app.config.view_changelog}">
    <meta data-var="sickrage.FANART_BACKGROUND" data-content="${sickrage.app.config.fanart_background}">
    <meta data-var="sickrage.FANART_BACKGROUND_OPACITY"
          data-content="${sickrage.app.config.fanart_background_opacity}">
    <%block name="metas" />

    <link rel="icon" type="image/png" sizes="32x32" href="${srWebRoot}/images/favicon.png">

    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css"/>
    <%block name="css" />
</head>
<body data-controller="${controller}" data-action="${action}">
    ${mainModals()}
    <%block name="modals" />

    % if current_user:
        <%
            numCombined = numErrors + numWarnings
            if numCombined:
                toolsBadgeClass = ''
                if numErrors:
                    toolsBadgeClass = 'badge-danger'
                elif numWarnings:
                    toolsBadgeClass = 'badge-warning'

                toolsBadge = '<span class="badge badge-pill ' + toolsBadgeClass + '" style="float:right;margin-bottom:-10px;">' + str(numCombined) + '</span>'
            else:
                toolsBadge = ''
        %>

        % if current_user and sickrage.app.newest_version_string:
            <div class="alert alert-success alert-dismissible fade show text-center m-0 rounded-0">
                <strong>${sickrage.app.newest_version_string}</strong>
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        % endif

        <nav class="navbar navbar-expand-lg navbar-dark navbar-default py-0">
            <div class="container-fluid">
                <a class="navbar-brand" href="${srWebRoot}/home/">
                    <img alt="SiCKRAGE" src="${srWebRoot}/images/logo.png" style="width: 400px;height: 50px;"/>
                </a>
                <button class="navbar-toggler" type="button" data-toggle="collapse"
                        data-target="#navbarSupportedContent"
                        aria-controls="navbarSupportedContent" aria-expanded="false"
                        aria-label="{{ __('Toggle navigation') }}">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div align="center" class="collapse navbar-collapse" id="navbarSupportedContent">
                    <!-- Left Side Of Navbar -->
                    <ul class="navbar-nav mr-auto">
                        <li>
                            <div class="input-group input-group-lg">
                                <div class="input-group-prepend">
                                    <div class="input-group-text bg-dark text-white-50" style="border: none">
                                        <i class="fas fa-search"></i>
                                    </div>
                                </div>
                                <input id="quicksearch" class="form-control bg-dark text-white-50"
                                       style="width:350px;border: none;" type="search">
                                <div class="input-group-append">
                                    <div class="input-group-text bg-dark text-white-50" style="border: none">
                                        <i id="quicksearch-icon"></i>
                                    </div>
                                </div>
                            </div>
                        </li>
                    </ul>

                    <!-- Right Side Of Navbar -->
                    <ul class="navbar-nav align-items-center ml-auto">
                        <li class="nav-item dropdown${('', ' active')[topmenu == 'home']}">
                            <a id="navbarHome" class="nav-link dropdown-toggle" href="#" role="button"
                               aria-haspopup="true" data-toggle="dropdown" aria-expanded="false">
                                <span>
                                    ${_('Shows')}
                                </span>
                            </a>
                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarHome">
                                <a class="dropdown-item" href="${srWebRoot}/home/">
                                    <i class="fas fa-home"></i>&nbsp;${_('Show List')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/addShows/">
                                    <i class="fas fa-tv"></i>&nbsp;${_('Add Shows')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/postprocess/">
                                    <i class="fas fa-folder-open"></i>&nbsp;${_('Manual Post-Processing')}
                                </a>
                                % if sickrage.app.config.shows_recent:
                                    <div class="dropdown-divider"></div>
                                % for recentShow in sickrage.app.config.shows_recent:
                                    <a class="dropdown-item"
                                       href="${srWebRoot}/home/displayShow/?show=${recentShow['indexerid']}">
                                        <i class="fas fa-tv"></i>&nbsp;${recentShow['name']|trim,h}
                                    </a>
                                % endfor
                                % endif
                            </div>
                        </li>

                        <li class="nav-item dropdown${('', ' active')[topmenu == 'manage']}">
                            <a id="navbarManage" class="nav-link dropdown-toggle" href="#" role="button"
                               aria-haspopup="true" data-toggle="dropdown" aria-expanded="false">
                            <span>
                                ${_('Manage')}
                            </span>
                            </a>
                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarSystem">
                                <a class="dropdown-item" href="${srWebRoot}/manage/">
                                    <i class="fas fa-diagnoses"></i>&nbsp;${_('Mass Update')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/backlogOverview/">
                                    <i class="fas fa-backward"></i>&nbsp;${_('Backlog Overview')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/manageQueues/">
                                    <i class="fas fa-list"></i>&nbsp;${_('Manage Queues')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/episodeStatuses/">
                                    <i class="fas fa-th-list"></i>&nbsp;${_('Episode Status Management')}
                                </a>
                                % if sickrage.app.config.use_trakt and sickrage.app.config.trakt_oauth_token != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/syncTrakt/">
                                        <i class="fas fa-sync"></i>&nbsp;${_('Sync Trakt')}
                                    </a>
                                % endif
                                % if sickrage.app.config.use_plex and sickrage.app.config.plex_server_host != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/updatePLEX/">
                                        <i class="fas fa-sync"></i>&nbsp;${_('Update PLEX')}
                                    </a>
                                % endif
                                % if sickrage.app.config.use_kodi and sickrage.app.config.kodi_host != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/updateKODI/">
                                        <i class="fas fa-sync"></i>&nbsp;${_('Update KODI')}
                                    </a>
                                % endif
                                % if sickrage.app.config.use_emby and sickrage.app.config.emby_host != "" and sickrage.app.config.emby_apikey != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/updateEMBY/">
                                        <i class="fas fa-sync"></i>&nbsp;${_('Update Emby')}
                                    </a>
                                % endif
                                % if torrent_webui_url:
                                    <a class="dropdown-item" href="${torrent_webui_url}" target="_blank">
                                        <i class="fas fa-video"></i>&nbsp;${_('Manage Torrents')}
                                    </a>
                                % endif
                                <a class="dropdown-item" href="${srWebRoot}/manage/failedDownloads/">
                                    <i class="fas fa-first-aid"></i>&nbsp;${_('Failed Downloads')}
                                </a>
                                % if sickrage.app.config.use_subtitles:
                                    <a class="dropdown-item" href="${srWebRoot}/manage/subtitleMissed/">
                                        <i class="fas fa-question"></i>&nbsp;${_('Missed Subtitle Management')}
                                    </a>
                                % endif
                            </div>
                        </li>

                        <li id="navbarSchedule" class="nav-item ${('', ' active')[topmenu == 'schedule']}">
                            <a class="nav-link" href="${srWebRoot}/schedule/">${_('Schedule')}</a>
                        </li>

                        <li id="navbarHistory" class="nav-item ${('', ' active')[topmenu == 'history']}">
                            <a class="nav-link" href="${srWebRoot}/history/">${_('History')}</a>
                        </li>

                        <li class="nav-item dropdown${('', ' active')[topmenu == 'config']}">
                            <a id="navbarConfig" class="nav-link" href="${srWebRoot}/config/" role="button"
                               aria-haspopup="true" data-toggle="dropdown" aria-expanded="false">
                                <span class="d-none d-sm-block dropdown-toggle d-md-none">
                                    ${_('Config')}
                                </span>
                                <span class="d-sm-none d-md-block">
                                    <i class="fas fa-2x fa-cogs"></i>
                                </span>
                            </a>

                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarConfig">
                                <a class="dropdown-item" href="${srWebRoot}/config/">
                                    <i class="fas fa-info"></i>&nbsp;${_('Help and Info')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/general/">
                                    <i class="fas fa-wrench"></i>&nbsp;${_('General')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/backuprestore/">
                                    <i class="fas fa-upload"></i>&nbsp;${_('Backup and Restore')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/search/">
                                    <i class="fas fa-binoculars"></i>&nbsp;${_('Search Clients')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/providers/">
                                    <i class="fas fa-share-alt"></i>&nbsp;${_('Search Providers')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/subtitles/">
                                    <i class="fas fa-closed-captioning"></i>&nbsp;${_('Subtitles Settings')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/qualitySettings/">
                                    <i class="fas fa-wrench"></i>&nbsp;${_('Quality Settings')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/postProcessing/">
                                    <i class="fas fa-folder-open"></i>&nbsp;${_('Post Processing')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/notifications/">
                                    <i class="fas fa-bell"></i>&nbsp;${_('Notifications')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/anime/">
                                    <i class="fas fa-eye"></i>&nbsp;${_('Anime')}
                                </a>
                            </div>
                        </li>

                        <li class="nav-item dropdown${('', ' active')[topmenu == 'system']}">
                            <a id="navbarSystem" class="nav-link" href="#" role="button"
                               aria-haspopup="true" data-toggle="dropdown" aria-expanded="false">
                                <span class="d-none d-sm-block dropdown-toggle d-md-none">
                                    ${_('Tools')}
                                </span>
                                <span class="d-sm-none d-md-block">
                                    <img class="rounded-circle shadow"
                                         src="https://gravatar.com/avatar/${md5(current_user['email']).hexdigest()}?d=mm&s=40"/>
                                    ${toolsBadge}
                                </span>
                            </a>

                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarSystem">
                                <a class="dropdown-item" href="${srWebRoot}/IRC/">
                                    <i class="fas fa-hashtag"></i>&nbsp;${_('IRC')}
                                </a>
                                <a class="dropdown-item" href="#" id="changelog">
                                    <i class="fas fa-globe"></i>&nbsp;${_('Changelog')}
                                </a>
                                <a class="dropdown-item" href="https://www.sickrage.ca/forums/donate" rel="noreferrer"
                                   onclick="window.open('${sickrage.app.config.anon_redirect}' + this.href); return false;">
                                    <i class="fas fa-donate"></i>&nbsp;${_('Donate')}
                                </a>
                                <div class="dropdown-divider"></div>
                                %if numErrors:
                                    <a class="dropdown-item" href="${srWebRoot}/logs/">
                                        <i class="fas fa-exclamation-circle"></i>&nbsp;${_('View Errors')}
                                        <span class="badge badge-danger">${numErrors}</span>
                                    </a>
                                %endif
                                %if numWarnings:
                                    <a class="dropdown-item"
                                       href="${srWebRoot}/logs/?level=${sickrage.app.log.WARNING}">
                                        <i class="fas fa-exclamation-triangle"></i>&nbsp;${_('View Warnings')}
                                        <span class="badge badge-warning">${numWarnings}</span>
                                    </a>
                                %endif
                                <a class="dropdown-item" href="${srWebRoot}/logs/viewlog/">
                                    <i class="fas fa-file-archive"></i>&nbsp;${_('View Log')}
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item" href="${srWebRoot}/home/updateCheck?pid=${srPID}">
                                    <i class="fas fa-check-square"></i>&nbsp;${_('Check For Updates')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/restart/?pid=${srPID}"
                                   class="confirm restart">
                                    <i class="fas fa-redo"></i>&nbsp;${_('Restart')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/shutdown/?pid=${srPID}"
                                   class="confirm shutdown">
                                    <i class="fas fa-power-off"></i>&nbsp;${_('Shutdown')}
                                </a>
                                % if sickrage.app.config.app_sub == current_user.get('sub'):
                                    <a class="dropdown-item" href="${srWebRoot}/unlink" class="confirm logout">
                                        <i class="fas fa-unlink"></i>&nbsp;${_('Unlink Account')}
                                    </a>
                                % endif
                                <a class="dropdown-item" href="${srWebRoot}/logout" class="confirm logout">
                                    <i class="fas fa-sign-out-alt"></i>&nbsp;${_('Logout')}
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item" href="${srWebRoot}/home/status/">
                                    <i class="fas fa-server"></i>&nbsp;${_('Server Status')}
                                </a>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    % endif

<div class="container-fluid mb-3">
    % if submenu:
        <div class="row submenu">
            <div class="col">
                <div class="text-center d-print-none">
                    % for menuItem in submenu:
                        <a href="${srWebRoot}${menuItem['path']}"
                           class="btn ${('', ' confirm ')['confirm' in menuItem]} ${menuItem.get('class', '')}">
                            <i class='${menuItem.get('icon', '')}'></i> ${menuItem['title']}
                        </a>
                    % endfor
                </div>
            </div>
        </div>
    % else:
        <%block name="sub_navbar" />
    % endif
</div>

<div class="loading-spinner text-center m-3">
    <i class="fas fa-10x fa-spinner fa-spin fa-fw"></i>
</div>

<div class="container-fluid main-container d-none" style="opacity: .90">
        <%block name="content" />
</div>

<div class="container-fluid">
    % if current_user:
        <footer class="text-center">
            <div>
                % if overall_stats:
                <%
                    total_size = pretty_filesize(overall_stats['total_size'])
                    ep_downloaded = overall_stats['episodes']['downloaded']
                    ep_snatched = overall_stats['episodes']['snatched']
                    ep_total = overall_stats['episodes']['total']
                    ep_percentage = '' if ep_total == 0 else '(<span class="text-primary">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
                %>
                    <span class="text-primary">${overall_stats['shows']['total']}</span> ${_('Shows')}
                    (<span class="text-primary">${overall_stats['shows']['active']}</span> ${_('Active')})
                    | <span class="text-primary">${ep_downloaded}</span>
                % if ep_snatched:
                    <span class="text-primary">
                        <a href="${srWebRoot}/manage/episodeStatuses?whichStatus=2">+${ep_snatched}</a>
                    </span>
                ${_('Snatched')}
                % endif
                    /&nbsp;<span class="text-primary">${ep_total}</span> ${_('Episodes Downloaded')} ${ep_percentage}
                    /&nbsp;<span class="text-primary">${total_size}</span> ${_('Overall Downloaded')}
                % endif
            </div>

            <div>
                ${_('Daily Search:')} <span
                    class="text-primary">${str(sickrage.app.scheduler.get_job('DAILYSEARCHER').next_run_time).split('.')[0]}</span>
                |
                ${_('Backlog Search:')} <span
                    class="text-primary">${str(sickrage.app.scheduler.get_job('BACKLOG').next_run_time).split('.')[0]}</span>
                |
                ${_('Memory used:')}
                <span class="text-primary">
                    ${memory_usage()}
                </span> |
                ${_('Load time:')}
                <span class="text-primary">
                        ${"{:10.4f}".format(time() - srStartTime)}s
                </span> / Mako:
                <span class="text-primary">
                        ${"{:10.4f}".format(time() - makoStartTime)}s
                </span> |
                ${_('Now:')}
                <span class="text-primary">
                    ${str(datetime.datetime.now(sickrage.app.tz)).split('.')[0]}
                </span>
            </div>
        </footer>
    % endif

    <script src="${srWebRoot}/js/core.min.js"></script>
    <%block name="scripts" />
</div>

<a id="back-to-top" href="#" class="btn btn-primary back-to-top" role="button"
   title="Click to return on the top page" data-toggle="tooltip" data-placement="left">
    <span class="fas fa-chevron-up"></span>
</a>

</body>
</html>
