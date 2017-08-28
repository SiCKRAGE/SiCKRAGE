<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import datetime
    import re

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings, Overview
%>
<%block name="content">
    <div class="row">
        <div class="col-xs-12 text-center">
            <label for="limit" class="badge">Limit:
                <select name="limit" id="limit" class="form-control form-control-inline input-sm">
                    <option value="100" ${('', 'selected')[limit == 100]}>100</option>
                    <option value="250" ${('', 'selected')[limit == 250]}>250</option>
                    <option value="500" ${('', 'selected')[limit == 500]}>500</option>
                    <option value="0"   ${('', 'selected')[limit == 0  ]}>All</option>
                </select>
            </label>
        </div>
        <div class="col-lg-6 col-md-6 col-sm-8 col-xs-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="horizontal-scroll">
                <table id="failedTable" class="sickrageTable tablesorter" cellspacing="1" border="0" cellpadding="0">
                    <thead>
                    <tr>
                        <th class="nowrap" width="75%" style="text-align: left;">Release</th>
                        <th width="10%">Size</th>
                        <th width="14%">Provider</th>
                        <th width="1%">Remove<br>
                            <input type="checkbox" class="bulkCheck" id="removeCheck" title="Remove failed release"/>
                        </th>
                    </tr>
                    </thead>
                    <tfoot>
                    <tr>
                        <td rowspan="1" colspan="4">
                            <input type="button" class="btn pull-right" value="Submit" id="submitMassRemove">
                        </td>
                    </tr>
                    </tfoot>
                    <tbody>
                        % for hItem in failedResults:
                            <% curRemove  = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-"+hItem["release"]+"\" />" %>
                            <tr>
                                <td class="nowrap">${hItem["release"]}</td>
                                <td align="center">
                                    % if hItem["size"] != -1:
                                        ${hItem["size"]}
                                    % else:
                                        ?
                                    % endif
                                </td>
                                <td align="center">
                                    <% provider = sickrage.srCore.providersDict.all()[hItem["provider"].lower()] %>
                                    % if provider is not None:
                                        <img src="${srWebRoot}/images/providers/${provider.imageName}" width="16"
                                             height="16"
                                             alt="${provider.name}"
                                             title="${provider.name}"/>
                                    % else:
                                        <img src="${srWebRoot}/images/providers/missing.png" width="16" height="16"
                                             alt="missing provider"
                                             title="missing provider"/>
                                    % endif
                                </td>
                                <td align="center">${curRemove}</td>
                            </tr>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</%block>
