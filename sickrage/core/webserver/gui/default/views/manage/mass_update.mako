<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import statusStrings
    from sickrage.core.helpers.compat import cmp
%>
<%block name="content">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>


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

            <tfoot>
            <tr>
                <td rowspan="1" colspan="${(12, 13)[bool(sickrage.srCore.srConfig.USE_SUBTITLES)]}" class="align-center alt">
                    <input class="btn pull-left" type="button" value="Mass Edit" id="submitMassEdit"/>
                    <input class="btn pull-left" type="button" value="Mass Update" id="submitMassUpdate"/>
                    <input class="btn pull-left" type="button" value="Mass Rescan" id="submitMassRescan"/>
                    <input class="btn pull-left" type="button" value="Mass Rename" id="submitMassRename"/>
                    <input class="btn pull-left" type="button" value="Mass Delete" id="submitMassDelete"/>
                    <input class="btn pull-left" type="button" value="Mass Remove" id="submitMassRemove"/>
                    % if sickrage.srCore.srConfig.USE_SUBTITLES:
                        <input class="btn pull-left" type="button" value="Mass Subtitle" id="submitMassSubtitle"/>
                    % endif
                </td>
            </tr>
            </tfoot>

            <tbody>
                <% myShowList = sickrage.srCore.SHOWLIST %>
                <% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>

                % for curShow in myShowList:
                    <% curEp = curShow.next_aired %>

                    <tr>
                        <td align="center">
                            <input type="checkbox" class="showCheck"
                                   id="${curShow.indexerid}" ${('disabled', '')[bool(not any([sickrage.srCore.SHOWQUEUE.isBeingRenamed(curShow), sickrage.srCore.SHOWQUEUE.isInRenameQueue(curShow), sickrage.srCore.SHOWQUEUE.isInRefreshQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingUpdated(curShow),sickrage.srCore.SHOWQUEUE.isInUpdateQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingRefreshed(curShow), sickrage.srCore.SHOWQUEUE.isInRefreshQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingRenamed(curShow), sickrage.srCore.SHOWQUEUE.isInRenameQueue(curShow), sickrage.srCore.SHOWQUEUE.isBeingSubtitled(curShow), sickrage.srCore.SHOWQUEUE.isInSubtitleQueue(curShow)]))]}/>
                        </td>
                        <td class="tvShow"><a href="/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a>
                        </td>
                        <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_sports)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_scene)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.is_anime)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[not bool(curShow.flatten_folders)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.archive_firstmatch)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.paused)]}"
                                width="16" height="16"/></td>
                        <td align="center"><img
                                src="/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[bool(curShow.subtitles)]}"
                                width="16" height="16"/></td>
                        <td align="center">${statusStrings[curShow.default_ep_status]}</td>
                        <td align="center">${curShow.status}</td>
                    </tr>
                % endfor
            </tbody>
        </table>
    </form>
</%block>
