<%inherit file="./layouts/main.mako"/>
<%!
    import os.path
    import datetime
    import re
    import time

    import sickrage
    from sickrage.core.helpers import srdatetime
    from sickrage.core.common import Overview, Quality, EpisodeStatus
    from sickrage.core.tv.show.history import History
    from sickrage.core.enums import  HistoryLayout
%>
<%block name="content">
    <%namespace file="./includes/quality_defaults.mako" import="renderQualityPill"/>
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3 class="float-left">${title}</h3>
                    <div class="float-right">
                        <div class="form-inline">
                            <select name="history_limit" id="history_limit" class="form-control mr-sm-2">
                                <option value="10" ${('', 'selected')[limit == 10]}>10</option>
                                <option value="25" ${('', 'selected')[limit == 25]}>25</option>
                                <option value="50" ${('', 'selected')[limit == 50]}>50</option>
                                <option value="100" ${('', 'selected')[limit == 100]}>100</option>
                                <option value="250" ${('', 'selected')[limit == 250]}>250</option>
                                <option value="500" ${('', 'selected')[limit == 500]}>500</option>
                                <option value="750" ${('', 'selected')[limit == 750]}>750</option>
                                <option value="1000" ${('', 'selected')[limit == 1000]}>1000</option>
                                <option value="0"   ${('', 'selected')[limit == 0  ]}>${_('All')}</option>
                            </select>

                            <select name="HistoryLayout" class="form-control"
                                    onchange="location = this.options[this.selectedIndex].value;">
                                % for item in HistoryLayout:
                                    <option value="${srWebRoot}/setHistoryLayout/?layout=${item.name}" ${('', 'selected')[sickrage.app.config.gui.history_layout == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>

                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        % if sickrage.app.config.gui.history_layout == HistoryLayout.DETAILED:
                            <table id="historyTable" class="table ">
                                <thead class="thead-dark">
                                <tr>
                                    <th>${_('Time')}</th>
                                    <th>${_('Episode')}</th>
                                    <th>${_('Action')}</th>
                                    <th>${_('Provider')}</th>
                                    <th>${_('Release Group')}</th>
                                    <th>${_('Quality')}</th>
                                </tr>
                                </thead>

                                <tbody>
                                    % for hItem in historyResults:
                                        <% curStatus, curQuality = Quality.split_composite_status(int(hItem["action"])) %>
                                        <tr>
                                            <td class="table-fit">
                                                <% airDate = srdatetime.SRDateTime(hItem["date"]).srfdatetime(show_seconds=True) %>
                                                <% isoDate = hItem["date"].isoformat() %>
                                                <time datetime="${isoDate}" class="date">${airDate}</time>
                                            </td>
                                            <td class="tvShow">
                                                <a href="${srWebRoot}/home/displayShow?show=${hItem["series_id"]}#S${hItem["season"]}E${hItem["episode"]}">
                                                    ${hItem["show_name"]}
                                                    - ${"S{:02d}".format(hItem['season'])}${"E{:02d}".format(hItem['episode'])}${('', ' <span class="badge badge-success">Proper</span>')['proper' in hItem["resource"].lower() or 'repack' in hItem["resource"].lower()]}
                                                </a>
                                            </td>
                                            <td class="table-fit" ${('', 'class="subtitles_column"')[curStatus == EpisodeStatus.SUBTITLED]}>
                                                % if curStatus == EpisodeStatus.SUBTITLED:
                                                    <i class="sickrage-flags sickrage-flags-${hItem['resource']}"></i>
                                                % endif
                                                <span style="cursor: help; vertical-align:middle;"
                                                      title="${os.path.basename(hItem['resource'])}">${curStatus.display_name}</span>
                                            </td>
                                            <td class="table-fit">
                                                % if hItem["provider"]:
                                                    % if hItem["provider"].lower() in sickrage.app.search_providers.all():
                                                    <% provider = sickrage.app.search_providers.all()[hItem["provider"].lower()] %>
                                                        <i class="sickrage-search-providers sickrage-search-providers-${provider.id}"
                                                           style="vertical-align:middle;">
                                                        </i>
                                                        <span style="vertical-align:middle;">${provider.name}</span>
                                                    % else:
                                                        <span style="vertical-align:middle;">${hItem["provider"]}</span>
                                                    % endif
                                                % endif
                                            </td>
                                            <td class="table-fit">${hItem['release_group']}</td>
                                            <td style="display: none;">${curQuality}</td>
                                            <td class="table-fit">${renderQualityPill(curQuality)}</td>
                                        </tr>
                                    % endfor
                                </tbody>
                            </table>
                        % else:
                            <table id="historyTable" class="table">
                                <thead class="thead-dark">
                                <tr>
                                    <th class="text-nowrap">${_('Time')}</th>
                                    <th>${_('Episode')}</th>
                                    <th>${_('Snatched')}</th>
                                    <th>${_('Downloaded')}</th>
                                    % if sickrage.app.config.subtitles.enable:
                                        <th>${_('Subtitled')}</th>
                                    % endif
                                    <th>${_('Quality')}</th>
                                </tr>
                                </thead>

                                <tbody>
                                    % for hItem in compactResults:
                                        <tr>
                                            <td class="table-fit">
                                                <% airDate = srdatetime.SRDateTime(hItem["actions"][0]["time"]).srfdatetime(show_seconds=True) %>
                                                <% isoDate = hItem["actions"][0]["time"].isoformat() %>
                                                <time datetime="${isoDate}" class="date">${airDate}</time>
                                            </td>
                                            <td class="tvShow" width="25%">
                                                <span>
                                                    <a href="${srWebRoot}/home/displayShow?show=${hItem["series_id"]}#S${hItem["season"]}E${hItem["episode"]}">
                                                        ${hItem["show_name"]}
                                                        - ${"S{:02d}".format(hItem['season'])}${"E{:02d}".format(hItem['episode'])}${('', ' <span class="badge badge-success">Proper</span>')['proper' in hItem["resource"].lower() or 'repack' in hItem["resource"].lower()]}
                                                    </a>
                                                </span>
                                            </td>
                                            <td class="table-fit"
                                                data-provider="${sorted(hItem["actions"], key=lambda x:sorted(x.keys()))[0]["provider"]}">
                                                % for action in sorted(hItem["actions"], key=lambda x:sorted(x.keys())):
                                                    <% curStatus, curQuality = Quality.split_composite_status(int(action["action"])) %>
                                                    % if curStatus in [EpisodeStatus.SNATCHED, EpisodeStatus.FAILED]:
                                                        % if action["provider"].lower() in sickrage.app.search_providers.all():
                                                        <% provider = sickrage.app.search_providers.all()[action["provider"].lower()] %>
                                                            <i class="sickrage-search-providers sickrage-search-providers-${provider.id}"
                                                               title="${provider.name}: ${os.path.basename(action["resource"])}"
                                                               style="vertical-align:middle;cursor: help;"></i>
                                                        % else:
                                                            <i class="sickrage-search-providers sickrage-search-providers-missing"
                                                               style="vertical-align:middle;"
                                                               title="${_('missing provider')}"></i>
                                                        % endif
                                                    % endif
                                                % endfor
                                            </td>
                                            <td class="table-fit">
                                                % for action in sorted(hItem["actions"], key=lambda x:sorted(x.keys())):
                                                    <% curStatus, curQuality = Quality.split_composite_status(int(action["action"])) %>
                                                    % if curStatus in [EpisodeStatus.DOWNLOADED, EpisodeStatus.ARCHIVED]:
                                                        % if action["provider"] != "-1":
                                                            <span style="cursor: help;"
                                                                  title="${os.path.basename(action["resource"])}"><i>${action["release_group"]}</i></span>
                                                        % else:
                                                            <span style="cursor: help;"
                                                                  title="${os.path.basename(action["resource"])}"></span>
                                                        % endif
                                                    % endif
                                                % endfor
                                            </td>
                                            % if sickrage.app.config.subtitles.enable:
                                                <td class="table-fit">
                                                    % for action in sorted(hItem["actions"], key=lambda x:sorted(x.keys())):
                                                        <% curStatus, curQuality = Quality.split_composite_status(int(action["action"])) %>
                                                        % if curStatus == EpisodeStatus.SUBTITLED:
                                                            <i class="sickrage-subtitles sickrage-subtitles-${action['provider']}"
                                                               style="vertical-align:middle;"
                                                               title="${action["provider"].capitalize()}: ${os.path.basename(action["resource"])}"></i>
                                                            <span style="vertical-align:middle;"> / </span>
                                                            <i class="sickrage-flags sickrage-flags-${action['resource']}"></i>
                                                            &nbsp;
                                                        % endif
                                                    % endfor
                                                </td>
                                            % endif
                                            <td class="table-fit" width="14%" data-quality="${curQuality}">
                                                ${renderQualityPill(curQuality)}
                                            </td>
                                        </tr>
                                    % endfor
                                </tbody>
                            </table>
                        % endif
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
