<%!
    import re
    import calendar
    import unidecode
    import datetime
    from functools import cmp_to_key

    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.helpers import srdatetime, pretty_file_size
    from sickrage.core.media.util import showImage
%>
<%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
<%
    download_stat_tip = ''

    cur_airs_next = show.airs_next
    cur_airs_prev = show.airs_prev
    cur_snatched = show.episodes_snatched
    cur_downloaded = show.episodes_downloaded
    cur_total = len(show.episodes) - show.episodes_special - show.episodes_unaired
    show_size = show.total_size

    if cur_total != 0:
        download_stat = str(cur_downloaded)
        download_stat_tip = _("Downloaded: ") + str(cur_downloaded)
        if cur_snatched > 0:
            download_stat = download_stat + "+" + str(cur_snatched)
            download_stat_tip = download_stat_tip + "&#013;" + _("Snatched: ") + str(cur_snatched)

        download_stat = download_stat + " / " + str(cur_total)
        download_stat_tip = download_stat_tip + "&#013;" + _("Total: ") + str(cur_total)
    else:
        download_stat = '?'
        download_stat_tip = _("no data")

    progressbar_percent = int(cur_downloaded * 100 / cur_total if cur_total > 0 else 1)
    progressbar_percent_class = "progress-{}".format('100' if progressbar_percent > 80 else '80' if progressbar_percent > 60 else '60' if progressbar_percent > 40 else '40' if progressbar_percent > 20 else '20')

    network_class_name = None
    if show.network:
        network_class_name = re.sub(r'(?!\w|\s).', '', unidecode.unidecode(show.network))
        network_class_name = re.sub(r'\s+', '-', network_class_name)
        network_class_name = re.sub(r'^(\s*)([\W\w]*)(\b\s*$)', '\\2', network_class_name)
        network_class_name = network_class_name.lower()
%>
<tr class="show-list-item">
    % if cur_airs_next > datetime.date.min:
    <% airDate = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, show.airs, show.network), convert=True).dt %>
    % try:
        <td class="table-fit align-middle">
            <time datetime="${airDate.isoformat()}"
                  class="date">${srdatetime.SRDateTime(airDate).srfdate()}</time>
        </td>
    % except ValueError:
        <td class="table-fit"></td>
    % endtry
    % else:
        <td class="table-fit"></td>
    % endif

    % if cur_airs_prev > datetime.date.min:
    <% airDate = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_prev, show.airs, show.network), convert=True).dt %>
    % try:
        <td class="table-fit align-middle">
            <time datetime="${airDate.isoformat()}" class="date">
                ${srdatetime.SRDateTime(airDate).srfdate()}
            </time>
        </td>
    % except ValueError:
        <td class="table-fit"></td>
    % endtry
    % else:
        <td class="table-fit"></td>
    % endif

    % if sickrage.app.config.home_layout == 'small':
        <td class="tvShow">
            <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}"
               title="${show.name}">
                <img src="${srWebRoot}${showImage(show.indexer_id, 'poster_thumb').url}"
                     class="img-smallposter rounded shadow"
                     alt="${show.indexer_id}"/>
                ${show.name}
            </a>
        </td>
    % elif sickrage.app.config.home_layout == 'banner':
        <td class="table-fit tvShow">
            <span class="d-none">${show.name}</span>
            <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}">
                <img src="${srWebRoot}${showImage(show.indexer_id, 'banner').url}"
                     class="img-banner rounded shadow" alt="${show.indexer_id}"
                     title="${show.name}"/>
            </a>
        </td>
    % elif sickrage.app.config.home_layout == 'simple':
        <td class="tvShow">
            <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}">
                ${show.name}
            </a>
        </td>
    % endif

    % if sickrage.app.config.home_layout != 'simple':
        <td class="table-fit align-middle">
            % if show.network:
                <span title="${show.network}">
                    <i class="sickrage-network sickrage-network-${network_class_name}"></i>
                </span>
                <span class="d-none d-print-inline">${show.network}</span>
            % else:
                <span title="${_('No Network')}">
                    <i class="sickrage-network sickrage-network-unknown"></i>
                </span>
                <span class="d-none d-print-inline">No Network</span>
            % endif
        </td>
    % else:
        <td class="table-fit">
            <span title="${show.network}">${show.network}</span>
        </td>
    % endif

    <td class="table-fit align-middle">${renderQualityPill(show.quality, showTitle=True)}</td>

    <td class="align-middle">
        <span style="display: none;">${download_stat}</span>
        <div class="bg-dark rounded shadow">
            <div class="progress-bar rounded ${progressbar_percent_class}" style="width: ${progressbar_percent}%">
                <div class="progressbarText" title="${download_stat_tip}">${download_stat}</div>
            </div>
        </div>
    </td>

    <td class="table-fit align-middle" data-show-size="${show_size}">
        ${pretty_file_size(show_size)}
    </td>

    <td class="table-fit align-middle">
        <i class="fa ${("fa-times text-danger", "fa-check text-success")[not bool(show.paused)]}"></i>
        <span class="d-none d-print-inline">${('No', 'Yes')[not bool(show.paused)]}</span>
    </td>

    <td class="table-fit align-middle">
        % if show.status and re.search(r'(?i)(?:new|returning)\s*series', show.status):
            ${_('Continuing')}
        % elif show.status and re.search('(?i)(?:nded)', show.status):
            ${_('Ended')}
        % else:
            ${show.status}
        % endif
    </td>
</tr>