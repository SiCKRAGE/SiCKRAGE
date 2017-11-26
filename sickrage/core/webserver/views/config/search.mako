<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveSearch' %></%def>
<%!
    import sickrage
%>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">${_('Search Settings')}</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">${_('NZB Clients')}</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane3">${_('Torrent Clients')}</a></li>
</%block>
<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active clearfix">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>${_('Search Settings')}</h3>
                <p>${_('How to manage searching with')} <a href="${srWebRoot}/config/providers">${_('providers')}</a>.
                </p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Randomize Providers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="randomize_providers" id="randomize_providers"
                               class="enabler" ${('', 'checked')[bool(sickrage.app.config.randomize_providers)]}/>
                        <label for="randomize_providers">
                            <p>${_('randomize the provider search order')}</p>
                        </label>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Download propers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="download_propers" id="download_propers"
                               class="enabler" ${('', 'checked')[bool(sickrage.app.config.download_propers)]}/>
                        <label for="download_propers">
                            <p>${_('replace original download with "Proper" or "Repack" if nuked')}</p>
                        </label>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable provider RSS cache')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="enable_rss_cache" id="enable_rss_cache"
                               class="enabler" ${('', 'checked')[bool(sickrage.app.config.enable_rss_cache)]}/>
                        <label for="enable_rss_cache">
                            <p>${_('enables/disables provider RSS feed caching')}</p>
                        </label>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable provider RSS cache for valid shows only')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="enable_rss_cache_valid_shows" id="enable_rss_cache_valid_shows"
                               class="enabler" ${('', 'checked')[bool(sickrage.app.config.enable_rss_cache_valid_shows)]}/>
                        <label for="enable_rss_cache_valid_shows">
                            <p>${_('enables/disables caching of shows already added to SiCKRAGE, speeds up searches')}</p>
                        </label>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Convert provider torrent file links to magnetic links')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="torrent_file_to_magnet" id="torrent_file_to_magnet"
                               class="enabler" ${('', 'checked')[bool(sickrage.app.config.torrent_file_to_magnet)]}/>
                        <label for="torrent_file_to_magnet">
                            <p>${_('enables/disables converting of public torrent provider file links to magnetic links')}</p>
                        </label>
                    </div>
                </div>
                <div id="content_download_propers">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Check propers every:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-time"></span>
                                </div>
                                <select id="check_propers_interval" name="check_propers_interval"
                                        class="form-control" title="Interval to check for propers">
                                    <% check_propers_interval_text = {'daily': _("24 hours"), '4h': _("4 hours"), '90m': _("90 mins"), '45m': _("45 mins"), '15m': _("15 mins")} %>
                                    % for curInterval in ('daily', '4h', '90m', '45m', '15m'):
                                        <option value="${curInterval}" ${('', 'selected')[sickrage.app.config.proper_searcher_interval == curInterval]}>${check_propers_interval_text[curInterval]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Backlog search frequency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="backlog_frequency"
                                   id="backlog_frequency"
                                   value="${sickrage.app.config.backlog_searcher_freq}"
                                   placeholder="${_('time in minutes')}"
                                   title="minimum allowed time ${sickrage.app.config.min_backlog_searcher_freq} minutes"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Daily search frequency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="dailysearch_frequency"
                                   value="${sickrage.app.config.daily_searcher_freq}"
                                   placeholder="${_('time in minutes')}"
                                   title="minimum allowed time ${sickrage.app.config.min_daily_searcher_freq} minutes"
                                   class="form-control"/>
                            <div class="input-group-addon">
                                min
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Usenet retention')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="usenet_retention"
                                   value="${sickrage.app.config.usenet_retention}"
                                   title="age limit in days (ex. 500)"
                                   class="form-control"/>
                            <div class="input-group-addon">
                                days
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Ignore words')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-font"></span>
                            </div>
                            <input name="ignore_words"
                                   value="${sickrage.app.config.ignore_words}"
                                   placeholder="${_('ex. word1,word2,word3')}"
                                   title="Results with one or more word from this list will be ignored separate words with a comma"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Require words')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-font"></span>
                            </div>
                            <input name="require_words"
                                   value="${sickrage.app.config.require_words}"
                                   placeholder="${_('ex. word1,word2,word3')}"
                                   title="Results with no word from this list will be ignored separate words with a comma"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Ignore language names in subbed results')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-font"></span>
                            </div>
                            <input name="ignored_subs_list"
                                   value="${sickrage.app.config.ignored_subs_list}"
                                   placeholder="${_('ex. lang1,lang2,lang3')}"
                                   title="Ignore subbed releases based on language names, ex: dk will ignore words: dksub, dksubs, dksubbed, dksubed"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Allow high priority')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="allow_high_priority"
                               id="allow_high_priority" ${('', 'checked')[bool(sickrage.app.config.allow_high_priority)]}/>
                        <label for="allow_high_priority">
                            <p>${_('Set downloads of recently aired episodes to high priority')}</p>
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Delete Failed')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input id="delete_failed" type="checkbox"
                               name="delete_failed" ${('', 'checked')[bool(sickrage.app.config.delete_failed)]}/>
                        <label for="delete_failed">
                            ${_('Delete files left over from a failed download?')}
                        </label>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>

            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>${_('NZB Clients')}</h3>
                <p>${_('How to handle NZB search results for clients.')}</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="use_nzbs" class="enabler" title="Enable NZB searches"
                               id="use_nzbs" ${('', 'checked')[bool(sickrage.app.config.use_nzbs)]}/>
                        <label for="use_nzbs">${_('enable NZB searches')}</label>
                    </div>
                </div>

                <div id="content_use_nzbs">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Send .nzb files to:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-send"></span>
                                </div>
                                <select name="nzb_method" id="nzb_method" class="form-control" title="NZB Clients">
                                    <% nzb_method_text = {'blackhole': "Black hole", 'sabnzbd': "SABnzbd", 'nzbget': "NZBget"} %>
                                    % for curAction in ('sabnzbd', 'blackhole', 'nzbget'):
                                        <option value="${curAction}" ${('', 'selected')[sickrage.app.config.nzb_method == curAction]}>${nzb_method_text[curAction]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="blackhole_settings">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Black hole folder location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <input name="nzb_dir" id="nzb_dir"
                                           value="${sickrage.app.config.nzb_dir}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                                <label for="nzb_dir">
                                    <p>
                                        <b>.nzb</b> ${_('files are stored at this location for external software to find and use')}
                                    </p>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div id="sabnzbd_settings">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('SABnzbd server URL')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-globe"></span>
                                    </div>
                                    <input id="sab_host" name="sab_host"
                                           value="${sickrage.app.config.sab_host}"
                                           placeholder="${_('ex. http://localhost:8080/')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('SABnzbd username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="sab_username" id="sab_username"
                                           value="${sickrage.app.config.sab_username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('SABnzbd password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="sab_password" id="sab_password"
                                           value="${sickrage.app.config.sab_password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('SABnzbd API key')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-cloud"></span>
                                    </div>
                                    <input name="sab_apikey" id="sab_apikey"
                                           value="${sickrage.app.config.sab_apikey}"
                                           class="form-control"
                                           title="locate at... SABnzbd Config -> General -> API Key"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use SABnzbd category')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="sab_category" id="sab_category"
                                           value="${sickrage.app.config.sab_category}"
                                           placeholder="${_('ex. TV')}"
                                           title="SABNzbd download category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use SABnzbd category (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="sab_category_backlog" id="sab_category_backlog"
                                           value="${sickrage.app.config.sab_category_backlog}"
                                           placeholder="${_('ex. TV')}"
                                           title="add downloads of old episodes to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use SABnzbd category for anime')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="sab_category_anime" id="sab_category_anime"
                                           value="${sickrage.app.config.sab_category_anime}"
                                           placeholder="${_('ex. anime')}"
                                           title="add anime downloads to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>


                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use SABnzbd category for anime (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="sab_category_anime_backlog"
                                           id="sab_category_anime_backlog"
                                           value="${sickrage.app.config.sab_category_anime_backlog}"
                                           placeholder="${_('ex. anime')}"
                                           title="add anime downloads of old episodes to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        % if sickrage.app.config.allow_high_priority == True:
                            <div class="row field-pair">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Use forced priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="sab_forced" class="enabler"
                                           id="sab_forced" ${('', 'selected')[bool(sickrage.app.config.sab_forced)]}/>
                                    <label for="sab_forced">
                                        <p>${_('enable to change priority from HIGH to FORCED')}</p>
                                    </label>
                                </div>
                            </div>
                        % endif
                    </div>

                    <div id="nzbget_settings">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Connect using HTTPS')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input id="nzbget_use_https" type="checkbox" class="enabler"
                                       name="nzbget_use_https" ${('', 'selected')[bool(sickrage.app.config.nzbget_use_https)]}/>
                                <label for="nzbget_use_https">
                                    <p>${_('enable secure control')}</p>
                                </label>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('NZBget host:port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-globe"></span>
                                    </div>
                                    <input name="nzbget_host" id="nzbget_host"
                                           value="${sickrage.app.config.nzbget_host}"
                                           placeholder="${_('ex. localhost:6789')}"
                                           title="NZBget RPC host name and port number (not NZBgetweb!"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('NZBget username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="nzbget_username"
                                           value="${sickrage.app.config.nzbget_username}"
                                           placeholder="${_('default = nzbget')}"
                                           title="locate in nzbget.conf"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('NZBget password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="nzbget_password" id="nzbget_password"
                                           value="${sickrage.app.config.nzbget_password}"
                                           placeholder="${_('default = tegbzn6789')}"
                                           title="locate in nzbget.conf"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use NZBget category')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="nzbget_category" id="nzbget_category"
                                           value="${sickrage.app.config.nzbget_category}"
                                           placeholder="${_('ex. TV')}"
                                           title="send downloads marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use NZBget category (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="nzbget_category_backlog" id="nzbget_category_backlog"
                                           value="${sickrage.app.config.nzbget_category_backlog}"
                                           placeholder="${_('ex. TV')}"
                                           title="send downloads of old episodes marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use NZBget category for anime')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="nzbget_category_anime" id="nzbget_category_anime"
                                           value="${sickrage.app.config.nzbget_category_anime}"
                                           placeholder="${_('ex. anime')}"
                                           title="send anime downloads marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Use NZBget category for anime (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-book"></span>
                                    </div>
                                    <input name="nzbget_category_anime_backlog"
                                           id="nzbget_category_anime_backlog"
                                           value="${sickrage.app.config.nzbget_category_anime_backlog}"
                                           placeholder="${_('ex. anime')}"
                                           title="send anime downloads of old episodes marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('NZBget priority')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-exclamation-sign"></span>
                                    </div>
                                    <select name="nzbget_priority" id="nzbget_priority"
                                            title="priority for daily snatches (no backlog)"
                                            class="form-control">
                                        <option value="-100" ${('', 'selected')[sickrage.app.config.nzbget_priority == -100]}>
                                            ${_('Very low')}
                                        </option>
                                        <option value="-50" ${('', 'selected')[sickrage.app.config.nzbget_priority == -50]}>
                                            ${_('Low')}
                                        </option>
                                        <option value="0" ${('', 'selected')[sickrage.app.config.nzbget_priority == 0]}>
                                            ${_('Normal')}
                                        </option>
                                        <option value="50" ${('', 'selected')[sickrage.app.config.nzbget_priority == 50]}>
                                            ${_('High')}
                                        </option>
                                        <option value="100" ${('', 'selected')[sickrage.app.config.nzbget_priority == 100]}>
                                            ${_('Very high')}
                                        </option>
                                        <option value="900" ${('', 'selected')[sickrage.app.config.nzbget_priority == 900]}>
                                            ${_('Force')}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testSABnzbd_result">${_('Click below to test')}</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn test-button" type="button" value="${_('Test SABnzbd')}" id="testSABnzbd"/>
                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/><br>
                        </div>
                    </div>

                </div><!-- /content_use_nzbs //-->

            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    <div id="core-tab-pane3" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>${_('Torrent Clients')}</h3>
                <p>${_('How to handle Torrent search results for clients.')}</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="use_torrents" class="enabler"
                               id="use_torrents" ${('', 'checked')[bool(sickrage.app.config.use_torrents)]}/>
                        <label for="use_torrents">${_('Enable torrent searches')}</label>
                    </div>
                </div>

                <div id="content_use_torrents">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Send .torrent files to:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-send"></span>
                                </div>
                                <select name="torrent_method" id="torrent_method" class="form-control"
                                        title="Torrent Clients">
                                    <% torrent_method_text = {'blackhole': "Black hole", 'utorrent': "uTorrent", 'transmission': "Transmission", 'deluge': "Deluge (via WebUI)", 'deluged': "Deluge (via Daemon)", 'download_station': "Synology DS", 'rtorrent': "rTorrent", 'qbittorrent': "qbittorrent", 'mlnet': "MLDonkey", 'putio': "Putio"} %>
                                    % for curAction in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet', 'putio'):
                                        <option value="${curAction}" ${('', 'selected')[sickrage.app.config.torrent_method == curAction]}>${torrent_method_text[curAction]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="options_torrent_blackhole">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Black hole folder location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <input name="torrent_dir" id="torrent_dir"
                                           value="${sickrage.app.config.torrent_dir}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                                <label for="torrent_dir">
                                    <p>
                                        <b>.torrent</b> ${_('files are stored at this location for external software to find and use')}
                                    </p>
                                </label>
                            </div>
                        </div>

                        <div></div>
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/><br>
                    </div>

                    <div id="options_torrent_clients">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title" id="host_title">${_('Torrent host:port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-globe"></span>
                                    </div>
                                    <input name="torrent_host" id="torrent_host"
                                           value="${sickrage.app.config.torrent_host}"
                                           placeholder="${_('ex. http://localhost:8000/')}"
                                           title="URL to your torrent client"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_rpcurl_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title" id="rpcurl_title">${_('Torrent RPC URL')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-globe"></span>
                                    </div>
                                    <input name="torrent_rpcurl" id="torrent_rpcurl"
                                           value="${sickrage.app.config.torrent_rpcurl}"
                                           placeholder="${_('ex. transmission')}"
                                           title="The path without leading and trailing slashes"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_auth_type_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('HTTP Authentication')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <select name="torrent_auth_type" id="torrent_auth_type" title="Client AUTH type"
                                            class="form-control">
                                        <% http_authtype = {'none': _("None"), 'basic': _("Basic"), 'digest': _("Digest")} %>
                                        % for authvalue, authname in http_authtype.items():
                                            <option id="torrent_auth_type_value"
                                                    value="${authvalue}" ${('', 'selected')[sickrage.app.config.torrent_auth_type == authvalue]}>${authname}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_verify_cert_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Verify certificate')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_verify_cert" class="enabler"
                                       id="torrent_verify_cert" ${('', 'checked')[bool(sickrage.app.config.torrent_verify_cert)]}/>
                                <label for="torrent_verify_cert">
                                    <p id="torrent_verify_deluge">
                                        ${_('disable if you get "Deluge: Authentication Error" in your log')}
                                    </p>
                                    <p id="torrent_verify_rtorrent">
                                        ${_('Verify SSL certificates for HTTPS requests')}
                                    </p>
                                </label>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_username_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title" id="username_title">${_('Client username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="torrent_username" id="torrent_username"
                                           value="${sickrage.app.config.torrent_username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_password_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title" id="password_title">${_('Client password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="torrent_password" id="torrent_password"
                                           value="${sickrage.app.config.torrent_password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_label_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Add label to torrent')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-tag"></span>
                                    </div>
                                    <input name="torrent_label" id="torrent_label"
                                           value="${sickrage.app.config.torrent_label}"
                                           placeholder="${_('blank spaces are not allowed')}"
                                           title="label plugin must be enabled in Deluge clients"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_label_anime_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Add anime label to torrent')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-tag"></span>
                                    </div>
                                    <input name="torrent_label_anime" id="torrent_label_anime"
                                           value="${sickrage.app.config.torrent_label_anime}"
                                           placeholder="${_('blank spaces are not allowed')}"
                                           title="label plugin must be enabled in Deluge clients"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_path_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Downloaded files location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <input name="torrent_path" id="torrent_path"
                                           value="${sickrage.app.config.torrent_path}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                                <label for="torrent_path">
                                    ${_('where the torrent client will save downloaded files (blank for client default)')}
                                    <br/>
                                    <b>${_('NOTE:')}</b> ${_('the destination has to be a shared folder for Synology DS')}
                                </label>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_seed_time_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title" id="torrent_seed_time_label">
                                    ${_('Minimum seeding time is')}
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-upload"></span>
                                    </div>
                                    <input type="number"
                                           step="1"
                                           name="torrent_seed_time"
                                           id="torrent_seed_time"
                                           value="${sickrage.app.config.torrent_seed_time}"
                                           title="hours. (default:'0' passes blank to client and '-1' passes nothing)"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_paused_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Start torrent paused')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_paused" class="enabler"
                                       id="torrent_paused" ${('', 'checked')[bool(sickrage.app.config.torrent_paused)]}/>
                                <label for="torrent_paused">
                                    <p>${_('add .torrent to client but do <b>not</b> start downloading')}</p>
                                </label>
                            </div>
                        </div>

                        <div class="row field-pair" id="torrent_high_bandwidth_option">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Allow high bandwidth')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_high_bandwidth" class="enabler"
                                       id="torrent_high_bandwidth" ${('', 'checked')[bool(sickrage.app.config.torrent_high_bandwidth)]}/>
                                <label for="torrent_high_bandwidth">
                                    <p>${_('use high bandwidth allocation if priority is high')}</p>
                                </label>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-12">
                                <div class="testNotification" id="test_torrent_result">${_('Click below to test')}</div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-12">
                                <input class="btn test-button" type="button" value="${_('Test Connection')}"
                                       id="test_torrent"/>
                                <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/><br>
                            </div>
                        </div>

                    </div>
                </div><!-- /content_use_torrents //-->
            </fieldset>
        </div>
    </div><!-- /tab-pane3 //-->
</%block>