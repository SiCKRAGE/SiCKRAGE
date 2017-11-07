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
        _('Daily Search'): 'DAILYSEARCHER',
        _('Backlog'): 'BACKLOGSEARCHER',
        _('Show Update'): 'SHOWUPDATER',
        _('Version Check'): 'VERSIONUPDATER',
        _('Proper Finder'): 'PROPERSEARCHER',
        _('Post Process'): 'AUTOPOSTPROCESSOR',
        _('Subtitles Finder'): 'SUBTITLESEARCHER',
        _('Trakt Checker'): 'TRAKTSEARCHER',
    }
    %>

    <div class="row">
        <div class="col-md-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Scheduler')}</h2>
            <div class="horizontal-scroll">
                <table id="schedulerStatusTable" class="tablesorter" width="100%">
                    <thead>
                    <tr>
                        <th>${_('Scheduled Job')}</th>
                        <th>${_('Enabled')}</th>
                        <th>${_('Active')}</th>
                        <th>${_('Cycle Time')}</th>
                        <th>${_('Next Run')}</th>
                    </tr>
                    </thead>
                    <tbody>
                        % for schedulerName, scheduler in schedulerList.items():
                            <% service = getattr(sickrage.srCore, scheduler) %>
                            <% job = sickrage.app.scheduler.get_job(service.name) %>
                            <% enabled = bool(getattr(job, 'next_run_time', False)) %>
                            <tr>
                                <td>${schedulerName}</td>
                                % if enabled:
                                    <td align="center" style="background-color:green">${_('YES')}</td>
                                % else:
                                    <td align="center" style="background-color:red">${_('NO')}</td>
                                % endif
                                % if scheduler == 'BACKLOGSEARCHER':
                                    <% searchQueue = getattr(sickrage.srCore, 'SEARCHQUEUE') %>
                                    <% BLSinProgress = searchQueue.is_backlog_in_progress() %>
                                    <% del searchQueue %>
                                    % if BLSinProgress:
                                        <td align="center">${_('True')}</td>
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
            <h2 class="header">${_('Show Queue')}</h2>
            <table id="queueStatusTable" class="tablesorter" width="100%">
                <thead>
                <tr>
                    <th>${_('Show ID')}</th>
                    <th>${_('Show Name')}</th>
                    <th>${_('In Progress')}</th>
                    <th>${_('Priority')}</th>
                    <th>${_('Added')}</th>
                    <th>${_('Queue Type')}</th>
                </tr>
                </thead>
                <tbody>
                    % if sickrage.app.show_queue.currentItem is not None:
                        <tr>
                        % try:
                            <% showindexerid = sickrage.app.show_queue.currentItem.show.indexerid %>
                            <td>${showindexerid}</td>
                        % except Exception:
                            <td></td>
                        % endtry
                        % try:
                            <% showname = sickrage.app.show_queue.currentItem.show.name %>
                            <td>${showname}</td>
                        % except Exception:
                            % if sickrage.app.show_queue.currentItem.action_id == ShowQueueActions.ADD:
                                <td>${sickrage.app.show_queue.currentItem.showDir}</td>
                            % else:
                                <td></td>
                            % endif
                        % endtry
                            <td>${sickrage.app.show_queue.currentItem.is_alive()}</td>
                            % if sickrage.app.show_queue.currentItem.priority == 10:
                                <td>${_('LOW')}</td>
                            % elif sickrage.app.show_queue.currentItem.priority == 20:
                                <td>${_('NORMAL')}</td>
                            % elif sickrage.app.show_queue.currentItem.priority == 30:
                                <td>${_('HIGH')}</td>
                            % else:
                                <td>${sickrage.app.show_queue.currentItem.priority}</td>
                            % endif
                            <td>${sickrage.app.show_queue.currentItem.added.strftime(dateTimeFormat)}</td>
                            <td>${ShowQueueActions.names[sickrage.app.show_queue.currentItem.action_id]}</td>
                        </tr>
                    % endif
                    % for __, __, item in sickrage.app.show_queue.queue:
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
                                <td>${_('LOW')}</td>
                            % elif item.priority == 20:
                                <td>${_('NORMAL')}</td>
                            % elif item.priority == 30:
                                <td>${_('HIGH')}</td>
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
            <h2 class="header">${_('Disk Space')}</h2>
            <table id="DFStatusTable" class="tablesorter" width="50%">
                <thead>
                <tr>
                    <th>${_('Type')}</th>
                    <th>${_('Location')}</th>
                    <th>${_('Free space')}</th>
                </tr>
                </thead>
                <tbody>
                    % if sickrage.app.config.TV_DOWNLOAD_DIR:
                        <tr>
                            <td>${_('TV Download Directory')}</td>
                            <td>${sickrage.app.config.TV_DOWNLOAD_DIR}</td>
                            % if tvdirFree is not False:
                                <td align="middle">${tvdirFree}</td>
                            % else:
                                <td align="middle"><i>${_('Missing')}</i></td>
                            % endif
                        </tr>
                    % endif
                <tr>
                    <td rowspan=${len(rootDir)}>${_('Media Root Directories')}</td>
                    % for cur_dir in rootDir:
                        <td>${cur_dir}</td>
                    % if rootDir[cur_dir] is not False:
                        <td align="middle">${rootDir[cur_dir]}</td>
                    % else:
                        <td align="middle"><i>${_('Missing')}</i></td>
                    % endif
                    </tr>
                    % endfor
                </tbody>
            </table>
        </div>
    </div>
</%block>
