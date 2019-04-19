<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.common import DOWNLOADED, SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import statusStrings, Quality, Overview
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
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
                        <div class="row">
                            <div class="col-md-12">
                                <button class="btn selectAllShows">${_('Select All')}</button>
                                <button class="btn unselectAllShows">${_('Clear All')}</button>
                            </div>
                        </div>
                        <br/>
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
                                    <div class="table-responsive">
                                        <table class="table">
                                            % for cur_indexer_id in sorted_show_ids:
                                                <tr id="${cur_indexer_id}">
                                                    <td class="table-fit" style="border:none">
                                                        <input type="checkbox" class="allCheck"
                                                               id="allCheck-${cur_indexer_id}"
                                                               title="${show_names[cur_indexer_id]}"
                                                               name="toChange" value="${cur_indexer_id}-all" checked/>
                                                    </td>
                                                    <td class="text-left text-nowrap" style="border:none">
                                                        <a class="text-white"
                                                           href="${srWebRoot}/home/displayShow?show=${cur_indexer_id}">
                                                            ${show_names[cur_indexer_id]}
                                                        </a>
                                                        (<span class="text-info">${ep_counts[cur_indexer_id]}</span>)
                                                    </td>
                                                    <td style="border:none"></td>
                                                    <td class="table-fit" style="border:none">
                                                        <input type="button" class="btn btn-sm get_more_eps"
                                                               id="${cur_indexer_id}" value="${_('Expand')}"/>
                                                    </td>
                                                </tr>
                                            % endfor
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </form>
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>