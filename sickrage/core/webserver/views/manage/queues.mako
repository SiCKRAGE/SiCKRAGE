<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                <b>${_('Backlog Search:')}</b>
                ${((_('Not in progress'), _('In Progress'))[backlogRunning], _('Paused'))[backlogPaused]}
            </h3>
            <a class="btn" href="${srWebRoot}/manage/manageQueues/forceBacklog">
                <i class="icon-exclamation-sign"></i>${_('Force')}
            </a>
            <a class="btn"
               href="${srWebRoot}/manage/manageQueues/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}">
                <i class="icon-${('paused', 'play')[bool(backlogPaused)]}"></i>${(_('Pause'), _('Unpause'))[bool(backlogPaused)]}
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                <b>${_('Daily Search:')}</b>
                ${(_('Not in progress'), _('In Progress'))[bool(dailySearchStatus)]}
            </h3>
            <a class="btn" href="${srWebRoot}/manage/manageQueues/forceSearch">
                <i class="icon-exclamation-sign"></i>${_('Force')}
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                <b>${_('Find Propers Search:')}</b>
                % if not sickrage.app.config.download_propers:
                    ${_('Propers search disabled')}
                % elif not findPropersStatus:
                    ${_('Not in progress')}
                % else:
                    ${_("In Progress")}
                % endif
            </h3>
            <a class="btn ${('disabled', '')[bool(sickrage.app.config.download_propers)]}"
               href="${srWebRoot}/manage/manageQueues/forceFindPropers">
                <i class="icon-exclamation-sign"></i>Force
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>
                <b>${_('Post-Processor:')}</b>
                ${((_('Not in progress'), _('In Progress'))[postProcessorRunning], 'Paused')[postProcessorPaused]}
            </h3>
            <a class="btn"
               href="${srWebRoot}/manage/manageQueues/pausePostProcessor?paused=${('1', '0')[bool(postProcessorPaused)]}">
                <i class="icon-${('paused', 'play')[bool(postProcessorPaused)]}"></i>${(_('Pause'), _('Unpause'))[bool(postProcessorPaused)]}
            </a>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>${_('Search Queue:')}</h3>
            <table>
                <tr>
                    <td>${_('Daily:')}</td>
                    <td><i>${searchQueueLength['daily']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Backlog:')}</td>
                    <td><i>${searchQueueLength['backlog']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Manual:')}</td>
                    <td><i>${searchQueueLength['manual']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Failed:')}</td>
                    <td><i>${searchQueueLength['failed']} ${_('pending items')}</i></td>
                </tr>
            </table>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <h3>${_('Post-Processor Queue:')}</h3>
            <table>
                <tr>
                    <td>${_('Auto:')}</td>
                    <td><i>${postProcessorQueueLength['auto']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Manual:')}</td>
                    <td><i>${postProcessorQueueLength['manual']} ${_('pending items')}</i></td>
                </tr>
            </table>
        </div>
    </div>
</%block>
