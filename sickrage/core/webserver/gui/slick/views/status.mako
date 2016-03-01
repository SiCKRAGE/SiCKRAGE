<%inherit file="/layouts/main.mako"/>
<%!
    import sickrage
    from core.queues.show import ShowQueueActions
    from core.common import dateTimeFormat
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
            </tr>
        </thead>
        <tbody>
            % for job in sickrage.srCore.SCHEDULER.get_jobs():
                <tr>
                    <td>${job}</td>
                </tr>
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
                        <td>${sickrage.srCore.SHOWQUEUE.currentItem.inProgress}</td>
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
            % for item in sickrage.srCore.SHOWQUEUE.queue:
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
            % if sickrage.srConfig.TV_DOWNLOAD_DIR:
            <tr>
                <td>TV Download Directory</td>
                <td>${sickrage.srConfig.TV_DOWNLOAD_DIR}</td>
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
