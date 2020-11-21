<%!
    import datetime
    import re
    from hashlib import md5
    from time import time

    import sickrage
    from sickrage.core.helpers import pretty_file_size
    from sickrage.core.enums import UITheme
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

    % if sickrage.app.config.gui.theme_name == UITheme.DARK:
        <meta name="theme-color" content="#15528F">
    % elif sickrage.app.config.gui.theme_name == UITheme.LIGHT:
        <meta name="theme-color" content="#333333">
    % endif

    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="${srWebRoot}/images/ico/ms-icon-144x144.png">
    <meta name="msapplication-config" content="${srWebRoot}/images/ico/browserconfig.xml">

    <meta data-var="srPID"
          data-content="${srPID}">
    <meta data-var="srDefaultPage"
          data-content="${srDefaultPage}">
    <meta data-var="srWebRoot"
          data-content="${srWebRoot}">
    <meta data-var="themeSpinner"
          data-content="${('', '-dark')[sickrage.app.config.gui.theme_name == UITheme.DARK]}">
    <meta data-var="anonURL"
          data-content="${sickrage.app.config.general.anon_redirect}">
    <meta data-var="srLocale"
          data-content="${srLocale}">
    <meta data-var="srLocaleDir"
          data-content="${srLocaleDir}">
    <meta data-var="sickrage.ANIME_SPLIT_HOME"
          data-content="${sickrage.app.config.anidb.split_home}">
    <meta data-var="sickrage.COMING_EPS_LAYOUT"
          data-content="${sickrage.app.config.gui.coming_eps_layout.name}">
    <meta data-var="sickrage.COMING_EPS_SORT"
          data-content="${sickrage.app.config.gui.coming_eps_sort.name}">
    <meta data-var="sickrage.DATE_PRESET"
          data-content="${sickrage.app.config.gui.date_preset}">
    <meta data-var="sickrage.FILTER_ROW"
          data-content="${sickrage.app.config.gui.filter_row}">
    <meta data-var="sickrage.FUZZY_DATING"
          data-content="${sickrage.app.config.gui.fuzzy_dating}">
    <meta data-var="sickrage.HISTORY_LAYOUT"
          data-content="${sickrage.app.config.gui.history_layout.name}">
    <meta data-var="sickrage.POSTER_SORT_BY"
          data-content="${sickrage.app.config.gui.poster_sort_by.name}">
    <meta data-var="sickrage.POSTER_SORT_DIR"
          data-content="${sickrage.app.config.gui.poster_sort_dir}">
    <meta data-var="sickrage.ROOT_DIRS"
          data-content="${sickrage.app.config.general.root_dirs}">
    <meta data-var="sickrage.SORT_ARTICLE"
          data-content="${sickrage.app.config.general.sort_article}">
    <meta data-var="sickrage.TIME_PRESET"
          data-content="${sickrage.app.config.gui.time_preset}">
    <meta data-var="sickrage.TRIM_ZERO"
          data-content="${sickrage.app.config.gui.trim_zero}">
    <meta data-var="sickrage.VIEW_CHANGELOG"
          data-content="${sickrage.app.config.general.view_changelog}">
    <meta data-var="sickrage.FANART_BACKGROUND"
          data-content="${sickrage.app.config.gui.fanart_background}">
    <meta data-var="sickrage.FANART_BACKGROUND_OPACITY"
          data-content="${sickrage.app.config.gui.fanart_background_opacity}">
    <%block name="metas" />

    <link rel="icon" type="image/png" sizes="32x32" href="${srWebRoot}/images/favicon.png">

    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css"/>
    <%block name="css" />
