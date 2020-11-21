<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <div class="card-columns">
                        <div class="card bg-transparent mb-3">
                            <div class="card-header">
                                <h3>
                                    <b>${_('Backlog Search:')}</b><br/>
                                    ${((_('Not in progress'), _('In Progress'))[backlogSearchStatus], _('Paused'))[backlogSearchPaused]}
                                </h3>
                            </div>
                            <div class="card-body">
                                <a class="btn" href="${srWebRoot}/manage/manageQueues/forceBacklogSearch">
                                    <i class="fa fa-exclamation-triangle"></i> ${_('Force')}
                                </a>
                                % if postProcessorRunning:
                                    <a class="btn"
                                       href="${srWebRoot}/manage/manageQueues/pauseBacklogSearcher?paused=${('1', '0')[bool(backlogSearchPaused)]}">
                                        <i class="fa fa-${('pause', 'play')[bool(backlogSearchPaused)]}"></i> ${(_('Pause'), _('Unpause'))[bool(backlogSearchPaused)]}
                                    </a>
                                % endif
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-header">
                                <h3>
                                    <b>${_('Daily Search:')}</b><br/>
                                    ${((_('Not in progress'), _('In Progress'))[dailySearchStatus], _('Paused'))[dailySearchPaused]}
                                </h3>
                            </div>
                            <div class="card-body">
                                <a class="btn" href="${srWebRoot}/manage/manageQueues/forceDailySearch">
                                    <i class="fa fa-exclamation-triangle"></i> ${_('Force')}
                                </a>
                                % if postProcessorRunning:
                                    <a class="btn"
                                       href="${srWebRoot}/manage/manageQueues/pauseDailySearcher?paused=${('1', '0')[bool(dailySearchPaused)]}">
                                        <i class="fa fa-${('pause', 'play')[bool(dailySearchPaused)]}"></i> ${(_('Pause'), _('Unpause'))[bool(dailySearchPaused)]}
                                    </a>
                                % endif
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-header">
                                <h3>
                                    <b>${_('Find Propers Search:')}</b><br/>
                                    % if not sickrage.app.config.general.download_propers:
                                        ${_('Propers search disabled')}
                                    % elif not findPropersStatus:
                                        ${_('Not in progress')}
                                    % else:
                                        ${_("In Progress")}
                                    % endif
                                </h3>
                            </div>
                            <div class="card-body">
                                <a class="btn ${('disabled', '')[bool(sickrage.app.config.general.download_propers)]}"
                                   href="${srWebRoot}/manage/manageQueues/forceFindPropers">
                                    <i class="fa fa-exclamation-triangle"></i> Force
                                </a>
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-header">
                                <h3>
                                    <b>${_('Post-Processor:')}</b><br/>
                                    ${((_('Not in progress'), _('In Progress'))[postProcessorRunning], 'Paused')[postProcessorPaused]}
                                </h3>
                            </div>
                            <div class="card-body">
                                % if postProcessorRunning:
                                    <a class="btn"
                                       href="${srWebRoot}/manage/manageQueues/pausePostProcessor?paused=${('1', '0')[bool(postProcessorPaused)]}">
                                        <i class="fa fa-${('pause', 'play')[bool(postProcessorPaused)]}"></i> ${(_('Pause'), _('Unpause'))[bool(postProcessorPaused)]}
                                    </a>
                                % endif
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-header text-center">
                                <h3>${_('Search Queue')}</h3>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Daily:')}</div>
                                        <div class="col"><i>${searchQueueLength['daily']} ${_('pending items')}</i>
                                        </div>
                                    </div>
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Backlog:')}</div>
                                        <div class="col"><i>${searchQueueLength['backlog']} ${_('pending items')}</i>
                                        </div>
                                    </div>
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Manual:')}</div>
                                        <div class="col"><i>${searchQueueLength['manual']} ${_('pending items')}</i>
                                        </div>
                                    </div>
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Failed:')}</div>
                                        <div class="col"><i>${searchQueueLength['failed']} ${_('pending items')}</i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-header text-center">
                                <h3>${_('Post-Processor Queue')}</h3>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Auto:')}</div>
                                        <div class="col">
                                            <i>${postProcessorQueueLength['auto']} ${_('pending items')}</i></div>
                                    </div>
                                    <div class="col text-center">
                                        <div class="col badge badge-warning">${_('Manual:')}</div>
                                        <div class="col">
                                            <i>${postProcessorQueueLength['manual']} ${_('pending items')}</i></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
