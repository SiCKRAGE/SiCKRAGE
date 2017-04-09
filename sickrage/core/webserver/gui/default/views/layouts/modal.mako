<%!
    import sickrage
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

    <meta name="msapplication-TileColor" content="#FFFFFF">
    <meta name="msapplication-TileImage" content="/images/ico/favicon-144.png">
    <meta name="msapplication-config" content="/browserconfig.xml">
    <meta data-var="srPID" data-content="${srPID}">
    <meta data-var="srDefaultPage" data-content="${srDefaultPage}">
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
    <%block name="metas" />

    <link rel="shortcut icon" href="/images/ico/favicon.ico">
    <link rel="icon" sizes="16x16 32x32 64x64" href="/images/ico/favicon.ico">
    <link rel="icon" type="image/png" sizes="196x196" href="/images/ico/favicon-196.png">
    <link rel="icon" type="image/png" sizes="160x160" href="/images/ico/favicon-160.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/images/ico/favicon-96.png">
    <link rel="icon" type="image/png" sizes="64x64" href="/images/ico/favicon-64.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/images/ico/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/images/ico/favicon-16.png">
    <link rel="apple-touch-icon" sizes="152x152" href="/images/ico/favicon-152.png">
    <link rel="apple-touch-icon" sizes="144x144" href="/images/ico/favicon-144.png">
    <link rel="apple-touch-icon" sizes="120x120" href="/images/ico/favicon-120.png">
    <link rel="apple-touch-icon" sizes="114x114" href="/images/ico/favicon-114.png">
    <link rel="apple-touch-icon" sizes="76x76" href="/images/ico/favicon-76.png">
    <link rel="apple-touch-icon" sizes="72x72" href="/images/ico/favicon-72.png">
    <link rel="apple-touch-icon" sizes="57x57" href="/images/ico/favicon-57.png">
    <link rel="stylesheet" type="text/css" href="/css/bower.min.css"/>
    % if sickrage.DEVELOPER:
        <link rel="stylesheet" type="text/css" href="/css/core.css"/>
    % else:
        <link rel="stylesheet" type="text/css" href="/css/core.min.css"/>
    % endif
    <link rel="stylesheet" type="text/css" href="/css/themes/${sickrage.srCore.srConfig.THEME_NAME}.css"/>
    <%block name="css" />

    <script src="/js/bower.min.js"></script>
    % if sickrage.DEVELOPER:
        <script src="/js/core.js"></script>
    % else:
        <script src="/js/core.min.js"></script>
    % endif
    <%block name="scripts" />
</head>
<body data-controller="${controller}" data-action="${action}">
<div class="modal-header">
    % if submenu:
        <span class="btn-group">
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
                    ${("&middot; ", "")[bool(inner_first)]}<a class="inner"
                                                              href="${menuItem['path'][cur_link]}">${cur_link}</a>
                    <% inner_first = False %>
                    % endfor
                    % else:
                        <a href="${menuItem['path']}"
                           class="btn${('', (' confirm ' + menuItem.get('class', '')))['confirm' in menuItem]}">${('', '<span class="pull-left ' + icon_class + '"></span> ')[bool(icon_class)]}${menuItem['title']}</a>
                    <% first = False %>
                    % endif
                % endif
            % endfor
            </span>
    % endif
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
</div>
<div class="modal-body">
        <%block name="content" />
</div>
</body>
</html>