</head>
<body data-controller="${controller}" data-action="${action}">
    ${mainModals()}
    <%block name="modals" />

    % if current_user:
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
                <a class="navbar-brand d-none d-xl-block" href="${srWebRoot}/home/">
                    <img alt="SiCKRAGE" src="${srWebRoot}/images/logo.png" style="width: 400px;height: 50px;"/>
                </a>
                <a class="navbar-brand d-xl-none" href="${srWebRoot}/home/">
                    <img alt="SiCKRAGE" src="${srWebRoot}/images/logo-badge.png" style="width: 50px;height: 50px;"/>
                </a>
                <button class="navbar-toggler" type="button" data-toggle="collapse"
                        data-target="#navbarSupportedContent"
                        aria-controls="navbarSupportedContent" aria-expanded="false"
                        aria-label="{{ __('Toggle navigation') }}">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse text-center" id="navbarSupportedContent">
                    <!-- Left Side Of Navbar -->
                    <ul class="navbar-nav mr-auto">
                        <li>
                            <div class="quicksearch-container">
                                <div class="quicksearch-input-container">
                                    <i class="fas fa-search m-2"></i>
                                    <input id="quicksearch" class="quicksearch-input" type="search">
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
                                    <i class="fas fa-fw fa-home"></i>&nbsp;${_('Show List')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/addShows/">
                                    <i class="fas fa-fw fa-tv"></i>&nbsp;${_('Add Shows')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/postprocess/">
                                    <i class="fas fa-fw fa-folder-open"></i>&nbsp;${_('Manual Post-Processing')}
                                </a>
                                % if sickrage.app.shows_recent:
                                    <div class="dropdown-divider"></div>
                                % for recentShow in sickrage.app.shows_recent:
                                    <a class="dropdown-item"
                                       href="${srWebRoot}/home/displayShow/?show=${recentShow['series_id']}">
                                        <i class="fas fa-fw fa-tv"></i>&nbsp;${recentShow['name']|trim,h}
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
                                    <i class="fas fa-fw fa-diagnoses"></i>&nbsp;${_('Mass Update')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/backlogOverview/">
                                    <i class="fas fa-fw fa-backward"></i>&nbsp;${_('Backlog Overview')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/manageQueues/">
                                    <i class="fas fa-fw fa-list"></i>&nbsp;${_('Manage Queues')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/manage/episodeStatuses/">
                                    <i class="fas fa-fw fa-th-list"></i>&nbsp;${_('Episode Status Management')}
                                </a>
                                % if sickrage.app.config.trakt.enable and sickrage.app.config.trakt.oauth_token != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/syncTrakt/">
                                        <i class="fas fa-fw fa-sync"></i>&nbsp;${_('Sync Trakt')}
                                    </a>
                                % endif
                                % if sickrage.app.config.plex.enable and sickrage.app.config.plex.server_host != "":
                                    <a class="dropdown-item" href="${srWebRoot}/home/updatePLEX/">
                                        <i class="fas fa-fw fa-sync"></i>&nbsp;${_('Update PLEX')}
                                    </a>
                                % endif
                                % if torrent_webui_url:
                                <a class="dropdown-item" href="${torrent_webui_url}" target="_blank">
                                    <i class="fas fa-fw fa-video"></i>&nbsp;${_('Manage Torrents')}
                                </a>
                            % endif
                                <a class="dropdown-item" href="${srWebRoot}/manage/failedDownloads/">
                                    <i class="fas fa-fw fa-first-aid"></i>&nbsp;${_('Failed Downloads')}
                                </a>
                                % if sickrage.app.config.subtitles.enable:
                                    <a class="dropdown-item" href="${srWebRoot}/manage/subtitleMissed/">
                                        <i class="fas fa-fw fa-question"></i>&nbsp;${_('Missed Subtitle Management')}
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
                                    <i class="fas fa-fw fa-2x fa-cogs"></i>
                                </span>
                            </a>

                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarConfig">
                                <a class="dropdown-item" href="${srWebRoot}/config/">
                                    <i class="fas fa-fw fa-info"></i>&nbsp;${_('Help and Info')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/general/">
                                    <i class="fas fa-fw fa-wrench"></i>&nbsp;${_('General')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/backuprestore/">
                                    <i class="fas fa-fw fa-upload"></i>&nbsp;${_('Backup and Restore')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/search/">
                                    <i class="fas fa-fw fa-binoculars"></i>&nbsp;${_('Search Clients')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/providers/">
                                    <i class="fas fa-fw fa-share-alt"></i>&nbsp;${_('Search Providers')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/subtitles/">
                                    <i class="fas fa-fw fa-closed-captioning"></i>&nbsp;${_('Subtitles Settings')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/qualitySettings/">
                                    <i class="fas fa-fw fa-wrench"></i>&nbsp;${_('Quality Settings')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/postProcessing/">
                                    <i class="fas fa-fw fa-folder-open"></i>&nbsp;${_('Post Processing')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/notifications/">
                                    <i class="fas fa-fw fa-bell"></i>&nbsp;${_('Notifications')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/config/anime/">
                                    <i class="fas fa-fw fa-eye"></i>&nbsp;${_('Anime')}
                                </a>
                            </div>
                        </li>

                        <li class="nav-item dropdown${('', ' active')[topmenu == 'system']}">
                            <a id="navbarSystem" class="nav-link" href="#" role="button"
                               aria-haspopup="true" data-toggle="dropdown" aria-expanded="false">
                                <span class="d-none d-sm-block dropdown-toggle d-md-none">
                                    ${_('Tools')}
                                </span>
                                <span id="profile-container" class="d-sm-none d-md-block">
                                    % if isinstance(current_user, dict):
                                        <img class="rounded-circle shadow"
                                             src="https://gravatar.com/avatar/${md5(current_user['email'].encode('utf-8')).hexdigest()}?d=mm&s=40"/>
                                    % else:
                                        <i class="fa fa-2x fa-user-circle"></i>
                                    % endif
                                    <span id="profile-badge" class="badge badge-info"
                                          style="float:right;margin-bottom:-10px;"></span>
                                </span>
                            </a>

                            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarSystem">
                                <a class="dropdown-item" href="${srWebRoot}/IRC/">
                                    <i class="fas fa-fw fa-hashtag"></i>&nbsp;${_('IRC')}
                                </a>
                                <a class="dropdown-item" href="#" id="changelog">
                                    <i class="fas fa-fw fa-globe"></i>&nbsp;${_('Changelog')}
                                </a>
                                <a class="dropdown-item" href="https://opencollective.com/sickrage" rel="noreferrer"
                                   onclick="window.open('${sickrage.app.config.general.anon_redirect}' + this.href); return false;">
                                    <i class="fas fa-fw fa-donate"></i>&nbsp;${_('Donate')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/announcements/">
                                    <i class="fas fa-fw fa-circle"></i>&nbsp;${_('Announcements')}
                                    <span id="numAnnouncements" class="badge badge-info"></span>
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item d-none"
                                   href="${srWebRoot}/logs/">
                                    <i class="fas fa-fw fa-exclamation-circle"></i>&nbsp;${_('View Errors')}
                                    <span id="numErrors" class="badge badge-danger"></span>
                                </a>
                                <a class="dropdown-item d-none"
                                   href="${srWebRoot}/logs/?level=${sickrage.app.log.WARNING}">
                                    <i class="fas fa-fw fa-exclamation-triangle"></i>&nbsp;${_('View Warnings')}
                                    <span id="numWarnings" class="badge badge-warning"></span>
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/logs/view/">
                                    <i class="fas fa-fw fa-file-archive"></i>&nbsp;${_('View Log')}
                                </a>
                                <div class="dropdown-divider"></div>
                                %if not sickrage.app.disable_updates:
                                    <a class="dropdown-item" href="${srWebRoot}/home/updateCheck?pid=${srPID}">
                                        <i class="fas fa-fw fa-check-square"></i>&nbsp;${_('Check For Updates')}
                                    </a>
                                %endif
                                <a class="dropdown-item" href="${srWebRoot}/home/restart/?pid=${srPID}"
                                   class="confirm restart">
                                    <i class="fas fa-fw fa-redo"></i>&nbsp;${_('Restart')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/home/shutdown/?pid=${srPID}"
                                   class="confirm shutdown">
                                    <i class="fas fa-fw fa-power-off"></i>&nbsp;${_('Shutdown')}
                                </a>
                                <a class="dropdown-item" href="${srWebRoot}/logout" class="confirm logout">
                                    <i class="fas fa-fw fa-sign-out-alt"></i>&nbsp;${_('Logout')}
                                </a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item" href="${srWebRoot}/home/serverStatus/">
                                    <i class="fas fa-fw fa-server"></i>&nbsp;${_('Server Status')}
                                </a>
                                % if sickrage.app.config.general.sso_auth_enabled:
                                    <a class="dropdown-item" href="${srWebRoot}/home/providerStatus/">
                                        <i class="fas fa-fw fa-server"></i>&nbsp;${_('Provider Status')}
                                    </a>
                                % endif
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
                        % if 'requires' in menuItem and not menuItem.get('requires'):
                            <% continue %>
                        % else:
                            <a href="${srWebRoot}${menuItem['path']}"
                               class="btn ${('', ' confirm ')['confirm' in menuItem]} ${menuItem.get('class', '')}">
                                <i class='${menuItem.get('icon', '')}'></i> ${menuItem['title']}
                            </a>
                        % endif
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
    ##     % if current_user:
    ##         <footer class="text-center">
    ##             <div>
    ##                 % if overall_stats:
    ##                 <%
    ##                     total_size = pretty_file_size(overall_stats['total_size'])
    ##                     ep_downloaded = overall_stats['episodes']['downloaded']
    ##                     ep_snatched = overall_stats['episodes']['snatched']
    ##                     ep_total = overall_stats['episodes']['total']
    ##                     ep_percentage = '' if ep_total == 0 else '(<span class="text-primary">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
    ##                 %>
    ##                     <span class="text-primary">${overall_stats['shows']['total']}</span> ${_('Shows')}
    ##                     (<span class="text-primary">${overall_stats['shows']['active']}</span> ${_('Active')})
    ##                     | <span class="text-primary">${ep_downloaded}</span>
    ##                 % if ep_snatched:
    ##                     <span class="text-primary">
    ##                         <a href="${srWebRoot}/manage/episodeStatuses?whichStatus=2">+${ep_snatched}</a>
    ##                     </span>
    ##                 ${_('Snatched')}
    ##                 % endif
    ##                     /&nbsp;<span class="text-primary">${ep_total}</span> ${_('Episodes Downloaded')} ${ep_percentage}
    ##                     /&nbsp;<span class="text-primary">${total_size}</span> ${_('Overall Downloaded')}
    ##                 % endif
    ##             </div>
    ##
    ##             <div>
    ##                 ${_('Daily Search:')} <span
    ##                     class="text-primary">${str(sickrage.app.scheduler.get_job('DAILYSEARCHER').next_run_time).split('.')[0]}</span>
    ##                 |
    ##                 ${_('Backlog Search:')} <span
    ##                     class="text-primary">${str(sickrage.app.scheduler.get_job('BACKLOG').next_run_time).split('.')[0]}</span>
    ##                 |
    ##                 ${_('Load time:')}
    ##                 <span class="text-primary">
    ##                         ${"{:10.4f}".format(time() - srStartTime)}s
    ##                 </span> / Mako:
    ##                 <span class="text-primary">
    ##                         ${"{:10.4f}".format(time() - makoStartTime)}s
    ##                 </span> |
    ##                 ${_('Now:')}
    ##                 <span class="text-primary">
    ##                     ${str(datetime.datetime.now(sickrage.app.tz)).split('.')[0]}
    ##                 </span>
    ##             </div>
    ##         </footer>
    ##     % endif

    <script src="${srWebRoot}/js/core.min.js"></script>
    <%block name="scripts" />
</div>

<a id="back-to-top" href="#" class="btn btn-primary back-to-top" role="button"
   title="Click to return on the top page" data-toggle="tooltip" data-placement="left">
    <span class="fas fa-chevron-up"></span>
</a>

</body>
</html>
