<%inherit file="../layouts/main.mako"/>
<%!
    import datetime
    import sickrage
    from sickrage.core.queues.show import ShowQueueActions
    from sickrage.core.common import dateTimeFormat
    from sickrage.core.helpers import pretty_time_delta
%>
<%block name="content">
    <%
        schedulerList = {
        'Daily Search': 'DAILYSEARCHER',
        'Backlog': 'BACKLOGSEARCHER',
        'Show Update': 'SHOWUPDATER',
        'Version Check': 'VERSIONUPDATER',
        'Proper Finder': 'PROPERSEARCHER',
        'Post Process': 'AUTOPOSTPROCESSOR',
        'Subtitles Finder': 'SUBTITLESEARCHER',
        'Trakt Checker': 'TRAKTSEARCHER',
    }
    %>
    <div class="row">
        <div class="col-md-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h2 class="header">Scheduler</h2>
            <div class="horizontal-scroll">
                <table id="schedulerStatusTable" class="tablesorter" width="100%">
                    <thead>
                    <tr>
                        <th>Scheduler</th>
                        <th>Enabled</th>
                        <th>Active</th>
                        <th>Cycle Time</th>
                        <th>Next Run</th>
                    </tr>
                    </thead>
                    <tbody>
                        % for schedulerName, scheduler in schedulerList.items():
                            <% service = getattr(sickrage.srCore, scheduler) %>
                            <% job = sickrage.srCore.srScheduler.get_job(service.name) %>
                            <% enabled = bool(getattr(job, 'next_run_time', False)) %>
                            <tr>
                                <td>${schedulerName}</td>
                                % if enabled:
                                    <td align="center" style="background-color:green">YES</td>
                                % else:
                                    <td align="center" style="background-color:red">NO</td>
                                % endif
                                % if scheduler == 'BACKLOGSEARCHER':
                                    <% searchQueue = getattr(sickrage.srCore, 'SEARCHQUEUE') %>
                                    <% BLSinProgress = searchQueue.is_backlog_in_progress() %>
                                    <% del searchQueue %>
                                    % if BLSinProgress:
                                        <td align="center">True</td>
                                    % else:
                                    % try:
                                        <td align="center">${service.amActive}</td>
                                    % except Exception:
                                        <td>N/A</td>
                                    % endtry
                                    % endif
                                % else:
                                % try:
                                    <td align="center">${service.amActive}</td>
                                % except Exception:
                                    <td align="center">N/A</td>
                                % endtry
                                % endif
                                % if job:
                                <% cycleTime = (job.trigger.interval.microseconds + (job.trigger.interval.seconds + job.trigger.interval.days * 24 * 3600) * 10**6) / 10**6 %>
                                    <td align="right"
                                        data-seconds="${cycleTime}">${pretty_time_delta(cycleTime)}</td>
                                % if job.next_run_time:
                                <%
                                    x = job.next_run_time - datetime.datetime.now(job.next_run_time.tzinfo)
                                    timeLeft = (x.microseconds + (x.seconds + x.days * 24 * 3600) * 10**6) / 10**6
                                %>
                                    <td align="right"
                                        data-seconds="${timeLeft}">${pretty_time_delta(timeLeft)}</td>
                                % else:
                                    <td align="center"></td>
                                % endif
                                % endif
                            </tr>
                            <% del job %>
                            <% del service %>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h2 class="header">Show Queue</h2>
            <table id="queueStatusTable" class="tablesorter" width="100%">
                <thead>
                <tr>
                    <th>Show ID</th>
                    <th>Show Name</th>
                    <th>In Progress</th>
                    <th>Priority</th>
                    <th>Added</th>
                    <th>Queue Type</th>
                </tr>
                </thead>
                <tbody>
                    % if sickrage.srCore.SHOWQUEUE.currentItem is not None:
                        <tr>
                        % try:
                            <% showindexerid = sickrage.srCore.SHOWQUEUE.currentItem.show.indexerid %>
                            <td>${showindexerid}</td>
                        % except Exception:
                            <td></td>
                        % endtry
                        % try:
                            <% showname = sickrage.srCore.SHOWQUEUE.currentItem.show.name %>
                            <td>${showname}</td>
                        % except Exception:
                            % if sickrage.srCore.SHOWQUEUE.currentItem.action_id == ShowQueueActions.ADD:
                                <td>${sickrage.srCore.SHOWQUEUE.currentItem.showDir}</td>
                            % else:
                                <td></td>
                            % endif
                        % endtry
                            <td>${sickrage.srCore.SHOWQUEUE.currentItem.is_alive()}</td>
                            % if sickrage.srCore.SHOWQUEUE.currentItem.priority == 10:
                                <td>LOW</td>
                            % elif sickrage.srCore.SHOWQUEUE.currentItem.priority == 20:
                                <td>NORMAL</td>
                            % elif sickrage.srCore.SHOWQUEUE.currentItem.priority == 30:
                                <td>HIGH</td>
                            % else:
                                <td>showQueue.currentItem.priority</td>
                            % endif
                            <td>${sickrage.srCore.SHOWQUEUE.currentItem.added.strftime(dateTimeFormat)}</td>
                            <td>${ShowQueueActions.names[sickrage.srCore.SHOWQUEUE.currentItem.action_id]}</td>
                        </tr>
                    % endif
                    % for _, _, item in sickrage.srCore.SHOWQUEUE.queue:
                        <tr>
                        % try:
                            <% showindexerid = item.show.indexerid %>
                            <td>${showindexerid}</td>
                        % except Exception:
                            <td></td>
                        % endtry
                        % try:
                            <% showname = item.show.name %>
                            <td>${showname}</td>
                        % except Exception:
                            % if item.action_id == ShowQueueActions.ADD:
                                <td>${item.showDir}</td>
                            % else:
                                <td></td>
                            % endif
                        % endtry
                            <td>${item.is_alive()}</td>
                            % if item.priority == 10:
                                <td>LOW</td>
                            % elif item.priority == 20:
                                <td>NORMAL</td>
                            % elif item.priority == 30:
                                <td>HIGH</td>
                            % else:
                                <td>${item.priority}</td>
                            % endif
                            <td>${item.added.strftime(dateTimeFormat)}</td>
                            <td>${ShowQueueActions.names[item.action_id]}</td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h2 class="header">Disk Space</h2>
            <table id="DFStatusTable" class="tablesorter" width="50%">
                <thead>
                <tr>
                    <th>Type</th>
                    <th>Location</th>
                    <th>Free space</th>
                </tr>
                </thead>
                <tbody>
                    % if sickrage.srCore.srConfig.TV_DOWNLOAD_DIR:
                        <tr>
                            <td>TV Download Directory</td>
                            <td>${sickrage.srCore.srConfig.TV_DOWNLOAD_DIR}</td>
                            % if tvdirFree is not False:
                                <td align="middle">${tvdirFree}</td>
                            % else:
                                <td align="middle"><i>Missing</i></td>
                            % endif
                        </tr>
                    % endif
                <tr>
                    <td rowspan=${len(rootDir)}>Media Root Directories</td>
                    % for cur_dir in rootDir:
                        <td>${cur_dir}</td>
                    % if rootDir[cur_dir] is not False:
                        <td align="middle">${rootDir[cur_dir]}</td>
                    % else:
                        <td align="middle"><i>Missing</i></td>
                    % endif
                    </tr>
                    % endfor
                </tbody>
            </table>
        </div>
    </div>

</%block>
