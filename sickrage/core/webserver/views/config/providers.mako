<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveProviders' %></%def>
<%!
    import json
    import sickrage
    from sickrage.search_providers import SearchProviderType
    from sickrage.search_providers.torrent import thepiratebay
    from sickrage.core.helpers import anon_url, validate_url
%>

<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#provider-priorities">${_('Provider Priorities')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#provider-options">${_('Provider Options')}</a></li>
    % if sickrage.app.config.general.use_nzbs:
        <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                     href="#custom-newnab-providers">${_('Custom Newznab Providers')}</a></li>
    % endif
    % if sickrage.app.config.general.use_torrents:
        <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                     href="#custom-torrent-providers">${_('Custom Torrent Providers')}</a></li>
    % endif
</%block>

<%block name="metas">
    <%
        newznab_providers = ''
        torrentrss_providers = ''

        if sickrage.app.config.general.use_nzbs:
            for providerID, providerObj in sickrage.app.search_providers.newznab().items():
                if providerObj.default:
                    continue

                newznab_providers += '{}!!!'.format(
                        '|'.join([providerID,
                        providerObj.name,
                        providerObj.urls["base_url"],
                        str(providerObj.key),
                        providerObj.catIDs,
                        ("false", "true")[bool(providerObj.default)],
                        ("false", "true")[bool(sickrage.app.config.general.use_nzbs)]]))

        if sickrage.app.config.general.use_torrents:
            for providerID, providerObj in sickrage.app.search_providers.torrentrss().items():
                if providerObj.default:
                    continue

                torrentrss_providers += '{}!!!'.format(
                    '|'.join([providerID,
                              providerObj.name,
                              providerObj.urls["base_url"],
                              providerObj.cookies,
                              providerObj.titleTAG,
                              ("false", "true")[bool(providerObj.default)],
                              ("false", "true")[bool(sickrage.app.config.general.use_torrents)]]))
    %>
    <meta data-var="NEWZNAB_PROVIDERS" data-content="${newznab_providers}">
    <meta data-var="TORRENTRSS_PROVIDERS" data-content="${torrentrss_providers}">
</%block>

