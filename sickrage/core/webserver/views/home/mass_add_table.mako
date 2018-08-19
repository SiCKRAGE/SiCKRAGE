<%!
    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.indexers import IndexerApi
%>

<table id="addRootDirTable" class="table">
    <thead class="thead-dark">
    <tr>
        <th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th>
        <th>${_('Directory')}</th>
        <th>${_('Show Name (tvshow.nfo)')}</th>
        <th>${_('Indexer')}</th>
    </tr>
    </thead>
    <tbody>
        % for curDir in dirList:
            % if not curDir['added_already']:
                <%
                    indexer = 0
                    show_id = curDir['dir']

                    if curDir['existing_info'][0]:
                        show_id = "{}|{}|{}".format(show_id, curDir['existing_info'][0], curDir['existing_info'][1])
                        indexer = curDir['existing_info'][2]

                    if curDir['existing_info'][0]:
                        indexer = curDir['existing_info'][2]
                    elif sickrage.app.config.indexer_default > 0:
                        indexer = sickrage.app.config.indexer_default
                %>

                <tr>
                    <td class="table-fit col-checkbox"><input type="checkbox" id="${show_id}" class="dirCheck" checked=checked>
                    </td>
                    <td><label for="${show_id}">${curDir['display_dir']}</label></td>
                    % if curDir['existing_info'][1] and indexer > 0:
                        <td class="table-fit">
                            <a href="${anon_url(IndexerApi(indexer).config['show_url'], curDir['existing_info'][0])}">${curDir['existing_info'][1]}</a>
                        </td>
                    % else:
                        <td>?</td>
                    % endif
                    <td class="table-fit">
                        <select class="rounded" name="indexer">
                            % for curIndexer in IndexerApi().indexers.items():
                                <option value="${curIndexer[0]}" ${('', 'selected')[curIndexer[0] == indexer]}>${curIndexer[1]}</option>
                            % endfor
                        </select>
                    </td>
                </tr>
            % endif
        % endfor
    </tbody>
</table>
