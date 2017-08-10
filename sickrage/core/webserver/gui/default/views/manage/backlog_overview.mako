<%inherit file="../layouts/main.mako"/>
<%!
    import datetime

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Overview, Quality, qualityPresets, qualityPresetStrings
    from sickrage.core.helpers import srdatetime
    from sickrage.core.updaters import tz_updater
%>
<%block name="content">
    <% totalWanted = 0 %>
    <% totalQual = 0 %>

    % for curShow in sickrage.srCore.SHOWLIST:
        <% totalWanted = totalWanted + showCounts[curShow.indexerid][Overview.WANTED] %>
        <% totalQual = totalQual + showCounts[curShow.indexerid][Overview.QUAL] %>
    % endfor

    <div class="row">
        <div class="col-lg-8 col-md-7 col-sm-6 col-xs-12 pull-right">
            <div class="pull-right">
                <span class="listing-key wanted">Wanted: <b>${totalWanted}</b></span>
                <span class="listing-key qual">Low Quality: <b>${totalQual}</b></span>
            </div>
        </div>
        <div class="col-lg-4 col-md-5 col-sm-6 col-xs-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <div class="input-group input350">
                <div class="input-group-addon">
                    <span class="fa fa-binoculars"></span>
                </div>
                <select id="pickShow" class="form-control form-control-inline input-sm">
                    % for curShow in sorted(sickrage.srCore.SHOWLIST, key=lambda x: x.name):
                        % if showCounts[curShow.indexerid][Overview.QUAL] + showCounts[curShow.indexerid][Overview.WANTED] != 0:
                            <option value="${curShow.indexerid}">${curShow.name}</option>
                        % endif
                    % endfor
                </select>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <table class="sickrageTable" cellspacing="0" border="0" cellpadding="0">
                % for curShow in sorted(sickrage.srCore.SHOWLIST, key=lambda x: x.name):
                    % if not showCounts[curShow.indexerid][Overview.QUAL] + showCounts[curShow.indexerid][Overview.WANTED] == 0:
                        <tr class="seasonheader" id="show-${curShow.indexerid}">
                            <td colspan="3" class="align-left">
                                <br>
                                <h2>
                                    <a href="${srWebRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a>
                                </h2>
                                <div class="pull-right">
                                    <span class="listing-key wanted">Wanted: <b>${showCounts[curShow.indexerid][Overview.WANTED]}</b></span>
                                    <span class="listing-key qual">Low Quality: <b>${showCounts[curShow.indexerid][Overview.QUAL]}</b></span>
                                    <a class="btn btn-inline forceBacklog"
                                       href="${srWebRoot}/manage/backlogShow?indexer_id=${curShow.indexerid}"><i
                                            class="icon-play-circle icon-white"></i> Force Backlog</a>
                                </div>
                            </td>
                        </tr>

                        <tr class="seasoncols">
                            <th>Episode</th>
                            <th>Name</th>
                            <th class="nowrap">Airdate</th>
                        </tr>

                    % for curResult in showResults[curShow.indexerid]:
                        <% whichStr = str(curResult['season']) + 'x' + str(curResult['episode']) %>
                        <% overview = showCats[curShow.indexerid][whichStr] %>

                        % if overview in (Overview.QUAL, Overview.WANTED):
                            <tr class="seasonstyle ${Overview.overviewStrings[showCats[curShow.indexerid][whichStr]]}">
                                <td class="tableleft" align="center">${whichStr}</td>
                                <td class="tableright" align="center" class="nowrap">
                                    ${curResult["name"]}
                                </td>
                                <td>
                                    <% airDate = srdatetime.srDateTime.convert_to_setting(tz_updater.parse_date_time(curResult['airdate'], curShow.airs, curShow.network)) %>
                                    % if int(curResult['airdate']) != 1:
                                        <time datetime="${airDate.isoformat()}"
                                              class="date">${srdatetime.srDateTime.srfdatetime(airDate)}</time>
                                    % else:
                                        Never
                                    % endif
                                </td>
                            </tr>
                        % endif
                    % endfor
                    % endif
                % endfor
            </table>
        </div>
    </div>

</%block>
