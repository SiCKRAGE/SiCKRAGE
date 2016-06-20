<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.providers import NZBProvider, TorrentProvider, NewznabProvider, TorrentRssProvider
    from sickrage.providers.torrent import thepiratebay
    from sickrage.core.helpers import anon_url
%>
<%block name="content">


    <script type="text/javascript">
        $(document).ready(function () {
            % if sickrage.srCore.srConfig.USE_NZBS:
                % for providerID, providerObj in sickrage.srCore.providersDict.newznab().items():
                    SICKRAGE.config.providers.addNewznabProvider(
                            '${providerID}',
                            '${providerObj.name}',
                            '${providerObj.urls["base_url"]}',
                            '${providerObj.key}',
                            '${providerObj.catIDs}',
                            '${int(providerObj.default)}',
                            '${("false", "true")[bool(sickrage.srCore.srConfig.USE_NZBS)]}');
                % endfor
            % endif

            % if sickrage.srCore.srConfig.USE_TORRENTS:
                % for providerID, providerObj in sickrage.srCore.providersDict.torrentrss().items():
                    SICKRAGE.config.providers.addTorrentRssProvider(
                            '${providerID}',
                            '${providerObj.name}',
                            '${providerObj.urls["base_url"]}',
                            '${providerObj.cookies}',
                            '${providerObj.titleTAG}',
                            '${("false", "true")[bool(sickrage.srCore.srConfig.USE_TORRENTS)]}');
                % endfor
            % endif
        });
    </script>

    <div id="config">
        <div id="ui-content">

            <form id="configForm" action="saveProviders" method="post">
                <div id="ui-components">
                    <ul>
                        <li><a href="#core-component-group1">Provider Priorities</a></li>
                        <li><a href="#core-component-group2">Provider Options</a></li>
                        % if sickrage.srCore.srConfig.USE_NZBS:
                            <li><a href="#core-component-group3">Configure Custom Newznab Providers</a></li>
                        % endif
                        % if sickrage.srCore.srConfig.USE_TORRENTS:
                            <li><a href="#core-component-group4">Configure Custom Torrent Providers</a></li>
                        % endif
                    </ul>

                    <div id="core-component-group1" class="component-group" style='min-height: 550px;'>

                        <div class="component-group-desc">
                            <h3>Provider Priorities</h3>
                            <p>Check off and drag the providers into the order you want them to be used.</p>
                            <p>At least one provider is required but two are recommended.</p>

                            % if not sickrage.srCore.srConfig.USE_NZBS or not sickrage.srCore.srConfig.USE_TORRENTS:
                                <blockquote style="margin: 20px 0;">NZB/Torrent providers can be toggled in <b><a
                                        href="/config/search">Search Clients</a></b></blockquote>
                            % else:
                                <br>
                            % endif

                            <div>
                                <p class="note">* Provider does not support backlog searches at this time.</p>
                                <p class="note">! Provider is <b>NOT WORKING</b>.</p>
                            </div>
                        </div>

                        <fieldset class="component-group-list">
                            <ul id="provider_order_list">
                                % for providerID, providerObj in sickrage.srCore.providersDict.sort().items():
                                    % if (providerObj.type in [NZBProvider.type, NewznabProvider.type] and sickrage.srCore.srConfig.USE_NZBS) or (providerObj.type in [TorrentProvider.type, TorrentRssProvider] and sickrage.srCore.srConfig.USE_TORRENTS):
                                        <li class="ui-state-default ${('nzb-provider', 'torrent-provider')[bool(providerObj.type in [TorrentProvider.type, TorrentRssProvider])]}"
                                            id="${providerID}">
                                            <input type="checkbox" id="enable_${providerID}"
                                                   class="provider_enabler" ${('', 'checked="checked"')[providerObj.isEnabled == True]}/>
                                            <a href="${anon_url(providerObj.urls['base_url'])}" class="imgLink"
                                               rel="noreferrer"
                                               onclick="window.open(this.href, '_blank'); return false;"><img
                                                    src="/images/providers/${providerObj.imageName}"
                                                    alt="${providerObj.name}" title="${providerObj.name}" width="16"
                                                    height="16" style="vertical-align:middle;"/></a>
                                            <span style="vertical-align:middle;">${providerObj.name}</span>
                                            ${('*', '')[bool(providerObj.supportsBacklog)]}
                                            <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right"
                                                  style="vertical-align:middle;"></span>
                                            <span class="ui-icon ${('ui-icon-unlocked','ui-icon-locked')[bool(providerObj.private)]} pull-right"
                                                  style="vertical-align:middle;"></span>
                                        </li>
                                    % endif
                                % endfor
                            </ul>
                            <input type="hidden" name="provider_order" id="provider_order"
                                   value="${" ".join([providerID+':'+str(int(providerObj.isEnabled)) for providerID, providerObj in sickrage.srCore.providersDict.all().items()])}"/>
                            <br><input type="submit" class="btn config_submitter" value="Save Changes"/><br>
                        </fieldset>
                    </div><!-- /component-group1 //-->

                    <div id="core-component-group2" class="component-group">
                        <div class="component-group-desc">
                            <h3>Provider Options</h3>
                            <p>Configure individual provider settings here.</p>
                            <p>Check with provider's website on how to obtain an API key if needed.</p>
                        </div>

                        <fieldset class="component-group-list">
                            <div class="field-pair">
                                <label for="editAProvider" id="provider-list">
                                    <span class="component-title">Configure provider:</span>
                                    <span class="component-desc">
                                            <select id="editAProvider" class="form-control input-sm">
                                                % for providerID, providerObj in sickrage.srCore.providersDict.enabled().items():
                                                    <option value="${providerID}">${providerObj.name}</option>
                                                % endfor
                                            </select>
                                    </span>
                                </label>
                            </div>


                            <!-- start div for editing providers //-->
                            % for providerID, providerObj in sickrage.srCore.providersDict.newznab().items():
                                <div class="providerDiv" id="${providerID}">
                                    % if not providerObj.default:
                                        <div class="field-pair">
                                            <label for="${providerID}_url">
                                                <span class="component-title">URL:</span>
                                                <span class="component-desc">
                                                    <input type="text" id="${providerID}_url"
                                                           value="${providerObj.urls['base_url']}"
                                                           class="form-control input-sm input350"
                                                           autocapitalize="off" disabled/>
                                                </span>
                                            </label>
                                        </div>

                                        <div class="field-pair">
                                            <label for="${providerID}_hash">
                                                <span class="component-title">API key:</span>
                                                <span class="component-desc">
                                                    <input type="text" id="${providerID}_hash"
                                                           value="${providerObj.key}"
                                                           newznab_name="${providerID}_hash"
                                                           class="newznab_key form-control input-sm input350"
                                                           autocapitalize="off"/>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'enable_daily'):
                                        <div class="field-pair">
                                            <label for="${providerID}_enable_daily">
                                                <span class="component-title">Enable daily searches</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_enable_daily"
                                                       id="${providerID}_enable_daily" ${('', 'checked="checked"')[bool(providerObj.enable_daily)]}/>
                                                <p>enable provider to perform daily searches.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'enable_backlog'):
                                        <div class="field-pair${(' hidden', '')[providerObj.supportsBacklog]}">
                                            <label for="${providerID}_enable_backlog">
                                                <span class="component-title">Enable backlog searches</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_enable_backlog"
                                                       id="${providerID}_enable_backlog" ${('', 'checked="checked"')[bool(providerObj.enable_backlog and providerObj.supportsBacklog)]}/>
                                                <p>enable provider to perform backlog searches.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_fallback'):
                                        <div class="field-pair">
                                            <label for="${providerID}_search_fallback">
                                                <span class="component-title">Season search fallback</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_search_fallback"
                                                       id="${providerID}_search_fallback" ${('', 'checked="checked"')[bool(providerObj.search_fallback)]}/>
                                                <p>when searching for a complete season depending on search mode you may
                                                    return no results, this helps by restarting the search using the
                                                    opposite search mode.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_mode'):
                                        <div class="field-pair">
                                            <label>
                                                <span class="component-title">Season search mode</span>
                                            <span class="component-desc">
                                                <p>when searching for complete seasons you can choose to have it look
                                                    for season packs only, or choose to have it build a complete season
                                                    from just single episodes.</p>
                                            </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                            <span class="component-desc">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_sponly"
                                                       value="sponly" ${('', 'checked="checked"')[providerObj.search_mode=="sponly"]}/>season packs only.
                                            </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                            <span class="component-desc">
                                                <input type="radio" name="${providerID}_search_mode"
                                                       id="${providerID}_search_mode_eponly"
                                                       value="eponly" ${('', 'checked="checked"')[providerObj.search_mode=="eponly"]}/>episodes only.
                                            </span>
                                            </label>
                                        </div>
                                    % endif
                                </div>
                            % endfor

                            % for providerID, providerObj in sickrage.srCore.providersDict.nzb().items():
                                <div class="providerDiv" id="${providerID}Div">
                                    % if hasattr(providerObj, 'username'):
                                        <div class="field-pair">
                                            <label for="${providerID}_username">
                                                <span class="component-title">Username:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_username"
                                                       value="${providerObj.username}"
                                                       class="form-control input-sm input350" autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'api_key'):
                                        <div class="field-pair">
                                            <label for="${providerID}_api_key">
                                                <span class="component-title">API key:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_api_key"
                                                       value="${providerObj.api_key}"
                                                       class="form-control input-sm input350" autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif


                                    % if hasattr(providerObj, 'enable_daily'):
                                        <div class="field-pair">
                                            <label for="${providerID}_enable_daily">
                                                <span class="component-title">Enable daily searches</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_enable_daily"
                                                       id="${providerID}_enable_daily" ${('', 'checked="checked"')[bool(providerObj.enable_daily)]}/>
                                                <p>enable provider to perform daily searches.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'enable_backlog'):
                                        <div class="field-pair${(' hidden', '')[providerObj.supportsBacklog]}">
                                            <label for="${providerID}_enable_backlog">
                                                <span class="component-title">Enable backlog searches</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_enable_backlog"
                                                       id="${providerID}_enable_backlog" ${('', 'checked="checked"')[bool(providerObj.enable_backlog and providerObj.supportsBacklog)]}/>
                                                <p>enable provider to perform backlog searches.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_fallback'):
                                        <div class="field-pair">
                                            <label for="${providerID}_search_fallback">
                                                <span class="component-title">Season search fallback</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="${providerID}_search_fallback"
                                                       id="${providerID}_search_fallback" ${('', 'checked="checked"')[bool(providerObj.search_fallback)]}/>
                                                <p>when searching for a complete season depending on search mode you may
                                                    return no
                                                    results, this helps by restarting the search using the opposite
                                                    search mode.</p>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_mode'):
                                        <div class="field-pair">
                                            <label>
                                                <span class="component-title">Season search mode</span>
                                                <span class="component-desc">
                                                    <p>when searching for complete seasons you can choose to have it
                                                        look
                                                        for season
                                                        packs only, or choose to have it build a complete season from
                                                        just
                                                        single
                                                        episodes.</p>
                                                </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                                <span class="component-desc">
                                                    <input type="radio" name="${providerID}_search_mode"
                                                           id="${providerID}_search_mode_sponly"
                                                           value="sponly" ${('', 'checked="checked"')[providerObj.search_mode=="sponly"]}/>season packs only.
                                                </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                                <span class="component-desc">
                                                    <input type="radio" name="${providerID}_search_mode"
                                                           id="${providerID}_search_mode_eponly"
                                                           value="eponly" ${('', 'checked="checked"')[providerObj.search_mode=="eponly"]}/>episodes only.
                                                </span>
                                            </label>
                                        </div>
                                    % endif
                                </div>
                            % endfor

                            % for providerID, providerObj in sickrage.srCore.providersDict.all_torrent().items():
                                <div class="providerDiv" id="${providerID}Div">
                                    % if hasattr(providerObj, 'api_key'):
                                        <div class="field-pair">
                                            <label for="${providerID}_api_key">
                                                <span class="component-title">Api key:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_api_key"
                                                       id="${providerID}_api_key"
                                                       value="${providerObj.api_key}"
                                                       class="form-control input-sm input350"
                                                       autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'digest'):
                                        <div class="field-pair">
                                            <label for="${providerID}_digest">
                                                <span class="component-title">Digest:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_digest" id="${providerID}_digest"
                                                       value="${providerObj.digest}"
                                                       class="form-control input-sm input350"
                                                       autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'hash'):
                                        <div class="field-pair">
                                            <label for="${providerID}_hash">
                                                <span class="component-title">Hash:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_hash" id="${providerID}_hash"
                                                       value="${providerObj.hash}"
                                                       class="form-control input-sm input350"
                                                       autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'username'):
                                        <div class="field-pair">
                                            <label for="${providerID}_username">
                                                <span class="component-title">Username:</span>
                                            <span class="component-desc">
                                                <input type="text" name="${providerID}_username"
                                                       id="${providerID}_username"
                                                       value="${providerObj.username}"
                                                       class="form-control input-sm input350"
                                                       autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'password'):
                                        <div class="field-pair">
                                            <label for="${providerID}_password">
                                                <span class="component-title">Password:</span>
                                            <span class="component-desc">
                                                <input type="password" name="${providerID}_password"
                                                       id="${providerID}_password" value="${providerObj.password}"
                                                       class="form-control input-sm input350" autocapitalize="off"/>
                                            </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'passkey'):
                                        <div class="field-pair">
                                            <label for="${providerID}_passkey">
                                                <span class="component-title">Passkey:</span>
                                                <span class="component-desc">
                                                    <input type="text" name="${providerID}_passkey"
                                                           id="${providerID}_passkey"
                                                           value="${providerObj.passkey}"
                                                           class="form-control input-sm input350"
                                                           autocapitalize="off"/>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'pin'):
                                        <div class="field-pair">
                                            <label for="${providerID}_pin">
                                                <span class="component-title">Pin:</span>
                                                <span class="component-desc">
                                                    <input type="password" name="${providerID}_pin"
                                                           id="${providerID}_pin"
                                                           value="${providerObj.pin}"
                                                           class="form-control input-sm input100"
                                                           autocapitalize="off"/>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'ratio'):
                                        <div class="field-pair">
                                            <label for="${providerID}_ratio">
                                            <span class="component-title"
                                                  id="${providerID}_ratio_desc">Seed ratio:</span>
                                            <span class="component-desc">
                                                <input type="number" step="0.1" name="${providerID}_ratio"
                                                       id="${providerID}_ratio"
                                                       value="${providerObj.ratio}"
                                                       class="form-control input-sm input75"/>
                                            </span>
                                            </label>
                                            <label>
                                                <span class="component-title">&nbsp;</span>
                                                <span class="component-desc">
                                                    <p>stop transfer when ratio is reached<br>(-1 SickRage default to
                                                        seed forever, or
                                                        leave blank for downloader default)</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'minseed'):
                                        <div class="field-pair">
                                            <label for="${providerID}_minseed">
                                                <span class="component-title" id="${providerID}_minseed_desc">Minimum seeders:</span>
                                                <span class="component-desc">
                                                    <input type="number" name="${providerID}_minseed"
                                                           id="${providerID}_minseed"
                                                           value="${providerObj.minseed}"
                                                           class="form-control input-sm input75"/>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'minleech'):
                                        <div class="field-pair">
                                            <label for="${providerID}_minleech">
                                                <span class="component-title" id="${providerID}_minleech_desc">Minimum leechers:</span>
                                                <span class="component-desc">
                                                    <input type="number" name="${providerID}_minleech"
                                                           id="${providerID}_minleech"
                                                           value="${providerObj.minleech}"
                                                           class="form-control input-sm input75"/>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'confirmed'):
                                        <div class="field-pair">
                                            <label for="${providerID}_confirmed">
                                                <span class="component-title">Confirmed download</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_confirmed"
                                                           id="${providerID}_confirmed" ${('', 'checked="checked"')[bool(providerObj.confirmed)]}/>
                                                    <p>only download torrents from trusted or verified uploaders ?</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'ranked'):
                                        <div class="field-pair">
                                            <label for="${providerID}_ranked">
                                                <span class="component-title">Ranked torrents</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_ranked"
                                                           id="${providerID}_ranked" ${('', 'checked="checked"')[bool(providerObj.ranked)]} />
                                                    <p>only download ranked torrents (internal releases)</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'engrelease'):
                                        <div class="field-pair">
                                            <label for="${providerID}_engrelease">
                                                <span class="component-title">English torrents</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_engrelease"
                                                           id="${providerID}_engrelease" ${('', 'checked="checked"')[bool(providerObj.engrelease)]} />
                                                    <p>only download english torrents ,or torrents containing english
                                                        subtitles</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'onlyspasearch'):
                                        <div class="field-pair">
                                            <label for="${providerID}_onlyspasearch">
                                                <span class="component-title">For Spanish torrents</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_onlyspasearch"
                                                           id="${providerID}_onlyspasearch" ${('', 'checked="checked"')[bool(providerObj.onlyspasearch)]} />
                                                    <p>ONLY search on this provider if show info is defined as "Spanish"
                                                        (avoid
                                                        provider's use for VOS shows)</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'sorting'):
                                        <div class="field-pair">
                                            <label for="${providerID}_sorting">
                                                <span class="component-title">Sorting results by</span>
                                                <span class="component-desc">
                                                    <select name="${providerID}_sorting" id="${providerID}_sorting"
                                                            class="form-control input-sm">
                                                        % for curAction in ('last', 'seeders', 'leechers'):
                                                            <option value="${curAction}" ${('', 'selected="selected"')[curAction == providerObj.sorting]}>${curAction}</option>
                                                        % endfor
                                                    </select>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'freeleech'):
                                        <div class="field-pair">
                                            <label for="${providerID}_freeleech">
                                                <span class="component-title">Freeleech</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_freeleech"
                                                           id="${providerID}_freeleech" ${('', 'checked="checked"')[bool(providerObj.freeleech)]}/>
                                                    <p>only download <b>[FreeLeech]</b> torrents.</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'enable_daily'):
                                        <div class="field-pair">
                                            <label for="${providerID}_enable_daily">
                                                <span class="component-title">Enable daily searches</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_enable_daily"
                                                           id="${providerID}_enable_daily" ${('', 'checked="checked"')[bool(providerObj.enable_daily)]}/>
                                                    <p>enable provider to perform daily searches.</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'enable_backlog'):
                                        <div class="field-pair${(' hidden', '')[providerObj.supportsBacklog]}">
                                            <label for="${providerID}_enable_backlog">
                                                <span class="component-title">Enable backlog searches</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_enable_backlog"
                                                           id="${providerID}_enable_backlog" ${('', 'checked="checked"')[bool(providerObj.enable_backlog and providerObj.supportsBacklog)]}/>
                                                    <p>enable provider to perform backlog searches.</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_fallback'):
                                        <div class="field-pair">
                                            <label for="${providerID}_search_fallback">
                                                <span class="component-title">Season search fallback</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_search_fallback"
                                                           id="${providerID}_search_fallback" ${('', 'checked="checked"')[bool(providerObj.search_fallback)]}/>
                                                    <p>when searching for a complete season depending on search mode you
                                                        may return no
                                                        results, this helps by restarting the search using the opposite
                                                        search mode.</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'search_mode'):
                                        <div class="field-pair">
                                            <label>
                                                <span class="component-title">Season search mode</span>
                                                <span class="component-desc">
                                                    <p>when searching for complete seasons you can choose to have it
                                                        look for season
                                                        packs only, or choose to have it build a complete season from
                                                        just single
                                                        episodes.</p>
                                                </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                                <span class="component-desc">
                                                    <input type="radio" name="${providerID}_search_mode"
                                                           id="${providerID}_search_mode_sponly"
                                                           value="sponly" ${('', 'checked="checked"')[providerObj.search_mode=="sponly"]}/>season packs only.
                                                </span>
                                            </label>
                                            <label>
                                                <span class="component-title"></span>
                                                <span class="component-desc">
                                                    <input type="radio" name="${providerID}_search_mode"
                                                           id="${providerID}_search_mode_eponly"
                                                           value="eponly" ${('', 'checked="checked"')[providerObj.search_mode=="eponly"]}/>episodes only.
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'cat') and providerID == 'tntvillage':
                                        <div class="field-pair">
                                            <label for="${providerID}_cat">
                                                <span class="component-title">Category:</span>
                                                <span class="component-desc">
                                                    <select name="${providerID}_cat" id="${providerID}_cat"
                                                            class="form-control input-sm">
                                                        % for i in providerObj.category_dict.keys():
                                                            <option value="${providerObj.category_dict[i]}" ${('', 'selected="selected"')[providerObj.category_dict[i] == providerObj.cat]}>${i}</option>
                                                        % endfor
                                                    </select>
                                                </span>
                                            </label>
                                        </div>
                                    % endif

                                    % if hasattr(providerObj, 'subtitle') and providerID == 'tntvillage':
                                        <div class="field-pair">
                                            <label for="${providerID}_subtitle">
                                                <span class="component-title">Subtitled</span>
                                                <span class="component-desc">
                                                    <input type="checkbox" name="${providerID}_subtitle"
                                                           id="${providerID}_subtitle" ${('', 'checked="checked"')[bool(providerObj.subtitle)]}/>
                                                    <p>select torrent with Italian subtitle</p>
                                                </span>
                                            </label>
                                        </div>
                                    % endif
                                </div>
                            % endfor
                            <!-- end div for editing providers -->
                            <input type="submit" class="btn config_submitter" value="Save Changes"/><br>
                        </fieldset>
                    </div><!-- /component-group2 //-->

                    % if sickrage.srCore.srConfig.USE_NZBS:
                        <div id="core-component-group3" class="component-group">

                            <div class="component-group-desc">
                                <h3>Configure Custom<br>Newznab Providers</h3>
                                <p>Add and setup or remove custom Newznab providers.</p>
                            </div>

                            <fieldset class="component-group-list">
                                <div class="field-pair">
                                    <label for="newznab_string">
                                        <span class="component-title">Select provider:</span>
                                <span class="component-desc">
                                    <select id="editANewznabProvider" class="form-control input-sm">
                                        <option value="addNewznab">-- add new provider --</option>
                                    </select>
                                </span>
                                    </label>
                                </div>

                                <div class="newznabProviderDiv" id="addNewznab">
                                    <div class="field-pair">
                                        <label for="newznab_name">
                                            <span class="component-title">Provider name:</span>
                                            <input type="text" id="newznab_name"
                                                   class="form-control input-sm input200"/>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="newznab_url">
                                            <span class="component-title">Site URL:</span>
                                            <input type="text" id="newznab_url" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="newznab_key">
                                            <span class="component-title">API key:</span>
                                            <input type="text" id="newznab_key" class="form-control input-sm input350"
                                                   autocapitalize="off"/>
                                        </label>
                                        <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc">(if not required, type 0)</span>
                                        </label>
                                    </div>

                                    <div class="field-pair" id="newznabcapdiv">
                                        <label>
                                            <span class="component-title">Newznab search categories:</span>
                                            <select id="newznab_cap" multiple="multiple"
                                                    style="min-width:10em;"></select>
                                            <select id="newznab_cat" multiple="multiple"
                                                    style="min-width:10em;"></select>
                                        </label>
                                        <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc">(select your Newznab categories on the left, and click the "update categories" button to use them for searching.) <b>don't
                                                forget to to save the form!</b></span>
                                        </label>
                                        <label>
                                            <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><input class="btn" type="button" class="newznab_cat_update"
                                                                    id="newznab_cat_update" value="Update Categories"/>
                                    <span class="updating_categories"></span>
                                </span>
                                        </label>
                                    </div>

                                    <div id="newznab_add_div">
                                        <input class="btn" type="button" class="newznab_save" id="newznab_add"
                                               value="Add"/>
                                    </div>
                                    <div id="newznab_update_div" style="display: none;">
                                        <input class="btn btn-danger newznab_delete" type="button"
                                               class="newznab_delete" id="newznab_delete" value="Delete"/>
                                    </div>
                                </div>

                            </fieldset>
                        </div><!-- /component-group3 //-->
                    % endif

                    % if sickrage.srCore.srConfig.USE_TORRENTS:

                        <div id="core-component-group4" class="component-group">

                            <div class="component-group-desc">
                                <h3>Configure Custom Torrent Providers</h3>
                                <p>Add and setup or remove custom RSS providers.</p>
                            </div>

                            <fieldset class="component-group-list">
                                <div class="field-pair">
                                    <label for="torrentrss_string">
                                        <span class="component-title">Select provider:</span>
                            <span class="component-desc">
                                <select id="editATorrentRssProvider" class="form-control input-sm">
                                    <option value="addTorrentRss">-- add new provider --</option>
                                </select>
                            </span>
                                    </label>
                                </div>

                                <div class="torrentRssProviderDiv" id="addTorrentRss">
                                    <div class="field-pair">
                                        <label for="torrentrss_name">
                                            <span class="component-title">Provider name:</span>
                                            <input type="text" id="torrentrss_name"
                                                   class="form-control input-sm input200"/>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="torrentrss_url">
                                            <span class="component-title">RSS URL:</span>
                                            <input type="text" id="torrentrss_url"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="torrentrss_cookies">
                                            <span class="component-title">Cookies:</span>
                                            <input type="text" id="torrentrss_cookies"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                        </label>
                                        <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc">eg. uid=xx;pass=yy</span>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="torrentrss_titleTAG">
                                            <span class="component-title">Search element:</span>
                                            <input type="text" id="torrentrss_titleTAG"
                                                   class="form-control input-sm input200" value="title"
                                                   autocapitalize="off"/>
                                        </label>
                                        <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc">eg: title</span>
                                        </label>
                                    </div>
                                    <div id="torrentrss_add_div">
                                        <input type="button" class="btn torrentrss_save" id="torrentrss_add"
                                               value="Add"/>
                                    </div>
                                    <div id="torrentrss_update_div" style="display: none;">
                                        <input type="button" class="btn btn-danger torrentrss_delete"
                                               id="torrentrss_delete" value="Delete"/>
                                    </div>
                                </div>
                            </fieldset>
                        </div><!-- /component-group4 //-->
                    % endif

                    <input type="hidden" name="provider_strings" id="provider_strings"/>
                    <br><input type="submit" class="btn config_submitter_refresh" value="Save Changes"/><br>

                </div><!-- /ui-components //-->

            </form>
        </div>
    </div>
</%block>
