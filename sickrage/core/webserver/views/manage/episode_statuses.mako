<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.helpers import flatten
    from sickrage.core.common import Overview, Quality, Qualities, EpisodeStatus
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
                                    ${_('None of your episodes have status')} ${whichStatus.display_name}
                                </h2>
                            </div>
                        </div>
                    % endif

                        <form action="${srWebRoot}/manage/episodeStatuses">
                            <label for="whichStatus">${_('Manage episodes with status')}</label>
                            <div class="input-group">
                                <select name="whichStatus" id="whichStatus" class="form-control shadow">
                                    % for curStatus in flatten([EpisodeStatus.SKIPPED, EpisodeStatus.SNATCHED, EpisodeStatus.WANTED, EpisodeStatus.IGNORED, EpisodeStatus.FAILED, EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
                                        %if curStatus not in [EpisodeStatus.ARCHIVED, EpisodeStatus.DOWNLOADED]:
                                            <option value="${curStatus.name}">
                                                ${curStatus.display_name}
                                            </option>
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
                            <input type="hidden" id="oldStatus" name="oldStatus" value="${whichStatus.name}"/>
                            <div class="row">
                                <div class="col-md-12">
                                    <h2>
                                        ${_('Shows containing')} ${whichStatus.display_name} ${_('episodes')}
                                    </h2>
                                </div>
                            </div>
                            <br>
                            <div class="row">
                                <div class="col-md-12">
                                    <%
                                        if whichStatus in flatten([EpisodeStatus.IGNORED, EpisodeStatus.SNATCHED, EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
                                            row_class = "good"
                                        else:
                                            row_class = Overview(whichStatus).css_name
                                    %>

                                    <input type="hidden" id="row_class" value="${row_class}"/>

                                    <label for="newStatus">${_('Set checked shows/episodes to')}</label>
                                    <div class="input-group">
                                        <select name="newStatus" id="newStatus" class="form-control">
                                            <%
                                                statusList = flatten([EpisodeStatus.SKIPPED, EpisodeStatus.WANTED, EpisodeStatus.IGNORED, EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)])

                                                # Do not allow setting to bare downloaded or archived!
                                                statusList.remove(EpisodeStatus.DOWNLOADED)
                                                statusList.remove(EpisodeStatus.ARCHIVED)

                                                if whichStatus in statusList:
                                                    statusList.remove(int(whichStatus))

                                                if whichStatus in flatten([EpisodeStatus.SNATCHED, EpisodeStatus.SNATCHED_PROPER, EpisodeStatus.SNATCHED_BEST, EpisodeStatus.composites(EpisodeStatus.ARCHIVED), EpisodeStatus.composites(EpisodeStatus.DOWNLOADED)]):
                                                    statusList.append(EpisodeStatus.FAILED)
                                            %>

                                            % for curStatus in statusList:
                                                <option value="${curStatus.name}">${curStatus.display_name}</option>
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
                                            % for series_id in sorted_show_ids:
                                                <tr id="${series_id}">
                                                    <td class="table-fit" style="border:none">
                                                        <input type="checkbox" class="allCheck"
                                                               id="allCheck-${series_id}"
                                                               title="${show_names[series_id]}"
                                                               name="toChange" value="${series_id}-all" checked/>
                                                    </td>
                                                    <td class="text-left text-nowrap" style="border:none">
                                                        <a class="text-white"
                                                           href="${srWebRoot}/home/displayShow?show=${series_id}">
                                                            ${show_names[series_id]}
                                                        </a>
                                                        (<span class="text-info">${ep_counts[series_id]}</span>)
                                                    </td>
                                                    <td style="border:none"></td>
                                                    <td class="table-fit" style="border:none">
                                                        <input type="button" class="btn btn-sm get_more_eps"
                                                               id="${series_id}" value="${_('Expand')}"/>
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