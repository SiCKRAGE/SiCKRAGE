<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import helpers
    from sickbeard.show_queue import ShowQueueActions
    from common import dateTimeFormat
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/status.js"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config-content">
    <h2 class="header">Scheduler</h2>
    <table id="schedulerStatusTable" class="tablesorter" width="100%">
        <thead>
            <tr>
                <th>Scheduler</th>
                <th>Alive</th>
                <th>Enable</th>
                <th>Active</th>
                <th>Start Time</th>
                <th>Cycle Time</th>
                <th>Next Run</th>
                <th>Last Run</th>
                <th>Silent</th>
            </tr>
        </thead>
        <tbody>
            % for job in sickbeard.SCHEDULER.get_jobs():
           <tr>
               <td>${job.name}</td>
               % if job.func.isAlive():
                   <td style="background-color:green">${job.func.isAlive()}</td>
               % else:
                   <td style="background-color:red">${job.func.isAlive()}</td>
               % endif
               % if job.name == 'BACKLOG':
                   <% BLSpaused = sickbeard.searchQueue.is_backlog_paused() %>
                   % if BLSpaused:
               <td>Paused</td>
                   % else:
                       <td>${job.resume()}</td>
                   % endif
               % else:
                   <td>${job.resume()}</td>
               % endif
               % if job.name == 'BACKLOG':
                   <% BLSinProgress = sickbeard.searchQueue.is_backlog_in_progress() %>
                   % if BLSinProgress:
               <td>True</td>
                   % else:
                       % try:
                       <% amActive = job.func.amActive %>
               <td>${amActive}</td>
                       % except Exception:
               <td>N/A</td>
                       % endtry
                   % endif
               % else:
                   % try:
                   <% amActive = job.func.amActive %>
               <td>${amActive}</td>
                   % except Exception:
               <td>N/A</td>
                   % endtry
               % endif
               % if job.start_time:
                   <td align="right">${job.start_time}</td>
               % else:
               <td align="right"></td>
               % endif
               <td align="right">${helpers.pretty_time_delta(job.next_run_time)}</td>
               % if job.enable:
               <% timeLeft = (job.timeLeft().microseconds + (job.timeLeft().seconds + job.timeLeft().days * 24 * 3600) * 10**6) / 10**6 %>
               <td align="right">${helpers.pretty_time_delta(timeLeft)}</td>
               % else:
               <td></td>
               % endif
               <td>${job.lastRun.strftime(dateTimeFormat)}</td>
           </tr>
           <% del service %>
           % endfor
       </tbody>
    </table>
    <h2 class="header">Show Queue</h2>
    <table id="queueStatusTable" class="tablesorter" width="100%">
        <thead>
            <tr>
                <th>Show id</th>
                <th>Show name</th>
                <th>In Progress</th>
                <th>Priority</th>
                <th>Added</th>
                <th>Queue type</th>
            </tr>
        </thead>
        <tbody>
            % if sickbeard.showQueue.currentItem is not None:
                <tr>
                    % try:
                        <% showindexerid = sickbeard.showQueue.currentItem.show.indexerid %>
                        <td>${showindexerid}</td>
                    % except Exception:
                        <td></td>
                    % endtry
                    % try:
                        <% showname = sickbeard.showQueue.currentItem.show.name %>
                        <td>${showname}</td>
                    % except Exception:
                        % if sickbeard.showQueue.currentItem.action_id == ShowQueueActions.ADD:
                            <td>${sickbeard.showQueue.currentItem.showDir}</td>
                        % else:
                            <td></td>
                        % endif
                    % endtry
                        <td>${sickbeard.showQueue.currentItem.inProgress}</td>
                        % if sickbeard.showQueue.currentItem.priority == 10:
                        <td>LOW</td>
                        % elif sickbeard.showQueue.currentItem.priority == 20:
                        <td>NORMAL</td>
                        % elif sickbeard.showQueue.currentItem.priority == 30:
                        <td>HIGH</td>
                    % else:
                            <td>sickbeard.showQueue.currentItem.priority</td>
                    % endif
                        <td>${sickbeard.showQueue.currentItem.added.strftime(dateTimeFormat)}</td>
                        <td>${ShowQueueActions.names[sickbeard.showQueue.currentItem.action_id]}</td>
                </tr>
            % endif
            % for item in sickbeard.showQueue.queue:
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
                    <td>${item.inProgress}</td>
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
            % if sickbeard.TV_DOWNLOAD_DIR:
            <tr>
                <td>TV Download Directory</td>
                <td>${sickbeard.TV_DOWNLOAD_DIR}</td>
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
</%block>
