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
        schedulers = {
            _('Daily Search'): 'daily_searcher',
            _('Backlog'): 'backlog_searcher',
            _('Show Update'): 'show_updater',
            _('Scene Exceptions'): 'name_cache',
        }

        if sickrage.app.config.version_notify:
            schedulers.update({_('Version Check'): 'version_updater'})
        if sickrage.app.config.download_propers:
            schedulers.update({_('Proper Finder'): 'proper_searcher'})
        if sickrage.app.config.process_automatically:
            schedulers.update({_('Post Process'): 'auto_postprocessor'})
        if sickrage.app.config.use_subtitles:
            schedulers.update({_('Subtitles Finder'): 'subtitle_searcher'})
        if sickrage.app.config.use_trakt:
            schedulers.update({_('Trakt Checker'): 'trakt_searcher'})
    %>

    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${_('Scheduler')}</h3>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table id="schedulerStatusTable" class="table" width="100%">
                            <thead class="thead-dark">
                            <tr>
                                <th>${_('Scheduled Job')}</th>
                                <th>${_('Enabled')}</th>
                                <th>${_('Active')}</th>
                                <th>${_('Cycle Time')}</th>
                                <th>${_('Next Run')}</th>
                                <th>${_('Action')}</th>
                            </tr>
                            </thead>
                            <tbody>
                                % for schedulerName, scheduler in schedulers.items():
                                    <% service = getattr(sickrage.app, scheduler) %>
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
                                            <% searchQueue = getattr(sickrage.app, 'search_queue') %>
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
                                        <td align="center">
                                            <button class="btn forceSchedulerJob"
                                                    data-target="${srWebRoot}/forceSchedulerJob?name=${scheduler}">
                                                <i class="fa fa-exclamation-triangle"></i> ${_('Force')}
                                            </button>
                                        </td>
                                    </tr>
                                % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${_('Show Queue')}</h3>
                </div>
                <div class="card-body">
                    <table id="queueStatusTable" class="table" width="100%">
                        <thead class="thead-dark">
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
                            % for item in sickrage.app.show_queue.queue_items:
                                <tr>
                                % try:
                                    <% showindexer_id = item.indexer_id %>
                                    <td>${showindexer_id}</td>
                                % except Exception:
                                    <td></td>
                                % endtry
                                % try:
                                    <% showname = item.show_name %>
                                    <td>${showname}</td>
                                % except Exception:
                                    % if item.action_id == ShowQueueActions.ADD:
                                        <td>${item.showDir}</td>
                                    % else:
                                        <td></td>
                                    % endif
                                % endtry
                                    <td>${item.is_alive}</td>
                                    % if item.priority == 5:
                                        <td>${_('EXTREME')}</td>
                                    % elif item.priority == 10:
                                        <td>${_('HIGH')}</td>
                                    % elif item.priority == 20:
                                        <td>${_('NORMAL')}</td>
                                    % elif item.priority == 30:
                                        <td>${_('LOW')}</td>
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
        </div>
    </div>

    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${_('Disk Space')}</h3>
                </div>
                <div class="card-body">
                    <table id="DFStatusTable" class="table" width="100%">
                        <thead>
                        <tr>
                            <th>${_('Type')}</th>
                            <th>${_('Location')}</th>
                            <th>${_('Free space')}</th>
                        </tr>
                        </thead>
                        <tbody>
                            % if sickrage.app.config.tv_download_dir:
                                <tr>
                                    <td>${_('TV Download Directory')}</td>
                                    <td>${sickrage.app.config.tv_download_dir}</td>
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
        </div>
    </div>
</%block>
