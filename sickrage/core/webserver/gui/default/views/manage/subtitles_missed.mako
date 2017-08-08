<%inherit file="../layouts/main.mako"/>
<%!
    import datetime

    import sickrage
    import sickrage.subtitles
%>
<%block name="content">
    % if whichSubs:
        <% subsLanguage = sickrage.subtitles.name_from_code(whichSubs) if not whichSubs == 'all' else 'All' %>
    % endif
    % if not whichSubs or (whichSubs and not ep_counts):
        % if whichSubs:
            <h2>All of your episodes have ${subsLanguage} subtitles.</h2>
            <br>
        % endif

        <form action="${srWebRoot}/manage/subtitleMissed" method="get">
            Manage episodes without <select name="whichSubs" class="form-control form-control-inline input-sm">
            % if not sickrage.subtitles.wanted_languages():
                <option value="all">All</option>
            % else:
                % for index, sub_code in enumerate(sickrage.subtitles.wanted_languages()):
                    % if index == 0:
                        <option value="und">${sickrage.subtitles.name_from_code(sub_code)}</option>
                    % endif
                % endfor
            % endif
        </select>
            subtitles
            <input class="btn" type="submit" value="Manage"/>
        </form>

    % else:
        <input type="hidden" id="selectSubLang" name="selectSubLang" value="${whichSubs}"/>

        <form action="${srWebRoot}/manage/downloadSubtitleMissed" method="post">
            <h2>Episodes without ${subsLanguage} subtitles.</h2>
            <br>
            Download missed subtitles for selected episodes <input class="btn btn-inline" type="submit" value="Go"/>
            <div>
                <button type="button" class="btn btn-xs selectAllShows"><a>Select all</a></button>
                <button type="button" class="btn btn-xs unselectAllShows"><a>Clear all</a></button>
            </div>
            <br>
            <table class="sickrageTable manageTable" cellspacing="1" border="0" cellpadding="0">
                % for cur_indexer_id in sorted_show_ids:
                    <tr id="${cur_indexer_id}">
                        <th>
                            <input type="checkbox" class="allCheck" id="allCheck-${cur_indexer_id}"
                                   name="${cur_indexer_id}-all" checked="checked"/>
                        </th>
                        <th colspan="3" style="width: 100%; text-align: left;">
                            <a class="whitelink"
                               href="${srWebRoot}/home/displayShow?show=${cur_indexer_id}">${show_names[cur_indexer_id]}
                            </a>
                            (${ep_counts[cur_indexer_id]}) <input type="button" class="pull-right get_more_eps btn"
                                                                  id="${cur_indexer_id}" value="Expand"/>
                        </th>
                    </tr>
                % endfor
            </table>
        </form>
    % endif
</%block>
