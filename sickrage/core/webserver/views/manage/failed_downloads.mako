<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import datetime
    import re

    import sickrage
    from sickrage.core.helpers import pretty_filesize
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings, Overview
%>
<%block name="content">
    <div class="row">
        <div class="col-md-10 mx-auto">
            <div class="card mt-3 mb-3">
                <div class="card-header">
                    <h3 class="float-lg-left">${title}</h3>
                    <div class="float-lg-right">
                        <select name="limit" id="limit" class="form-control" title="${_('Limit')}">
                            <option value="100" ${('', 'selected')[limit == 100]}>100</option>
                            <option value="250" ${('', 'selected')[limit == 250]}>250</option>
                            <option value="500" ${('', 'selected')[limit == 500]}>500</option>
                            <option value="0"   ${('', 'selected')[limit == 0  ]}>All</option>
                        </select>
                    </div>
                </div>
                <div class="card-body">
                    <table id="failedTable" class="table">
                        <thead>
                        <tr>
                            <th align="left" class="nowrap">${_('Release')}</th>
                            <th class="table-fit text-center">${_('Size')}</th>
                            <th class="table-fit text-center">${_('Provider')}</th>
                            <th class="table-fit text-center" title="${_('Remove All')} ">
                                <input type="checkbox" class="bulkCheck" id="removeCheck"/>
                            </th>
                        </tr>
                        </thead>
                        <tbody>
                            % for hItem in failedResults:
                                <% curRemove  = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-"+hItem["release"]+"\" />" %>
                                <tr>
                                    <td class="nowrap">${hItem["release"]}</td>
                                    <td align="center">
                                        % if hItem["size"] != -1:
                                            ${pretty_filesize(hItem["size"])}
                                        % else:
                                            ?
                                        % endif
                                    </td>
                                    <td align="center">
                                        <% provider = sickrage.app.search_providers.all()[hItem["provider"].lower()] %>
                                        % if provider is not None:
                                            <i class="sickrage-providers sickrage-providers-${provider.id}"
                                               title="${provider.name}"></i>
                                        % else:
                                            <i class="sickrage-providers sickrage-providers-missing"
                                               title="${_('missing provider')}"></i>
                                        % endif
                                    </td>
                                    <td align="center">${curRemove}</td>
                                </tr>
                            % endfor
                        </tbody>
                    </table>
                    <input type="button" class="btn" value="${_('Submit')}"
                                                           id="submitMassRemove">
                </div>
            </div>
        </div>
    </div>
</%block>
