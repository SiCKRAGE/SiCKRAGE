<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import statusStrings
    from sickrage.core.helpers.compat import cmp
%>
<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>

    <div class="row">
        <!-- Labels -->
        <div class="col-xs-12">
            <div class="row">
                <div class="col-xs-12">
                    <div class="btn-group pull-left">
                        <button class="btn" id="submitMassEdit">${_('Mass Edit')}</button>
                        <button class="btn" id="submitMassUpdate">${_('Mass Update')}</button>
                        <button class="btn" id="submitMassRescan">${_('Mass Rescan')}</button>
                        <button class="btn" id="submitMassRename">${_('Mass Rename')}</button>
                        <button class="btn" id="submitMassDelete">${_('Mass Delete')}</button>
                        <button class="btn" id="submitMassRemove">${_('Mass Remove')}</button>
                        % if sickrage.app.config.use_subtitles:
                            <input class="btn pull-left" type="button" value="${_('Mass Subtitle')}"
                                   id="submitMassSubtitle"/>
                        % endif
                    </div>

                    <div class="pull-right" id="checkboxControls">
                        <label for="viewstatuses" class="badge"
                               style="background-color: #333333;">${_('View Statuses:')}
                            <input type="checkbox" id="Continuing" checked="checked"/> ${_('Continuing')}
                            <input type="checkbox" id="Ended" checked="checked"/> ${_('Ended')}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <form name="massUpdateForm" method="post" action="massUpdate">

        <table id="massUpdateTable" class="sickrageTable tablesorter" cellspacing="1" border="0" cellpadding="0">
            <thead>
            <tr>
                <th class="col-checkbox">${_('Selected')}<br/>
                    <input type="checkbox" class="bulkCheck" id="checkAll"/>
                </th>
                <th class="nowrap" style="text-align: left;">${_('Show Name')}</th>
                <th class="col-quality">${_('Quality')}</th>
                <th class="col-legend">${_('Sports')}</th>
                <th class="col-legend">${_('Scene')}</th>
                <th class="col-legend">${_('Anime')}</th>
                <th class="col-legend">${_('Season folders')}</th>
                <th class="col-legend">${_('Skip downloaded')}</th>
                <th class="col-legend">${_('Paused')}</th>
                <th class="col-legend">${_('Subtitle')}</th>
                <th class="col-legend">${_('Default Ep')}<br>${_('Status')}</th>
                <th class="col-legend">${_('Status')}</th>
            </tr>
            </thead>

            <tbody>
                % for curShow in sorted(sickrage.app.showlist, lambda x, y: cmp(x.name, y.name)):
                    <% curEp = curShow.next_aired %>

                    <tr class="${curShow.status}" id="${curShow.indexerid}">
                        <td align="center">
                            <input type="checkbox" class="showCheck"
                                   id="${curShow.indexerid}"
                                   name="${curShow.indexerid}" ${('disabled', '')[bool(not any([sickrage.app.show_queue.isBeingRenamed(curShow), sickrage.app.show_queue.isInRenameQueue(curShow), sickrage.app.show_queue.isInRefreshQueue(curShow), sickrage.app.show_queue.isBeingUpdated(curShow),sickrage.app.show_queue.isInUpdateQueue(curShow), sickrage.app.show_queue.isBeingRefreshed(curShow), sickrage.app.show_queue.isInRefreshQueue(curShow), sickrage.app.show_queue.isBeingRenamed(curShow), sickrage.app.show_queue.isInRenameQueue(curShow), sickrage.app.show_queue.isBeingSubtitled(curShow), sickrage.app.show_queue.isInSubtitleQueue(curShow)]))]}/>
                        </td>
                        <td class="tvShow"><a
                                href="${srWebRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a>
                        </td>
                        <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.is_sports)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.is_scene)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.is_anime)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[not bool(curShow.flatten_folders)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.skip_downloaded)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.paused)]}"></i>
                        </td>
                        <td align="center">
                            <i class="fa ${("fa-times red-text", "fa-check green-text")[bool(curShow.subtitles)]}"></i>
                        </td>
                        <td align="center">${statusStrings[curShow.default_ep_status]}</td>
                        <td align="center">${curShow.status}</td>
                    </tr>
                % endfor
            </tbody>
        </table>
    </form>
</%block>
