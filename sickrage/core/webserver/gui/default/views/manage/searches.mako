<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div id="summary2" class="align-left">
        <div class="row">
            <div class="col-md-12">
                <h3>
                    Backlog Search:
                    ${(('Not in progress', 'In Progress')[backlogRunning], 'Paused')[backlogPaused]}
                </h3>
                <a class="btn" href="${srWebRoot}/manage/manageSearches/forceBacklog">
                    <i class="icon-exclamation-sign"></i>Force
                </a>
                <a class="btn"
                   href="${srWebRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}">
                    <i class="icon-${('paused', 'play')[bool(backlogPaused)]}"></i>${('Pause', 'Unpause')[bool(backlogPaused)]}
                </a>
            </div>
        </div>


        <div class="row">
            <div class="col-md-12">
                <h3>
                    Daily Search:
                    ${('Not in progress', 'In Progress')[bool(dailySearchStatus)]}
                </h3>
                <a class="btn" href="${srWebRoot}/manage/manageSearches/forceSearch">
                    <i class="icon-exclamation-sign"></i>Force
                </a>
            </div>
        </div>


        <div class="row">
            <div class="col-md-12">
                <h3>
                    Find Propers Search:
                    % if not sickrage.srCore.srConfig.DOWNLOAD_PROPERS:
                        Propers search disabled
                    % elif not findPropersStatus:
                        Not in progress
                    % else:
                        In Progress
                    % endif
                </h3>
                <a class="btn ${('disabled', '')[bool(sickrage.srCore.srConfig.DOWNLOAD_PROPERS)]}"
                   href="${srWebRoot}/manage/manageSearches/forceFindPropers">
                    <i class="icon-exclamation-sign"></i>Force
                </a>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <h3>Search Queue:</h3>
                <table>
                    <tr>
                        <td>Daily:</td>
                        <td><i>${queueLength['daily']} pending items</i></td>
                    </tr>
                    <tr>
                        <td>Backlog:</td>
                        <td><i>${queueLength['backlog']} pending items</i></td>
                    </tr>
                    <tr>
                        <td>Manual:</td>
                        <td><i>${queueLength['manual']} pending items</i></td>
                    </tr>
                    <tr>
                        <td>Failed:</td>
                        <td><i>${queueLength['failed']} pending items</i></td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</%block>
