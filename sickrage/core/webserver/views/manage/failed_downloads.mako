<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import datetime
    import re

    import sickrage
    from sickrage.core.helpers import pretty_file_size
    from sickrage.core.common import Overview, Quality
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3 class="float-left">${title}</h3>
                    <div class="float-right">
                        <div class="form-inline">
                            <select name="limit" id="limit" class="form-control" title="${_('Limit')}">
                                <option value="100" ${('', 'selected')[limit == 100]}>100</option>
                                <option value="250" ${('', 'selected')[limit == 250]}>250</option>
                                <option value="500" ${('', 'selected')[limit == 500]}>500</option>
                                <option value="0"   ${('', 'selected')[limit == 0  ]}>All</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table id="failedTable" class="table">
                            <thead class="thead-dark">
                            <tr>
                                <th>${_('Release')}</th>
                                <th>${_('Size')}</th>
                                <th>${_('Provider')}</th>
                                <th>
                                    <input type="checkbox" class="bulkCheck" id="removeCheck"/>
                                </th>
                            </tr>
                            </thead>
                            <tbody>
                                % for hItem in failedResults:
                                    <tr>
                                        <td class="text-nowrap">${hItem.release}</td>
                                        <td class="table-fit">
                                            % if hItem.size != -1:
                                                ${pretty_file_size(hItem.size)}
                                            % else:
                                                ?
                                            % endif
                                        </td>
                                        <td class="table-fit">
                                            % if hItem.provider.lower() in sickrage.app.search_providers.all():
                                            <% provider = sickrage.app.search_providers.all()[hItem.provider.lower()] %>
                                                <i class="sickrage-search-providers sickrage-search-providers-${provider.id}"
                                                   title="${provider.name}"
                                                   style="vertical-align:middle;cursor: help;"></i>
                                            % else:
                                                <i class="sickrage-search-providers sickrage-search-providers-missing"
                                                   style="vertical-align:middle;"
                                                   title="${_('missing provider')}"></i>
                                            % endif
                                        </td>
                                        <td class="table-fit">
                                            <input type="checkbox" class="removeCheck" id="remove-${hItem.release}"/>
                                        </td>
                                    </tr>
                                % endfor
                            </tbody>
                        </table>
                    </div>
                    <input type="button" class="btn" value="${_('Clear')}" id="submitMassRemove">
                </div>
            </div>
        </div>
    </div>
</%block>
