<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <h1 class="header">${header}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                Backlog Search:
                ${(('Not in progress', 'In Progress')[backlogRunning], 'Paused')[backlogPaused]}
            </h3>
            <a class="btn" href="${srWebRoot}/manage/manageQueues/forceBacklog">
                <i class="icon-exclamation-sign"></i>Force
            </a>
            <a class="btn"
               href="${srWebRoot}/manage/manageQueues/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}">
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
            <a class="btn" href="${srWebRoot}/manage/manageQueues/forceSearch">
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
               href="${srWebRoot}/manage/manageQueues/forceFindPropers">
                <i class="icon-exclamation-sign"></i>Force
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                Post-Processor:
                ${(('Not in progress', 'In Progress')[postProcessorRunning], 'Paused')[postProcessorPaused]}
            </h3>
            <a class="btn"
               href="${srWebRoot}/manage/manageQueues/pausePostProcessor?paused=${('1', '0')[bool(postProcessorPaused)]}">
                <i class="icon-${('paused', 'play')[bool(postProcessorPaused)]}"></i>${('Pause', 'Unpause')[bool(postProcessorPaused)]}
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>Search Queue:</h3>
            <table>
                <tr>
                    <td>Daily:</td>
                    <td><i>${searchQueueLength['daily']} pending items</i></td>
                </tr>
                <tr>
                    <td>Backlog:</td>
                    <td><i>${searchQueueLength['backlog']} pending items</i></td>
                </tr>
                <tr>
                    <td>Manual:</td>
                    <td><i>${searchQueueLength['manual']} pending items</i></td>
                </tr>
                <tr>
                    <td>Failed:</td>
                    <td><i>${searchQueueLength['failed']} pending items</i></td>
                </tr>
            </table>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>Post-Processor Queue:</h3>
            <table>
                <tr>
                    <td>Auto:</td>
                    <td><i>${postProcessorQueueLength['auto']} pending items</i></td>
                </tr>
                <tr>
                    <td>Manual:</td>
                    <td><i>${postProcessorQueueLength['manual']} pending items</i></td>
                </tr>
            </table>
        </div>
    </div>
</%block>
