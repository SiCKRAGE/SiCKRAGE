<%!
    import sickrage
%>
<!DOCTYPE html>
<html>
<head>
    <title>SickRage - ${title}</title>

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
    <meta data-var="themeSpinner" data-content="${('', '-dark')[sickrage.srCore.srConfig.THEME_NAME == 'dark']}">
    <meta data-var="anonURL" data-content="${sickrage.srCore.srConfig.ANON_REDIRECT}">
    <meta data-var="srWebRoot" data-content="${srWebRoot}">
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

    <link rel="apple-touch-icon" sizes="57x57" href="${srWebRoot}/images/ico/apple-icon-57x57.png">
    <link rel="apple-touch-icon" sizes="60x60" href="${srWebRoot}/images/ico/apple-icon-60x60.png">
    <link rel="apple-touch-icon" sizes="72x72" href="${srWebRoot}/images/ico/apple-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="76x76" href="${srWebRoot}/images/ico/apple-icon-76x76.png">
    <link rel="apple-touch-icon" sizes="114x114" href="${srWebRoot}/images/ico/apple-icon-114x114.png">
    <link rel="apple-touch-icon" sizes="120x120" href="${srWebRoot}/images/ico/apple-icon-120x120.png">
    <link rel="apple-touch-icon" sizes="144x144" href="${srWebRoot}/images/ico/apple-icon-144x144.png">
    <link rel="apple-touch-icon" sizes="152x152" href="${srWebRoot}/images/ico/apple-icon-152x152.png">
    <link rel="apple-touch-icon" sizes="180x180" href="${srWebRoot}/images/ico/apple-icon-180x180.png">
    <link rel="icon" type="image/png" sizes="192x192"  href="${srWebRoot}/images/ico/android-icon-192x192.png">
    <link rel="icon" type="image/png" sizes="32x32" href="${srWebRoot}/images/ico/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="${srWebRoot}/images/ico/favicon-96x96.png">
    <link rel="icon" type="image/png" sizes="16x16" href="${srWebRoot}/images/ico/favicon-16x16.png">
    <link rel="manifest" href="${srWebRoot}/images/ico/manifest.json">
    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/bower.min.css?${srPID}"/>
    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css?${srPID}"/>
    <link rel="stylesheet" type="text/css" href="${srWebRoot}/css/${srThemeName}.css?${srPID}"/>
    <%block name="css" />

    <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <script type="text/javascript" src="${srWebRoot}/js/bower.min.js"></script>
    <script src="${srWebRoot}/js/core.min.js"></script>
    <%block name="scripts" />

</head>
<body data-controller="${controller}" data-action="${action}">
<nav class="navbar navbar-default navbar-fixed-top">
    <div class="container-fluid">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#nav-collapsed">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="${srWebRoot}/apibuilder/" title="SiCKRAGE">
                <img alt="SiCKRAGE" src="${srWebRoot}/images/logo.png" style="width: 200px; height: 50px;"
                     class="img-responsive pull-left"/>
                <p class="navbar-text hidden-xs">${title}</p>
            </a>
        </div>

        <div class="collapse navbar-collapse" id="nav-collapsed">
            <div class="btn-group navbar-btn" data-toggle="buttons">
                <label class="btn btn-primary">
                    <input autocomplete="off" id="option-profile" type="checkbox"/> Profile
                </label>
                <label class="btn btn-primary">
                    <input autocomplete="off" id="option-jsonp" type="checkbox"/> JSONP
                </label>
            </div>

            <ul class="nav navbar-nav navbar-right">
                <li><a href="${srWebRoot}/home/">Back to SickRage</a></li>
                <li class="hidden-xs">
                    <a href="https://www.gofundme.com/sickrage" rel="noreferrer"
                       onclick="window.open('${sickrage.srCore.srConfig.ANON_REDIRECT}' + this.href); return false;">
                        <img src="${srWebRoot}/images/donate.jpg" alt="[donate]" class="navbaricon"/>
                    </a>
                </li>
            </ul>

            <form class="navbar-form navbar-right">
                <div class="form-group">
                    <input autocomplete="off" class="form-control" id="command-search" placeholder="Command name"
                           type="search"/>
                </div>
            </form>
        </div>
    </div>
</nav>

<div class="container-fluid" id="content">
        <%block name="content" />
</div>

</body>
</html>
