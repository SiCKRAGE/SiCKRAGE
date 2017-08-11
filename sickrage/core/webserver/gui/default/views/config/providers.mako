<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveProviders' %></%def>
<%!
    import json
    import sickrage
    from sickrage.providers import NZBProvider, TorrentProvider, NewznabProvider, TorrentRssProvider
    from sickrage.providers.torrent import thepiratebay
    from sickrage.core.helpers import anon_url
%>

<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Provider Priorities</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Provider Options</a></li>
    % if sickrage.srCore.srConfig.USE_NZBS:
        <li><a data-toggle="tab" href="#core-tab-pane3">Custom Newznab Providers</a></li>
    % endif
    % if sickrage.srCore.srConfig.USE_TORRENTS:
        <li><a data-toggle="tab" href="#core-tab-pane4">Custom Torrent Providers</a></li>
    % endif
</%block>

<%block name="metas">
    <%
        newznab_providers = ''
        torrentrss_providers = ''

        if sickrage.srCore.srConfig.USE_NZBS:
            for providerID, providerObj in sickrage.srCore.providersDict.newznab().items():
                if providerObj.default:
                    continue

                newznab_providers += '{}!!!'.format(
                        '|'.join([providerID,
                        providerObj.name,
                        providerObj.urls["base_url"],
                        providerObj.key,
                        providerObj.catIDs,
                        ("false", "true")[bool(providerObj.default)],
                        ("false", "true")[bool(sickrage.srCore.srConfig.USE_NZBS)]]))

        if sickrage.srCore.srConfig.USE_TORRENTS:
            for providerID, providerObj in sickrage.srCore.providersDict.torrentrss().items():
                if providerObj.default:
                    continue

                torrentrss_providers += '{}!!!'.format(
                    '|'.join([providerID,
                              providerObj.name,
                              providerObj.urls["base_url"],
                              providerObj.cookies,
                              providerObj.titleTAG,
                              ("false", "true")[bool(providerObj.default)],
                              ("false", "true")[bool(sickrage.srCore.srConfig.USE_TORRENTS)]]))
    %>
    <meta data-var="NEWZNAB_PROVIDERS" data-content="${newznab_providers}">
    <meta data-var="TORRENTRSS_PROVIDERS" data-content="${torrentrss_providers}">
</%block>

