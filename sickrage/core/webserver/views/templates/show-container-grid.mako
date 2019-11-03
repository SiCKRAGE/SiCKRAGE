% if not is_loading:
    <%!
        import re
        import calendar
        import unidecode
        import datetime

        import sickrage
        from sickrage.core.helpers import srdatetime, pretty_file_size
        from sickrage.core.media.util import showImage
    %>
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
    <%
        download_stat_tip = ''
        display_status = show.status

        if display_status:
            if re.search(r'(?i)(?:new|returning)\s*series', show.status):
                display_status = _('Continuing')
            elif re.search(r'(?i)(?:nded)', show.status):
                display_status = _('Ended')

        cur_airs_next = show.airs_next
        cur_snatched = show.episodes_snatched
        cur_downloaded = show.episodes_downloaded
        cur_total = len(show.episodes) - show.episodes_special - show.episodes_unaired

        if cur_total != 0:
            download_stat = str(cur_downloaded)
            download_stat_tip = _("Downloaded: ") + str(cur_downloaded)
            if cur_snatched > 0:
                download_stat = download_stat
                download_stat_tip = download_stat_tip + " " + _("Snatched: ") + str(cur_snatched)

            download_stat = download_stat + " / " + str(cur_total)
            download_stat_tip = download_stat_tip + " " + _("Total: ") + str(cur_total)
        else:
            download_stat = '?'
            download_stat_tip = _("no data")

        progressbar_percent = int(cur_downloaded * 100 / cur_total if cur_total > 0 else 1)
        progressbar_percent_class = "progress-{}".format('100' if progressbar_percent > 80 else '80' if progressbar_percent > 60 else '60' if progressbar_percent > 40 else '40' if progressbar_percent > 20 else '20')

        data_date = '6000000000.0'
        if cur_airs_next > datetime.date.min:
            data_date = calendar.timegm(srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, show.airs, show.network), convert=True).dt.timetuple())
        elif display_status:
            if 'nded' not in display_status and 1 == int(show.paused):
                data_date = '5000000500.0'
            elif 'ontinu' in display_status:
                data_date = '5000000000.0'
            elif 'nded' in display_status:
                data_date = '5000000100.0'

        network_class_name = None
        if show.network:
            network_class_name = re.sub(r'(?!\w|\s).', '', unidecode.unidecode(show.network))
            network_class_name = re.sub(r'\s+', '-', network_class_name)
            network_class_name = re.sub(r'^(\s*)([\W\w]*)(\b\s*$)', '\\2', network_class_name)
            network_class_name = network_class_name.lower()
    %>
    <div class="show-container" id="show${show.indexer_id}" data-name="${show.name}"
         data-date="${data_date}" data-network="${show.network}"
         data-progress="${progressbar_percent}">
        <div class="card card-block text-white bg-dark m-1 shadow">
            <a href="${srWebRoot}/home/displayShow?show=${show.indexer_id}">
                <img alt="" class="card-img-top" src="${srWebRoot}${showImage(show.indexer_id, 'poster').url}"/>
            </a>
            <div class="card-header bg-dark py-0 px-0">
                <span style="display: none;">${download_stat}</span>
                <div class="bg-dark progress shadow">
                    <div class="progress-bar ${progressbar_percent_class} d-print-none"
                         style="width: ${progressbar_percent}%">
                        <div class="progressbarText" title="${download_stat_tip}">${download_stat}</div>
                    </div>
                </div>
            </div>
            <div class="card-body text-truncate py-1 px-1 small">
                <div class="show-title">
                    ${show.name}
                </div>

                <div class="show-date" style="color: grey">
                    % if cur_airs_next > datetime.date.min:
                        <% ldatetime = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(cur_airs_next, show.airs, show.network), convert=True).dt %>
                        <%
                            try:
                              out = srdatetime.SRDateTime(ldatetime).srfdate()
                            except ValueError:
                              out = _('Invalid date')
                        %>
                    % else:
                        <% display_status = show.status %>
                        <%
                            out = 'UNKNOWN'
                            if display_status:
                              out = display_status
                              if 'nded' not in display_status and 1 == int(show.paused):
                                  out = _('Paused')
                        %>
                    % endif
                  ${out}
                </div>
            </div>
            <div class="card-footer show-details p-1">
                <table class="show-details w-100" style="height:40px">
                    <tr>
                        <td class="text-left align-middle w-25">
                            % if show.network:
                                <span>
                                    <i class="show-network-image sickrage-network sickrage-network-${network_class_name}"
                                       title="${show.network}"></i>
                                </span>
                            % else:
                                <span>
                                    <i class="show-network-image sickrage-network sickrage-network-unknown"
                                       title="${_('No Network')}"></i>
                                </span>
                            % endif
                        </td>
                        <td class="text-right align-middle w-25">
                            ${renderQualityPill(show.quality, showTitle=True)}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
% else:
    <div class="show-container" data-name="0" data-date="010101" data-network="0"
         data-progress="101">
        <div class="card card-block text-white bg-dark m-1 shadow">
            <img alt="" title="${show.name}" class="card-img-top" src="${srWebRoot}/images/poster.png"/>
            <div class="card-body text-truncate py-1 px-1 small">
                <div class="show-title">
                    ${show.name}
                </div>
            </div>
            <div class="card-footer show-details p-1">
                <div class="show-details">
                    <div class="show-add text-center">${_('... Loading ...')}</div>
                </div>
            </div>
        </div>
    </div>
% endif