<%inherit file="../layouts/main.mako"/>
<%!
    import datetime

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
%>
<%block name="content">
    <div id="content800">
        <div id="summary2" class="align-left">
            <h4>Backlog Search:
                % if not backlogRunning:
                    <span style="color: red; ">Not in progress</span><br/>
                % else:
                ${('', 'Paused:')[bool(backlogPaused)]}<span style="color: green; ">Currently running</span><br/>
                % endif
            </h4>
            <a class="btn" href="/manage/manageSearches/forceBacklog"><i class="icon-exclamation-sign"></i> Force</a>
            <a class="btn" href="/manage/manageSearches/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}"><i
                    class="icon-${('paused', 'play')[bool(backlogPaused)]}"></i> ${('Pause', 'Unpause')[bool(backlogPaused)]}
            </a>
            <br/>
            <br/>

            <h4>
                Daily
                Search: ${('<span style="color: red; ">Not in progress</span>', '<span style="color: green; ">In Progress</span>')[dailySearchStatus]}
                <br/>
            </h4>
            <a class="btn" href="/manage/manageSearches/forceSearch"><i class="icon-exclamation-sign"></i> Force</a>
            <br/>
            <br/>

            <h4>Find Propers Search:
                % if not sickrage.srCore.srConfig.DOWNLOAD_PROPERS:
                    <span style="color: red; ">Propers search disabled</span><br>
                % elif not findPropersStatus:
                    <span style="color: red; ">Not in progress</span><br>
                % else:
                    <span style="color: green; ">In Progress</span><br>
                % endif
            </h4>
            <a class="btn ${('disabled', '')[bool(sickrage.srCore.srConfig.DOWNLOAD_PROPERS)]}"
               href="/manage/manageSearches/forceFindPropers"><i class="icon-exclamation-sign"></i> Force
            </a>
            <br/>
            <br/>

            <h4>Search Queue:</h4>
            Backlog: <i>${queueLength['backlog']} pending items</i><br/>
            Daily: <i>${queueLength['daily']} pending items</i><br/>
            Manual: <i>${queueLength['manual']} pending items</i><br/>
            Failed: <i>${queueLength['failed']} pending items</i><br/>
        </div>
    </div>
</%block>