<%block name="pages">
    <div id="core-tab-pane1" class="row tab-pane fade in active">

        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
            <h3>Provider Priorities</h3>
            <p>Check off and drag the providers into the order you want them to be used.</p>
            <p>At least one provider is required but two are recommended.</p>

            % if not sickrage.srCore.srConfig.USE_NZBS or not sickrage.srCore.srConfig.USE_TORRENTS:
                <blockquote style="margin: 20px 0;">
                    NZB/Torrent providers can be toggled in <b><a href="${srWebRoot}/config/search">Search
                    Clients</a></b>
                </blockquote>
            % else:
                <br>
            % endif

            <div>
                <p class="note">
                    <span class="red-text fa fa-exclamation-circle"></span> Provider does not support backlog searches
                    at this time.
                </p>
            </div>
        </div>

        <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
            <ul id="provider_order_list">
                % for providerID, providerObj in sickrage.srCore.providersDict.sort().items():
                    % if (providerObj.type in [NZBProvider.type, NewznabProvider.type] and sickrage.srCore.srConfig.USE_NZBS) or (providerObj.type in [TorrentProvider.type, TorrentRssProvider.type] and sickrage.srCore.srConfig.USE_TORRENTS):
                        <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[bool(providerObj.type in [TorrentProvider.type, TorrentRssProvider.type])]}"
                            id="${providerID}">
                            <input type="checkbox" id="enable_${providerID}"
                                   class="provider_enabler" ${('', 'checked')[bool(providerObj.isEnabled)]}/>
                            <a href="${anon_url(providerObj.urls['base_url'])}" class="imgLink"
                               rel="noreferrer"
                               onclick="window.open(this.href, '_blank'); return false;"><img
                                    src="${srWebRoot}/images/providers/${providerObj.imageName}"
                                    alt="${providerObj.name}" title="${providerObj.name}" width="16"
                                    height="16" style="vertical-align:middle;"/></a>
                            <label for="enable_${providerID}"
                                   style="vertical-align:middle;">${providerObj.name}</label>
                            <span class="fa fa-arrows-v pull-right"
                                  style="vertical-align:middle;"></span>
                            <span class="fa ${('fa-unlock','fa-lock')[bool(providerObj.private)]} pull-right"
                                  style="vertical-align:middle;"></span>
                            ${('<span class="red-text fa fa-exclamation-circle pull-right"></span>', '')[bool(providerObj.supports_backlog)]}
                        </li>
                    % endif
                % endfor
            </ul>
            <input type="hidden" name="provider_order" id="provider_order"
                   value="${" ".join([providerID+':'+str(int(providerObj.isEnabled)) for providerID, providerObj in sickrage.srCore.providersDict.all().items()])}"/>
            <br><input type="submit" class="btn config_submitter" value="Save Changes"/><br>
        </fieldset>
    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="row tab-pane fade">
        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
            <h3>Provider Options</h3>
            <p>Configure individual provider settings here.</p>
            <p>Check with provider's website on how to obtain an API key if needed.</p>
        </div>

        <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Configure provider:</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="input-group input200">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-search"></span>
                        </div>
                        <select id="editAProvider" class="form-control" title="Choose a search provider">
                            % for providerID, providerObj in sickrage.srCore.providersDict.enabled().items():
                                <option value="${providerID}">${providerObj.name}</option>
                            % endfor
                        </select>
                    </div>
                </div>
            </div>


            <!-- start div for editing providers //-->
            % for providerID, providerObj in sickrage.srCore.providersDict.newznab().items():
                <div class="providerDiv" id="${providerID}Div">
                    % if not providerObj.default:
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">URL:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-globe"></span>
                                    </div>
                                    <input id="${providerID}_url"
                                           value="${providerObj.urls['base_url']}"
                                           title="Provider URL"
                                           class="form-control"
                                           autocapitalize="off" disabled/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if providerObj.private:
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">API key:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-cloud"></span>
                                    </div>
                                    <input id="${providerID}_key"
                                           name="${providerID}_key"
                                           value="${providerObj.key}"
                                           newznab_name="${providerID}_key"
                                           class="newznab_key form-control"
                                           title="Provider API key"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'enable_daily'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable daily searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_daily"
                                       id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                <label for="${providerID}_enable_daily">
                                    <p>enable provider to perform daily searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'enable_backlog'):
                        <div class="field-pair${(' hidden', '')[providerObj.supports_backlog]}">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable backlog searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_backlog"
                                       id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                <label for="${providerID}_enable_backlog">
                                    <p>enable provider to perform backlog searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_fallback'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Search mode fallback</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_search_fallback"
                                       id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                <label for="${providerID}_search_fallback">
                                    <p>
                                        when searching for a complete season depending on search mode you may
                                        return no results, this helps by restarting the search using the
                                        opposite search mode.
                                    </p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_mode'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Season search mode</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_sponly"
                                               value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                        <label for="${providerID}_search_mode_sponly">season packs only.</label>
                                    </div>
                                </div>
                                <br/>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_eponly"
                                               value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>
                                        <label for="${providerID}_search_mode_eponly">episodes only.</label>
                                    </div>
                                </div>
                                <p>
                                    when searching for complete seasons you can choose to have it look
                                    for season packs only, or choose to have it build a complete season
                                    from just single episodes.
                                </p>
                            </div>
                        </div>
                    % endif
                </div>
            % endfor

            % for providerID, providerObj in sickrage.srCore.providersDict.nzb().items():
                <div class="providerDiv" id="${providerID}Div">
                    % if hasattr(providerObj, 'username'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Username:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="${providerID}_username"
                                           value="${providerObj.username}"
                                           title="Provider username"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'api_key'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">API key:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-cloud"></span>
                                    </div>
                                    <input name="${providerID}_api_key"
                                           value="${providerObj.api_key}"
                                           title="Provider API key"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif


                    % if hasattr(providerObj, 'enable_daily'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable daily searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_daily"
                                       id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                <label for="${providerID}_enable_daily">
                                    <p>enable provider to perform daily searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'enable_backlog'):
                        <div class="field-pair${(' hidden', '')[providerObj.supports_backlog]}">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable backlog searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_backlog"
                                       id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                <label for="${providerID}_enable_backlog">
                                    <p>enable provider to perform backlog searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_fallback'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Search mode fallback</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_search_fallback"
                                       id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                <label for="${providerID}_search_fallback">
                                    <p>
                                        when searching for a complete season depending on search mode you may return no
                                        results, this helps by restarting the search using the opposite
                                        search mode.
                                    </p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_mode'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Season search mode</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_eponly"
                                               value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>
                                        <label for="${providerID}_search_mode_eponly">episodes only.</label>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_sponly"
                                               value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                        <label for="${providerID}_search_mode_sponly">season packs only.</label>
                                    </div>
                                </div>

                                <p>
                                    when searching for complete seasons you can choose to have it look for season
                                    packs only, or choose to have it build a complete season from just single
                                    episodes.
                                </p>
                            </div>
                        </div>
                    % endif
                </div>
            % endfor

            % for providerID, providerObj in sickrage.srCore.providersDict.all_torrent().items():
                <div class="providerDiv" id="${providerID}Div">
                    % if hasattr(providerObj, 'api_key'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Api key:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-cloud"></span>
                                    </div>
                                    <input name="${providerID}_api_key"
                                           id="${providerID}_api_key"
                                           value="${providerObj.api_key}"
                                           title="Provider API key"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'digest'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Digest:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input name="${providerID}_digest" id="${providerID}_digest"
                                           value="${providerObj.digest}"
                                           title="Provider digest"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'hash'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Hash:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="fa fa-hashtag"></span>
                                    </div>
                                    <input name="${providerID}_hash" id="${providerID}_hash"
                                           value="${providerObj.hash}"
                                           title="Provider hash"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'username'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Username:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="${providerID}_username"
                                           id="${providerID}_username"
                                           value="${providerObj.username}"
                                           title="Provider username"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'password'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Password:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="${providerID}_password"
                                           id="${providerID}_password" value="${providerObj.password}"
                                           title="Provider password"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'passkey'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Passkey:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input name="${providerID}_passkey"
                                           id="${providerID}_passkey"
                                           value="${providerObj.passkey}"
                                           title="Provider PassKey"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if getattr(providerObj, 'enable_cookies', False):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Cookies:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-certificate"></span>
                                    </div>
                                    <input name="${providerID}_cookies"
                                           id="${providerID}_cookies"
                                           value="${providerObj.cookies}"
                                           placeholder="ex. uid=xx;pass=yy"
                                           class="form-control"
                                           autocapitalize="off" autocomplete="no"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'pin'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Pin:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="${providerID}_pin"
                                           id="${providerID}_pin"
                                           value="${providerObj.pin}"
                                           title="Provider PIN#"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'ratio'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Seed ratio:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="fa fa-percent"></span>
                                    </div>
                                    <input type="number" step="0.1" name="${providerID}_ratio"
                                           id="${providerID}_ratio"
                                           value="${providerObj.ratio}"
                                           title="stop transfer when ratio is reached (-1 SickRage default to seed forever, or leave blank for downloader default)"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'minseed'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Minimum seeders:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="fa fa-hashtag"></span>
                                    </div>
                                    <input type="number" name="${providerID}_minseed"
                                           id="${providerID}_minseed"
                                           value="${providerObj.minseed}"
                                           title="Minimum allowed seeders"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'minleech'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Minimum leechers:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="fa fa-hashtag"></span>
                                    </div>
                                    <input type="number" name="${providerID}_minleech"
                                           id="${providerID}_minleech"
                                           value="${providerObj.minleech}"
                                           title="Minimum allowed leechers"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'confirmed'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Confirmed download</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_confirmed"
                                       id="${providerID}_confirmed" ${('', 'checked')[bool(providerObj.confirmed)]}/>
                                <label for="${providerID}_confirmed">
                                    <p>only download torrents from trusted or verified uploaders ?</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'ranked'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Ranked torrents</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_ranked"
                                       id="${providerID}_ranked" ${('', 'checked')[bool(providerObj.ranked)]} />
                                <label for="${providerID}_ranked">
                                    <p>only download ranked torrents (internal releases)</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'engrelease'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">English torrents</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_engrelease"
                                       id="${providerID}_engrelease" ${('', 'checked')[bool(providerObj.engrelease)]} />
                                <label for="${providerID}_engrelease">
                                    <p>only download english torrents ,or torrents containing english subtitles</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'onlyspasearch'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">For Spanish torrents</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_onlyspasearch"
                                       id="${providerID}_onlyspasearch" ${('', 'checked')[bool(providerObj.onlyspasearch)]} />
                                <label for="${providerID}_onlyspasearch">
                                    <p>ONLY search on this provider if show info is defined as "Spanish"
                                        (avoid provider's use for VOS shows)</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'sorting'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Sort results by</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-sort-by-order"></span>
                                    </div>
                                    <select name="${providerID}_sorting" id="${providerID}_sorting"
                                            title="Sort search results"
                                            class="form-control">
                                        % for curAction in ('last', 'seeders', 'leechers'):
                                            <option value="${curAction}" ${('', 'selected="selected"')[curAction == providerObj.sorting]}>${curAction}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'freeleech'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Freeleech</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_freeleech"
                                       id="${providerID}_freeleech" ${('', 'checked')[bool(providerObj.freeleech)]}/>
                                <label for="${providerID}_freeleech">
                                    <p>only download <b>[FreeLeech]</b> torrents.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'enable_daily'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable daily searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_daily"
                                       id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                <label for="${providerID}_enable_daily">
                                    <p>enable provider to perform daily searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'reject_m2ts'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Reject Blu-ray M2TS releases</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_reject_m2ts"
                                       id="${providerID}_reject_m2ts" ${('', 'checked')[bool(providerObj.reject_m2ts)]}/>
                                <label for="${providerID}_reject_m2ts">
                                    <p>enable to ignore Blu-ray MPEG-2 Transport Stream container releases</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'enable_backlog'):
                        <div class="row field-pair ${(' hidden', '')[providerObj.supports_backlog]}">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Enable backlog searches</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_enable_backlog"
                                       id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                <label for="${providerID}_enable_backlog">
                                    <p>enable provider to perform backlog searches.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_fallback'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Search mode fallback</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_search_fallback"
                                       id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                <label for="${providerID}_search_fallback">
                                    <p>when searching for a complete season depending on search mode you may return no
                                        results, this helps by restarting the search using the opposite
                                        search mode.</p>
                                </label>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'search_mode'):
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Season search mode</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_sponly"
                                               value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                        <label for="${providerID}_search_mode_sponly">season packs only.</label>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="radio" name="${providerID}_search_mode"
                                               id="${providerID}_search_mode_eponly"
                                               value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>
                                        <label for="${providerID}_search_mode_eponly">episodes only.</label>
                                    </div>
                                </div>

                                <p>
                                    when searching for complete seasons you can choose to have it look for season
                                    packs only, or choose to have it build a complete season from just single
                                    episodes.
                                </p>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'cat') and providerID == 'tntvillage':
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Category:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input200">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-list"></span>
                                    </div>
                                    <select name="${providerID}_cat" id="${providerID}_cat"
                                            title="Provider category"
                                            class="form-control">
                                        % for i in providerObj.category_dict.keys():
                                            <option value="${providerObj.category_dict[i]}" ${('', 'selected="selected"')[providerObj.category_dict[i] == providerObj.cat]}>${i}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>
                    % endif

                    % if hasattr(providerObj, 'subtitle') and providerID == 'tntvillage':
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Subtitled</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="${providerID}_subtitle"
                                       id="${providerID}_subtitle" ${('', 'checked')[bool(providerObj.subtitle)]}/>
                                <label for="${providerID}_subtitle">
                                    <p>select torrent with Italian subtitle</p>
                                </label>
                            </div>
                        </div>
                    % endif
                </div>
            % endfor
            <!-- end div for editing providers -->
            <div class="row">
                <div class="col-md-12">
                    <input type="submit" class="btn config_submitter" value="Save Changes"/>
                </div>
            </div>
        </fieldset>
    </div><!-- /tab-pane2 //-->

    % if sickrage.srCore.srConfig.USE_NZBS:
        <div id="core-tab-pane3" class="row tab-pane fade">

            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Configure Custom<br>Newznab Providers</h3>
                <p>Add and setup or remove custom Newznab providers.</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Select provider:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input200">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-search"></span>
                            </div>
                            <select id="editANewznabProvider" class="form-control" title="Choose provider">
                                <option value="addNewznab">-- add new provider --</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="newznabProviderDiv" id="addNewznab">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Provider name:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="fa fa-id-card"></span>
                                </div>
                                <input id="newznab_name" class="form-control" title="Provider name"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Site URL:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input id="newznab_url" class="form-control" title="Provider URL"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">API key:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input id="newznab_key" class="form-control" title="Provider API key"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>

                    <div class="row field-pair" id="newznabcapdiv">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Newznab search categories:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <select id="newznab_cap" multiple="multiple" title="Newznab caps"
                                            style="min-width:10em;"></select>
                                    <select id="newznab_cat" multiple="multiple" title="Newznab categories"
                                            style="min-width:10em;"></select>
                                    <p>
                                        (select your Newznab categories on the left, and click the "update categories"
                                        button to
                                        use them for searching.) <b>don't forget to to save the form!</b>
                                    </p>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn newznab_cat_update"
                                           type="button"
                                           id="newznab_cat_update"
                                           value="Update Categories"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="newznab_add_div">
                        <div class="row">
                            <div class="col-md-12">
                                <input class="btn newznab_save" type="button" id="newznab_add"
                                       value="Add"/>
                            </div>
                        </div>
                    </div>
                    <div id="newznab_update_div" style="display: none;">
                        <div class="row">
                            <div class="col-md-12">
                                <input class="btn btn-danger newznab_delete" type="button"
                                       id="newznab_delete" value="Delete"/>
                            </div>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div><!-- /tab-pane3 //-->
    % endif

    % if sickrage.srCore.srConfig.USE_TORRENTS:

        <div id="core-tab-pane4" class="row tab-pane fade">

            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Configure Custom Torrent Providers</h3>
                <p>Add and setup or remove custom RSS providers.</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Select provider:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input200">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-search"></span>
                            </div>
                            <select id="editATorrentRssProvider" class="form-control" title="Choose provider">
                                <option value="addTorrentRss">-- add new provider --</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="torrentRssProviderDiv" id="addTorrentRss">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Provider name:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="fa fa-id-card"></span>
                                </div>
                                <input id="torrentrss_name"
                                       title="Provider name"
                                       class="form-control"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">RSS URL:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input id="torrentrss_url" title="Provider URL"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Cookies:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-certificate"></span>
                                </div>
                                <input id="torrentrss_cookies" placeholder="ex. uid=xx;pass=yy"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Search element:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input200">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-search"></span>
                                </div>
                                <input id="torrentrss_titleTAG" placeholder="ex. title"
                                       class="form-control" value="title"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div id="torrentrss_add_div">
                        <div class="row">
                            <div class="col-md-12">
                                <input type="button" class="btn torrentrss_save" id="torrentrss_add"
                                       value="Add"/>
                            </div>
                        </div>
                    </div>
                    <div id="torrentrss_update_div" style="display: none;">
                        <div class="row">
                            <div class="col-md-12">
                                <input type="button" class="btn btn-danger torrentrss_delete"
                                       id="torrentrss_delete" value="Delete"/>
                            </div>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div><!-- /tab-pane4 //-->
    % endif
    <input type="hidden" name="provider_strings" id="provider_strings"/>
</%block>
