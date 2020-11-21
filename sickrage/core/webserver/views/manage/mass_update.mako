<%inherit file="../layouts/main.mako"/>
<%!
    from functools import cmp_to_key

    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.enums import SearchFormat
    from sickrage.core.common import EpisodeStatus
    from sickrage.core.helpers.compat import cmp
%>

<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col">
            <button class="btn" id="submitMassEdit">${_('Mass Edit')}</button>
            <button class="btn" id="submitMassUpdate">${_('Mass Update')}</button>
            <button class="btn" id="submitMassRescan">${_('Mass Rescan')}</button>
            <button class="btn" id="submitMassRename">${_('Mass Rename')}</button>
            <button class="btn" id="submitMassDelete">${_('Mass Delete')}</button>
            <button class="btn" id="submitMassRemove">${_('Mass Remove')}</button>
            % if sickrage.app.config.subtitles.enable:
                <button class="btn" id="submitMassSubtitle">${_('Mass Subtitle')}</button>
            % endif
        </div>
        <div class="col text-right">
            <div class="dropdown ml-4" id="checkboxControls">
                <button type="button" class="btn bg-transparent dropdown-toggle" data-toggle="dropdown"
                        style="border: none;">
                    <i class="fas fa-2x fa-columns"></i>
                </button>
                <div class="dropdown-menu dropdown-menu-right">
                    <a class="dropdown-item" href="#">
                        <label>
                            <input type="checkbox" id="Continuing" checked="checked"/>
                            ${_('Continuing')}
                        </label>
                    </a>
                    <a class="dropdown-item" href="#">
                        <label>
                            <input type="checkbox" id="Ended" checked="checked"/>
                            ${_('Ended')}
                        </label>
                    </a>
                </div>
            </div>
        </div>
    </div>
</%block>

<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>

    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table id="massUpdateTable" class="table">
                            <thead class="thead-dark">
                            <tr>
                                <th class="col-checkbox">
                                    <input type="checkbox" class="bulkCheck" id="checkAll"/>
                                </th>
                                <th>${_('Show Name')}</th>
                                <th>${_('Show Directory')}</th>
                                <th class="col-legend">${_('Search Format')}</th>
                                <th class="col-quality">${_('Quality')}</th>
                                <th class="col-legend">${_('Scene')}</th>
                                <th class="col-legend">${_('Anime')}</th>
                                <th class="col-legend">${_('Season folders')}</th>
                                <th class="col-legend">${_('Skip downloaded')}</th>
                                <th class="col-legend">${_('Paused')}</th>
                                <th class="col-legend">${_('Subtitle')}</th>
                                <th class="col-legend">${_('Default Ep Status')}</th>
                                <th class="col-legend">${_('Status')}</th>
                            </tr>
                            </thead>

                            <tbody>
                                % for curShow in shows_list:
                                    <% curEp = curShow.airs_next %>

                                    <tr class="${curShow.status}" id="${curShow.series_id}">
                                        <td class="table-fit">
                                            <input type="checkbox" class="showCheck" id="${curShow.series_id}"
                                                   name="${curShow.series_id}" ${('disabled', '')[bool(not any([
                                            sickrage.app.show_queue.is_being_renamed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_renamed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_refreshed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_updated(curShow.series_id),
                                            sickrage.app.show_queue.is_being_updated(curShow.series_id),
                                            sickrage.app.show_queue.is_being_refreshed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_refreshed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_renamed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_renamed(curShow.series_id),
                                            sickrage.app.show_queue.is_being_subtitled(curShow.series_id),
                                            sickrage.app.show_queue.is_being_subtitled(curShow.series_id)]))]}/>
                                        </td>
                                        <td class="tvShow">
                                            <a href="${srWebRoot}/home/displayShow?show=${curShow.series_id}">${curShow.name}</a>
                                        </td>
                                        <td>
                                            ${curShow.location}
                                        </td>
                                        <td class="table-fit">${curShow.search_format.display_name}</td>
                                        <td class="table-fit">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(curShow.is_anime)]}"></i>
                                            <span class="d-none d-print-inline">${bool(curShow.is_anime)}</span>
                                        </td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(not curShow.flatten_folders)]}"></i>
                                            <span class="d-none d-print-inline">${bool(not curShow.flatten_folders)}</span>
                                        </td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(curShow.scene)]}"></i>
                                            <span class="d-none d-print-inline">${bool(curShow.scene)}</span>
                                        </td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(curShow.skip_downloaded)]}"></i>
                                            <span class="d-none d-print-inline">${bool(curShow.skip_downloaded)}</span>
                                        </td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(curShow.paused)]}"></i>
                                            <span class="d-none d-print-inline">${bool(curShow.paused)}</span>
                                        </td>
                                        <td class="table-fit">
                                            <i class="fa ${("fa-times text-danger", "fa-check text-success")[bool(curShow.subtitles)]}"></i>
                                            <span class="d-none d-print-inline">${bool(curShow.subtitles)}</span>
                                        </td>
                                        <td class="table-fit">
                                            ${curShow.default_ep_status.display_name}
                                        </td>
                                        <td class="table-fit">
                                            ${curShow.status}
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
</%block>
