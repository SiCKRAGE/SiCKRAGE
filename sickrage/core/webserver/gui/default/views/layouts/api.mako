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
    <meta name="viewport" content="width=device-width">

    % if srThemeName == "dark":
        <meta name="theme-color" content="#15528F">
    % elif srThemeName == "light":
        <meta name="theme-color" content="#333333">
    % endif

    <meta name="msapplication-TileColor" content="#FFFFFF">
    <meta name="msapplication-TileImage" content="/images/ico/favicon-144.png">
    <meta name="msapplication-config" content="/browserconfig.xml">

    <meta data-var="srPID" data-content="${srPID}">
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
    <link rel="apple-touch-icon" href="/images/ico/favicon-57.png">
    <link rel="stylesheet" type="text/css" href="/css/bower.min.css?${srPID}"/>
    <link rel="stylesheet" type="text/css" href="/css/core.min.css?${srPID}"/>
    <link rel="stylesheet" type="text/css" href="/css/${srThemeName}.css?${srPID}"/>
    <%block name="css" />

    <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <script type="text/javascript" src="/js/bower.min.js"></script>
    % if sickrage.DEVELOPER:
        <script src="/js/core.js"></script>
    % else:
        <script src="/js/core.min.js"></script>
    % endif
    <%block name="scripts" />

</head>
<body data-controller="${controller}" data-action="${action}">
<nav class="navbar navbar-default navbar-fixed-top hidden-print" role="navigation">
    <div class="container-fluid">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#nav-collapsed">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="/apibuilder/" title="SiCKRAGE">
                <img alt="SiCKRAGE" src="/images/logo.png" style="width: 200px; height: 50px;" class="img-responsive pull-left"/>
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
                <li><a href="/home/">Back to SickRage</a></li>
                <li class="hidden-xs">
                    <a href="https://www.gofundme.com/sickrage" rel="noreferrer"
                       onclick="window.open('${sickrage.srCore.srConfig.ANON_REDIRECT}' + this.href); return false;">
                        <img src="/images/donate.jpg" alt="[donate]" class="navbaricon"/>
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
<div id="contentWrapper">
    <div id="content">
            <%block name="content" />
    </div>
</div>
</body>
</html>
