<%!
    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.core.enums import SeriesProviderID
%>

<table id="addRootDirTable" class="table">
    <thead class="thead-dark">
    <tr>
        <th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th>
        <th>${_('Directory')}</th>
        <th>${_('Show Name (tvshow.nfo)')}</th>
        <th>${_('Series Provider')}</th>
    </tr>
    </thead>
    <tbody>
        % for curDir in dirList:
            % if not curDir['added_already']:
                <%
                    series_id = curDir['dir']
                    series_provider_id = sickrage.app.config.general.series_provider_default

                    if curDir['existing_info'][0]:
                        series_id = "{}|{}|{}".format(series_id, curDir['existing_info'][0], curDir['existing_info'][1])
                        series_provider_id = curDir['existing_info'][2]
                %>

                <tr>
                    <td class="table-fit col-checkbox"><input type="checkbox" id="${series_id}" class="dirCheck" checked=checked>
                    </td>
                    <td><label for="${series_id}">${curDir['display_dir']}</label></td>
                    % if curDir['existing_info'][1] and series_provider_id:
                        <td class="table-fit">
                            <a href="${anon_url(sickrage.app.series_providers[series_provider_id].show_url, curDir['existing_info'][0])}">${curDir['existing_info'][1]}</a>
                        </td>
                    % else:
                        <td>?</td>
                    % endif
                    <td class="table-fit">
                        <select class="rounded" name="series_provider_id">
                            % for item in SeriesProviderID:
                                <option value="${item.name}" ${('', 'selected')[series_provider_id == item]}>${item.display_name}</option>
                            % endfor
                        </select>
                    </td>
                </tr>
            % endif
        % endfor
    </tbody>
</table>