<%block name="pages">
    <div id="provider-priorities" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Provider Priorities')}</h3>
                <small class="form-text text-muted">
                    ${_('Check off and drag the providers into the order you want them to be used.')}<br/>
                    ${_('At least one provider is required but two are recommended.')}
                </small>

                % if not sickrage.app.config.general.use_nzbs or not sickrage.app.config.general.use_torrents:
                    <small class="form-text text-muted">
                        ${_('NZB/Torrent providers can be toggled in')}
                        <b><a href="${srWebRoot}/config/search">${_('Search Clients')}</a></b>
                    </small>
                % endif

                <small class="form-text text-muted">
                    <i class="text-warning fas fa-chevron-circle-left"></i>
                    ${_('Provider does not support backlog searches at this time.')}<br/>
                    <i class="text-danger fas fa-exclamation-circle"></i>
                    ${_('Provider is <b>NOT WORKING</b>.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="list-group w-50" id="provider_order_list">
                    % for providerID, providerObj in sickrage.app.search_providers.sort().items():
                        % if (providerObj.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB] and sickrage.app.config.general.use_nzbs) or (providerObj.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS] and sickrage.app.config.general.use_torrents):
                        <% provider_url = providerObj.urls.get('base_url', '') %>
                        % if providerObj.custom_settings.get('custom_url', None) and validate_url(providerObj.custom_settings['custom_url']):
                            <% provider_url = providerObj.custom_settings['custom_url'] %>
                        % endif
                            <div class="list-group-item list-group-item-action ${('list-group-item-dark', 'list-group-item-secondary')[bool(providerObj.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS])]} rounded mb-1 p-2"
                                 id="${providerID}">
                                <div class="align-middle">
                                    <label class="form-check-label" for="enable_${providerID}">
                                        <input type="checkbox" id="enable_${providerID}"
                                               class="provider_enabler text-left" ${('', 'checked')[bool(providerObj.is_enabled)]}/>
                                        <a href="${anon_url(provider_url)}" class="text-right" rel="noreferrer"
                                           onclick="window.open(this.href, '_blank'); return false;">
                                            % if providerObj.provider_type in [SearchProviderType.NZB, SearchProviderType.TORRENT]:
                                                <i class="sickrage-search-providers sickrage-search-providers-${providerObj.id}"></i>
                                            % else:
                                                <i class="sickrage-search-providers sickrage-search-providers-${providerObj.provider_type.value}"></i>
                                            % endif
                                        </a>
                                        <span class="font-weight-bold">${providerObj.name}</span>
                                    </label>
                                    <span class="float-right d-inline-block">
                                        ${('<i class="text-warning fas fa-chevron-circle-left"></i>', '')[bool(providerObj.supports_backlog)]}
                                        ${('<i class="text-danger fas fa-exclamation-circle"></i>', '')[bool(providerObj.is_alive)]}
                                        <i class="fas ${('fa-unlock text-success','fa-lock text-danger')[bool(providerObj.private)]}"></i>
                                    </span>
                                </div>
                            </div>
                        % endif
                    % endfor
                </div>
                <input type="hidden" name="provider_order" id="provider_order"
                       value="${"!!!".join(["{}:{}".format(providerID, int(providerObj.is_enabled)) for providerID, providerObj in sickrage.app.search_providers.all().items()])}"/>
                <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="provider-options" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Provider Options')}</h3>
                <small class="form-text text-muted">
                    ${_('Configure individual provider settings here.')}<br/>
                    ${_('Check with provider\'s website on how to obtain an API key if needed.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Configure provider:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-search"></span></span>
                            </div>
                            <select id="editAProvider" class="form-control" title="Choose a search provider">
                                % for providerID, providerObj in sickrage.app.search_providers.enabled().items():
                                    <option value="${providerID}">${providerObj.name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>


                <!-- start div for editing providers //-->
                % for providerID, providerObj in sickrage.app.search_providers.newznab().items():
                    <div class="providerDiv" id="${providerID}Div">
                        % if not providerObj.default:
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('URL:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
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
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('API key:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-cloud"></span></span>
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
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable daily searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_daily">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_daily"
                                               id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                        ${_('enable provider to perform daily searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'enable_backlog'):
                            <div class="row field-pair${(' d-none', '')[providerObj.supports_backlog]}">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable backlog searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_backlog">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_backlog"
                                               id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                        ${_('enable provider to perform backlog searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_fallback'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Search mode fallback')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label class="form-check-label">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_search_fallback"
                                               id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                        ${_('when searching for a complete season depending on search mode you may')}
                                        <br/>
                                        ${_('return no results, this helps by restarting the search using the opposite')}
                                        <br/>
                                        ${_('search mode.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_mode'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Season search mode')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="form-row">
                                        <div class="col-md-12">
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_sponly"
                                                       value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                                ${_('season packs only.')}
                                            </label>
                                            <br/>
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_eponly"
                                                       value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>

                                                ${_('episodes only.')}
                                            </label>
                                            <p class="text-info">
                                                ${_('when searching for complete seasons you can choose to have it look for '
                                                'season packs only, or choose to have it build a complete season from just '
                                                'single episodes.')}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        % endif
                    </div>
                % endfor

                % for providerID, providerObj in sickrage.app.search_providers.nzb().items():
                    <div class="providerDiv" id="${providerID}Div">
                        % if providerObj.custom_settings.get('username', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Username:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-user"></span></span>
                                        </div>
                                        <input name="${providerID}_username"
                                               value="${providerObj.custom_settings['username']}"
                                               title="Provider username"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('api_key', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('API key:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                        </div>
                                        <input name="${providerID}_api_key"
                                               value="${providerObj.custom_settings['api_key']}"
                                               title="Provider API key"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif


                        % if hasattr(providerObj, 'enable_daily'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable daily searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_daily">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_daily"
                                               id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                        ${_('enable provider to perform daily searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'enable_backlog'):
                            <div class="field-pair${(' d-none', '')[providerObj.supports_backlog]}">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable backlog searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_backlog">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_backlog"
                                               id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                        ${_('enable provider to perform backlog searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_fallback'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Search mode fallback')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label class="form-check-label">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_search_fallback"
                                               id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                        ${_('when searching for a complete season depending on search mode you may '
                                        'return no results, this helps by restarting the search using the opposite '
                                        'search mode.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_mode'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Season search mode')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="form-row">
                                        <div class="col-md-12">
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_eponly"
                                                       value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>
                                                ${_('episodes only.')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row">
                                        <div class="col-md-12">
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_sponly"
                                                       value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                                ${_('season packs only.')}
                                            </label>
                                        </div>
                                    </div>

                                    <p class="text-info">
                                        ${_('when searching for complete seasons you can choose to have it look for '
                                        'season packs only, or choose to have it build a complete season from just '
                                        'single episodes.')}
                                    </p>
                                </div>
                            </div>
                        % endif
                    </div>
                % endfor

                % for providerID, providerObj in sickrage.app.search_providers.all_torrent().items():
                    <div class="providerDiv" id="${providerID}Div">
                        % if providerObj.custom_settings.get('custom_url', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Custom URL:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                        </div>
                                        <input name="${providerID}_custom_url"
                                               id="${providerID}_custom_url"
                                               value="${providerObj.custom_settings['custom_url']}"
                                               title="${_('Provider custom url')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('api_key', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Api key:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                        </div>
                                        <input name="${providerID}_api_key"
                                               id="${providerID}_api_key"
                                               value="${providerObj.custom_settings['api_key']}"
                                               title="${_('Provider API key')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('digest', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Digest:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                        </div>
                                        <input name="${providerID}_digest" id="${providerID}_digest"
                                               value="${providerObj.custom_settings['digest']}"
                                               title="${_('Provider digest')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('hash', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Hash:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-hashtag"></span>
                                            </span>
                                        </div>
                                        <input name="${providerID}_hash" id="${providerID}_hash"
                                               value="${providerObj.custom_settings['hash']}"
                                               title="${_('Provider hash')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('username', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Username:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-user"></span></span>
                                        </div>
                                        <input name="${providerID}_username"
                                               id="${providerID}_username"
                                               value="${providerObj.custom_settings['username']}"
                                               title="${_('Provider username')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('password', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Password:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                        </div>
                                        <input type="password" name="${providerID}_password"
                                               id="${providerID}_password"
                                               value="${providerObj.custom_settings['password']}"
                                               title="${_('Provider password')}"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('passkey', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Passkey:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                        </div>
                                        <input name="${providerID}_passkey"
                                               id="${providerID}_passkey"
                                               value="${providerObj.custom_settings['passkey']}"
                                               title="${_('Provider PassKey')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if getattr(providerObj, 'enable_cookies', False):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Cookies:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span
                                                    class="fas fa-certificate"></span></span>
                                        </div>
                                        <input name="${providerID}_cookies"
                                               id="${providerID}_cookies"
                                               value="${providerObj.cookies}"
                                               class="form-control"
                                               autocapitalize="off" autocomplete="no"/>
                                    </div>
                                    % if hasattr(providerObj, 'required_cookies'):
                                        <label for="${providerID}_cookies">
                                            <p>
                                                ex. ${'{}=xx'.format('=xx;'.join(providerObj.required_cookies))}<br/>
                                                ${_('this provider requires the following cookies: ')}${', '.join(providerObj.required_cookies)}
                                            </p>
                                        </label>
                                    % endif
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('pin', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Pin:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                        </div>
                                        <input type="password" name="${providerID}_pin"
                                               id="${providerID}_pin"
                                               value="${providerObj.custom_settings['pin']}"
                                               title="${_('Provider PIN#')}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'ratio'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Seed ratio:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-percent"></span>
                                            </span>
                                        </div>
                                        <input type="number" step="0.1" name="${providerID}_ratio"
                                               id="${providerID}_ratio"
                                               value="${providerObj.ratio}"
                                               class="form-control"
                                               title="${_('stop transfer when ratio is reached (-1 SickRage default to seed forever, or leave blank for downloader default)')}"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('minseed', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Minimum seeders:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-hashtag"></span>
                                            </span>
                                        </div>
                                        <input type="number" name="${providerID}_minseed"
                                               id="${providerID}_minseed"
                                               value="${providerObj.custom_settings['minseed']}"
                                               title="${_('Minimum allowed seeders')}"
                                               class="form-control"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('minleech', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Minimum leechers:')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-hashtag"></span>
                                            </span>
                                        </div>
                                        <input type="number" name="${providerID}_minleech"
                                               id="${providerID}_minleech"
                                               value="${providerObj.custom_settings['minleech']}"
                                               title="${_('Minimum allowed leechers')}"
                                               class="form-control"/>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('confirmed', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Confirmed download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_confirmed">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_confirmed"
                                               id="${providerID}_confirmed" ${('', 'checked')[bool(providerObj.custom_settings['confirmed'])]}/>
                                        ${_('only download torrents from trusted or verified uploaders?')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('ranked', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Ranked torrents')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_ranked">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_ranked"
                                               id="${providerID}_ranked" ${('', 'checked')[bool(providerObj.custom_settings['ranked'])]} />
                                        ${_('only download ranked torrents (internal releases)')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('engrelease', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('English torrents')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_engrelease">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_engrelease"
                                               id="${providerID}_engrelease" ${('', 'checked')[bool(providerObj.custom_settings['engrelease'])]} />
                                        ${_('only download english torrents ,or torrents containing english subtitles')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('onlyspasearch', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('For Spanish torrents')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_onlyspasearch">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_onlyspasearch"
                                               id="${providerID}_onlyspasearch" ${('', 'checked')[bool(providerObj.custom_settings['onlyspasearch'])]} />
                                        <p>
                                            ${_('ONLY search on this provider if show info is defined as "Spanish" '
                                            '(avoid provider\'s use for VOS shows)')}
                                        </p>
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('sorting', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Sort results by')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span
                                                    class="fas fa-sort-by-order"></span></span>
                                        </div>
                                        <select name="${providerID}_sorting" id="${providerID}_sorting"
                                                title="${_('Sort search results')}"
                                                class="form-control">
                                            % for curAction in ('last', 'seeders', 'leechers'):
                                                <option value="${curAction}" ${('', 'selected')[curAction == providerObj.custom_settings['sorting']]}>${curAction}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('freeleech', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Freeleech')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_freeleech">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_freeleech"
                                               id="${providerID}_freeleech" ${('', 'checked')[bool(providerObj.custom_settings['freeleech'])]}/>
                                        ${_('only download')} <b>[${_('FreeLeech')}]</b> ${_('torrents.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'enable_daily'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable daily searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_daily">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_daily"
                                               id="${providerID}_enable_daily" ${('', 'checked')[bool(providerObj.enable_daily)]}/>
                                        ${_('enable provider to perform daily searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if providerObj.custom_settings.get('reject_m2ts', None):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Reject Blu-ray M2TS releases')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_reject_m2ts">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_reject_m2ts"
                                               id="${providerID}_reject_m2ts" ${('', 'checked')[bool(providerObj.custom_settings['reject_m2ts'])]}/>
                                        ${_('enable to ignore Blu-ray MPEG-2 Transport Stream container releases')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'enable_backlog'):
                            <div class="form-row form-group ${(' d-none', '')[providerObj.supports_backlog]}">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Enable backlog searches')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_enable_backlog">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_enable_backlog"
                                               id="${providerID}_enable_backlog" ${('', 'checked')[bool(providerObj.enable_backlog and providerObj.supports_backlog)]}/>
                                        ${_('enable provider to perform backlog searches.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_fallback'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Search mode fallback')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label class="form-check-label">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_search_fallback"
                                               id="${providerID}_search_fallback" ${('', 'checked')[bool(providerObj.search_fallback)]}/>
                                        ${_('when searching for a complete season depending on search mode you may '
                                        'return no results, this helps by restarting the search using the opposite '
                                        'search mode.')}
                                    </label>
                                </div>
                            </div>
                        % endif

                        % if hasattr(providerObj, 'search_mode'):
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Season search mode')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <div class="form-row">
                                        <div class="col-md-12">
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_sponly"
                                                       value="sponly" ${('', 'checked')[providerObj.search_mode=="sponly"]}/>
                                                ${_('season packs only.')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row">
                                        <div class="col-md-12">
                                            <label class="form-check-label">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_eponly"
                                                       value="eponly" ${('', 'checked')[providerObj.search_mode=="eponly"]}/>

                                                ${_('episodes only.')}
                                            </label>
                                        </div>
                                    </div>

                                    <p class="text-info">
                                        ${_('when searching for complete seasons you can choose to have it look for '
                                        'season packs only, or choose to have it build a complete season from just '
                                        'single episodes.')}
                                    </p>
                                </div>
                            </div>
                        % endif

##                         % if hasattr(providerObj, 'cat') and providerID == 'tntvillage':
##                             <div class="form-row form-group">
##                                 <div class="col-lg-3 col-md-4 col-sm-5">
##                                     <label class="component-title">${_('Category:')}</label>
##                                 </div>
##                                 <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
##                                     <div class="input-group">
##                                         <div class="input-group-prepend">
##                                             <span class="input-group-text"><span class="fas fa-list"></span></span>
##                                         </div>
##                                         <select name="${providerID}_cat" id="${providerID}_cat"
##                                                 title="Provider category"
##                                                 class="form-control">
##                                             % for i in providerObj.category_dict.keys():
##                                                 <option value="${providerObj.category_dict[i]}" ${('', 'selected')[providerObj.category_dict[i] == providerObj.cat]}>${i}</option>
##                                             % endfor
##                                         </select>
##                                     </div>
##                                 </div>
##                             </div>
##                         % endif

                        % if providerObj.custom_settings.get('subtitle', None) and providerID == 'tntvillage':
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Subtitled')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="${providerID}_subtitle">
                                        <input type="checkbox" class="toggle color-primary is-material"
                                               name="${providerID}_subtitle"
                                               id="${providerID}_subtitle" ${('', 'checked')[bool(providerObj.custom_settings['subtitle'])]}/>
                                        ${_('select torrent with Italian subtitle')}
                                    </label>
                                </div>
                            </div>
                        % endif
                    </div>
                % endfor
                <!-- end div for editing providers -->
                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    % if sickrage.app.config.general.use_nzbs:
        <div id="custom-newnab-providers" class="tab-pane">
            <div class="form-row">
                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                    <h3>
                        ${_('Configure Custom')}<br/>
                        ${_('Newznab Providers')}
                    </h3>
                    <small class="form-text text-muted">
                        ${_('Add and setup or remove custom Newznab providers.')}
                    </small>
                </div>

                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Select provider:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-search"></span></span>
                                </div>
                                <select id="editANewznabProvider" class="form-control" title="Choose provider">
                                    <option value="addNewznab">-- ${_('add new provider')} --</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="newznabProviderDiv" id="addNewznab">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Provider name:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-id-card"></span>
                                        </span>
                                    </div>
                                    <input id="newznab_name" class="form-control" title="Provider name"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Site URL:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input id="newznab_url" class="form-control" title="Provider URL"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('API key:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                    </div>
                                    <input id="newznab_key" class="form-control" title="Provider API key"
                                           placeholder="if not required type 0" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="newznabcapdiv">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Newznab search categories:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="form-row">
                                    <div class="col-md-12">
                                        <select id="newznab_cap" multiple="multiple" title="Newznab caps"
                                                style="min-width:10em;"></select>
                                        <select id="newznab_cat" multiple="multiple" title="Newznab categories"
                                                style="min-width:10em;"></select>
                                        <p>
                                            ${_('(select your Newznab categories on the left, and click the "update '
                                            'categories" button to use them for searching.)')}<br/>
                                            <b>${_('Don\'t forget to save changes!')}</b>
                                        </p>
                                    </div>
                                </div>

                                <div class="form-row">
                                    <div class="col-md-12">
                                        <input class="btn newznab_cat_update"
                                               type="button"
                                               id="newznab_cat_update"
                                               value=${_('Update Categories')}/>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="newznab_add_div">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input class="btn newznab_save" type="button" id="newznab_add"
                                           value=${_('Add')}>
                                </div>
                            </div>
                        </div>
                        <div id="newznab_update_div" style="display: none;">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input class="btn btn-danger newznab_delete" type="button" id="newznab_delete"
                                           value=${_('Delete')}>
                                </div>
                            </div>
                        </div>
                    </div>
                </fieldset>
            </div>
        </div><!-- /tab-pane3 //-->
    % endif

    % if sickrage.app.config.general.use_torrents:
        <div id="custom-torrent-providers" class="tab-pane">
            <div class="form-row">
                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                    <h3>
                        ${_('Configure Custom')}<br/>
                        ${_('Torrent Providers')}
                    </h3>
                    <small class="form-text text-muted">
                        ${_('Add and setup or remove custom RSS providers.')}
                    </small>
                </div>

                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Select provider:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-search"></span></span>
                                </div>
                                <select id="editATorrentRssProvider" class="form-control" title="Choose provider">
                                    <option value="addTorrentRss">-- ${_('add new provider')} --</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="torrentRssProviderDiv" id="addTorrentRss">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Provider name:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-id-card"></span>
                                        </span>
                                    </div>
                                    <input id="torrentrss_name"
                                           title="Provider name"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('RSS URL:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input id="torrentrss_url" title="Provider URL"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Cookies:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-certificate"></span></span>
                                    </div>
                                    <input id="torrentrss_cookies" placeholder="${_('ex. uid=xx;pass=yy')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Search element:')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-search"></span></span>
                                    </div>
                                    <input id="torrentrss_titleTAG" placeholder="${_('ex. title')}"
                                           class="form-control" value="title"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div id="torrentrss_add_div">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="button" class="btn torrentrss_save" id="torrentrss_add"
                                           value="Add"/>
                                </div>
                            </div>
                        </div>
                        <div id="torrentrss_update_div" style="display: none;">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="button" class="btn btn-danger torrentrss_delete"
                                           id="torrentrss_delete" value="Delete"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </fieldset>
            </div>
        </div><!-- /tab-pane4 //-->
    % endif
    <input type="hidden" name="provider_strings" id="provider_strings"/>
</%block>
