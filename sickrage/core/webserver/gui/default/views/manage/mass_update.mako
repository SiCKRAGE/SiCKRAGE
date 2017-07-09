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
                        <button class="btn" id="submitMassEdit">Mass Edit</button>
                        <button class="btn" id="submitMassUpdate">Mass Update</button>
                        <button class="btn" id="submitMassRescan">Mass Rescan</button>
                        <button class="btn" id="submitMassRename">Mass Rename</button>
                        <button class="btn" id="submitMassDelete">Mass Delete</button>
                        <button class="btn" id="submitMassRemove">Mass Remove</button>
                        % if sickrage.srCore.srConfig.USE_SUBTITLES:
                            <input class="btn pull-left" type="button" value="Mass Subtitle" id="submitMassSubtitle"/>
                        % endif
                    </div>

                    <div class="pull-right" id="checkboxControls">
                        <label for="continuing"><span class="Continuing"><input type="checkbox" id="Continuing"
                                                                                checked="checked"/> Continuing</span></label>
                        <label for="ended"><span class="Ended"><input type="checkbox" id="Ended"
                                                                      checked="checked"/> Ended</span></label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <form name="massUpdateForm" method="post" action="massUpdate">

        <table id="massUpdateTable" class="sickrageTable tablesorter" cellspacing="1" border="0" cellpadding="0">
            <thead>
            <tr>
                <th class="col-checkbox">Selected<br/>
                    <input type="checkbox" class="bulkCheck" id="checkAll"/>
                </th>
                <th class="nowrap" style="text-align: left;">Show Name</th>
                <th class="col-quality">Quality</th>
                <th class="col-legend">Sports</th>
                <th class="col-legend">Scene</th>
                <th class="col-legend">Anime</th>
                <th class="col-legend">Season folders</th>
                <th class="col-legend">Archive first match</th>
                <th class="col-legend">Paused</th>
                <th class="col-legend">Subtitle</th>
                <th class="col-legend">Default Ep<br>Status</th>
                <th class="col-legend">Status</th>
            </tr>
            </thead>

            <tbody>
                <% myShowList = sickrage.srCore.SHOWLIST %>
                <% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>

                % for curShow in myShowList:
                    <% curEp = curShow.next_aired %>

                    <tr class="${curShow.status}" id="${curShow.indexerid}">
                        <td align="center">
                            <input type="checkbox" class="showCheck"
                                   id="${curShow.indexerid}"
                                   name="${curShow.indexerid}" ${('disabled', '')[bool(not any([sickrage.srCore.SHOWQUEUE.isBeingRenamed(curShow), sickrage.srCore.SHOWQUEUE.isInRenameQueue(curShow), sickrage.srCore.SHOWQUEUE.isInRefreshQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingUpdated(curShow),sickrage.srCore.SHOWQUEUE.isInUpdateQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingRefreshed(curShow), sickrage.srCore.SHOWQUEUE.isInRefreshQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingRenamed(curShow), sickrage.srCore.SHOWQUEUE.isInRenameQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingSubtitled(curShow), sickrage.srCore.SHOWQUEUE.isInSubtitleQueue(curShow)]))]}/>
                        </td>
                        <td class="tvShow"><a
                                href="${srWebRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a>
                        </td>
                        <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_sports)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_scene)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_anime)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[not bool(curShow.flatten_folders)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.archive_firstmatch)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.paused)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="${srWebRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.subtitles)]}"
                                width="16" height="16"/></td>
                        <td align="center">${statusStrings[curShow.default_ep_status]}</td>
                        <td align="center">${curShow.status}</td>
                    </tr>
                % endfor
            </tbody>
        </table>
    </form>
</%block>
