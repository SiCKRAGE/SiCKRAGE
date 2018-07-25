<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.common import DOWNLOADED, SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import statusStrings, Quality, Overview
%>
<%block name="content">
    <div class="row">
        <div class="col-md-10 mx-auto">
            <div class="card mt-1 mb-3">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    % if not whichStatus or (whichStatus and not ep_counts):
                    % if whichStatus:
                        <div class="row">
                            <div class="col-md-12">
                                <h2>
                                    ${_('None of your episodes have status')} ${statusStrings[int(whichStatus)]}
                                </h2>
                            </div>
                        </div>
                    % endif

                        <form action="${srWebRoot}/manage/episodeStatuses">
                            <label for="whichStatus">${_('Manage episodes with status')}</label>
                            <div class="input-group">
                                <select name="whichStatus" id="whichStatus" class="form-control shadow">
                                    % for curStatus in [SKIPPED, SNATCHED, WANTED, IGNORED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                                        %if curStatus not in [ARCHIVED, DOWNLOADED]:
                                            <option value="${curStatus}">${statusStrings[curStatus]}</option>
                                        %endif
                                    % endfor
                                </select>
                                <div class="input-group-append">
                                    <input class="btn" type="submit" value="${_('Manage')}"/>
                                </div>
                            </div>
                        </form>
                    % else:
                        <form action="${srWebRoot}/manage/changeEpisodeStatuses" method="post">
                            <input type="hidden" id="oldStatus" name="oldStatus" value="${whichStatus}"/>

                            <div class="row">
                                <div class="col-md-12">
                                    <h2>
                                        ${_('Shows containing')} ${statusStrings[int(whichStatus)]} ${_('episodes')}
                                    </h2>
                                </div>
                            </div>

                            <br>

                            <div class="row">
                                <div class="col-md-12">
                                    <%
                                        if int(whichStatus) in [IGNORED, SNATCHED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                                            row_class = "good"
                                        else:
                                            row_class = Overview.overviewStrings[int(whichStatus)]
                                    %>

                                    <input type="hidden" id="row_class" value="${row_class}"/>

                                    <label for="newStatus">${_('Set checked shows/episodes to')}</label>
                                    <div class="input-group">
                                        <select name="newStatus" id="newStatus" class="form-control">
                                            <%
                                                statusList = [SKIPPED, WANTED, IGNORED] + Quality.DOWNLOADED + Quality.ARCHIVED
                                                # Do not allow setting to bare downloaded or archived!
                                                statusList.remove(DOWNLOADED)
                                                statusList.remove(ARCHIVED)
                                                if int(whichStatus) in statusList:
                                                    statusList.remove(int(whichStatus))

                                                if int(whichStatus) in [SNATCHED, SNATCHED_PROPER, SNATCHED_BEST] + Quality.ARCHIVED + Quality.DOWNLOADED:
                                                    statusList.append(FAILED)
                                            %>

                                            % for curStatus in statusList:
                                                <option value="${curStatus}">${statusStrings[curStatus]}</option>
                                            % endfor
                                        </select>
                                        <div class="input-group-append">
                                            <input class="btn" type="submit" value="${_('Go')}"/>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <button class="btn selectAllShows">${_('Select All')}</button>
                                    <button class="btn unselectAllShows">${_('Clear All')}</button>
                                </div>
                            </div>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <table class="table manageTable">
                                        % for cur_indexer_id in sorted_show_ids:
                                            <tr id="${cur_indexer_id}">
                                                <th>
                                                    <input type="checkbox" class="allCheck"
                                                           id="allCheck-${cur_indexer_id}"
                                                           title="${show_names[cur_indexer_id]}"
                                                           name="${cur_indexer_id}-all" checked/>
                                                </th>
                                                <th colspan="2" style="width: 100%; text-align: left;">
                                                    <a class="whitelink"
                                                       href="${srWebRoot}/home/displayShow?show=${cur_indexer_id}">
                                                        ${show_names[cur_indexer_id]}
                                                    </a>
                                                    (${ep_counts[cur_indexer_id]})
                                                    <input type="button" class="btn btn-sm get_more_eps"
                                                           id="${cur_indexer_id}" value="${_('Expand')}"/>
                                                </th>
                                            </tr>
                                        % endfor
                                        <tr>
                                            <td style="padding:0;"></td>
                                            <td style="padding:0;"></td>
                                            <td style="padding:0;"></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </form>
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>