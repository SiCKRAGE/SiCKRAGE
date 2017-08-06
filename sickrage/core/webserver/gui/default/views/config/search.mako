<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveSearch' %></%def>
<%!
    import sickrage
%>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Search Settings</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">NZB Clients</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane3">Torrent Clients</a></li>
</%block>
<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active clearfix">
        <div class="tab-pane-desc">
            <h3>Search Settings</h3>
            <p>How to manage searching with <a href="${srWebRoot}/config/providers">providers</a>.</p>
        </div>
        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Randomize Providers</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="randomize_providers" id="randomize_providers"
                           class="enabler" ${('', 'checked')[bool(sickrage.srCore.srConfig.RANDOMIZE_PROVIDERS)]}/>
                    <label for="randomize_providers"><p>randomize the provider search order instead of going in order of
                        placement</p></label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Download propers</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="download_propers" id="download_propers"
                           class="enabler" ${('', 'checked')[bool(sickrage.srCore.srConfig.DOWNLOAD_PROPERS)]}/>
                    <label for="download_propers"><p>replace original download with "Proper" or "Repack" if nuked</p>
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <label for="enable_rss_cache">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable provider RSS cache</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="enable_rss_cache" id="enable_rss_cache"
                               class="enabler" ${('', 'checked')[bool(sickrage.srCore.srConfig.ENABLE_RSS_CACHE)]}/>
                        <p>Enables/Disables provider RSS cache</p>
                    </div>
                </label>
            </div>
            <div id="content_download_propers">
                <div class="row field-pair">
                    <label for="check_propers_interval">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Check propers every:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select id="check_propers_interval" name="check_propers_interval"
                                    class="form-control input-sm">
                                <% check_propers_interval_text = {'daily': "24 hours", '4h': "4 hours", '90m': "90 mins", '45m': "45 mins", '15m': "15 mins"} %>
                                % for curInterval in ('daily', '4h', '90m', '45m', '15m'):
                                    <option value="${curInterval}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROPER_SEARCHER_INTERVAL == curInterval]}>${check_propers_interval_text[curInterval]}</option>
                                % endfor
                            </select>
                        </div>
                    </label>
                </div>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Backlog search frequency</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="backlog_frequency"
                               value="${sickrage.srCore.srConfig.BACKLOG_SEARCHER_FREQ}"
                               class="form-control input-sm input75"/>
                        <p>time in minutes between searches
                            (min. ${sickrage.srCore.srConfig.MIN_BACKLOG_SEARCHER_FREQ}
                            )</p>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Daily search frequency</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="dailysearch_frequency"
                               value="${sickrage.srCore.srConfig.DAILY_SEARCHER_FREQ}"
                               class="form-control input-sm input75"/>
                        <p>time in minutes between searches
                            (min. ${sickrage.srCore.srConfig.MIN_DAILY_SEARCHER_FREQ})</p>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Usenet retention</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="usenet_retention"
                               value="${sickrage.srCore.srConfig.USENET_RETENTION}"
                               class="form-control input-sm input75"/>
                        <p>age limit in days for usenet articles to be used (e.g. 500)</p>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Torrent Trackers</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="torrent_trackers"
                               value="${sickrage.srCore.srConfig.TORRENT_TRACKERS}"
                               class="form-control input-sm input350" autocapitalize="off"/>
                        <div class="clear-left">Trackers that will be added to magnets without trackers<br>
                            separate trackers with a comma, e.g. "tracker1,tracker2,tracker3"
                        </div>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Ignore words</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="ignore_words"
                               value="${sickrage.srCore.srConfig.IGNORE_WORDS}"
                               class="form-control input-sm input350" autocapitalize="off"/>
                        <div class="clear-left">results with one or more word from this list will be ignored<br>
                            separate words with a comma, e.g. "word1,word2,word3"
                        </div>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Require words</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="require_words"
                               value="${sickrage.srCore.srConfig.REQUIRE_WORDS}"
                               class="form-control input-sm input350" autocapitalize="off"/>
                        <div class="clear-left">results with no word from this list will be ignored<br>
                            separate words with a comma, e.g. "word1,word2,word3"
                        </div>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Ignore language names in subbed results</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input name="ignored_subs_list"
                               value="${sickrage.srCore.srConfig.IGNORED_SUBS_LIST}"
                               class="form-control input-sm input350" autocapitalize="off"/>
                        <div class="clear-left">Ignore subbed releases based on language names <br>
                            Example: "dk" will ignore words: dksub, dksubs, dksubbed, dksubed <br>
                            separate languages with a comma, e.g. "lang1,lang2,lang3
                        </div>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <label for="allow_high_priority">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Allow high priority</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="allow_high_priority"
                               id="allow_high_priority" ${('', 'checked')[bool(sickrage.srCore.srConfig.ALLOW_HIGH_PRIORITY)]}/>
                        <p>set downloads of recently aired episodes to high priority</p>
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <input id="use_failed_downloads" type="checkbox" class="enabler"
                       name="use_failed_downloads" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS)]} />
                <label for="use_failed_downloads">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Use Failed Downloads</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Use Failed Download Handling?</div>
                </label>
                <label class="nocheck" for="use_failed_downloads">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">&nbsp;</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Will only work with
                        snatched/downloaded episodes after enabling this
                    </div>
                </label>
            </div>

            <div id="content_use_failed_downloads">
                <div class="row field-pair">
                    <input id="delete_failed" type="checkbox"
                           name="delete_failed" ${('', 'checked')[bool(sickrage.srCore.srConfig.DELETE_FAILED)]}/>
                    <label for="delete_failed">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Delete Failed</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Delete files left over from a
                            failed download?
                        </div>
                    </label>
                    <label class="nocheck" for="delete_failed">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">&nbsp;</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc"><b>NOTE:</b> This only works if
                            Use Failed Downloads is enabled.
                        </div>
                    </label>
                </div>
            </div>

            <input type="submit" class="btn config_submitter" value="Save Changes"/>

        </fieldset>
    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="tab-pane fade">

        <div class="tab-pane-desc">
            <h3>NZB Clients</h3>
            <p>How to handle NZB search results for clients.</p>
        </div>

        <fieldset class="tab-pane-list">

            <div class="row field-pair">
                <label for="use_nzbs">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable NZB searches</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="use_nzbs" class="enabler"
                               id="use_nzbs" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_NZBS)]}/>
                    </div>
                </label>
            </div>

            <div id="content_use_nzbs">
                <div class="row field-pair">
                    <label for="nzb_method">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Send .nzb files to:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select name="nzb_method" id="nzb_method" class="form-control input-sm">
                                <% nzb_method_text = {'blackhole': "Black hole", 'sabnzbd': "SABnzbd", 'nzbget': "NZBget"} %>
                                % for curAction in ('sabnzbd', 'blackhole', 'nzbget'):
                                    <option value="${curAction}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZB_METHOD == curAction]}>${nzb_method_text[curAction]}</option>
                                % endfor
                            </select>
                        </div>
                    </label>
                </div>

                <div id="blackhole_settings">
                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Black hole folder location</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzb_dir" id="nzb_dir"
                                       value="${sickrage.srCore.srConfig.NZB_DIR}"
                                       class="form-control input-sm input350" autocapitalize="off"/>
                                <div class="clear-left"><p><b>.nzb</b> files are stored at this location for
                                    external software to find and use</p></div>
                            </div>
                        </label>
                    </div>
                </div>

                <div id="sabnzbd_settings">
                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">SABnzbd server URL</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input id="sab_host" name="sab_host"
                                       value="${sickrage.srCore.srConfig.SAB_HOST}"
                                       class="form-control input-sm input350" autocapitalize="off"/>
                                <div class="clear-left"><p>URL to your SABnzbd server (e.g.
                                    http://localhost:8080/)</p></div>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">SABnzbd username</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_username" id="sab_username"
                                       value="${sickrage.srCore.srConfig.SAB_USERNAME}"
                                       class="form-control input-sm input200"
                                       autocapitalize="off"/>
                                <p>(blank for none)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">SABnzbd password</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="password" name="sab_password" id="sab_password"
                                       value="${sickrage.srCore.srConfig.SAB_PASSWORD}"
                                       class="form-control input-sm input200"
                                       autocapitalize="off"/>
                                <p>(blank for none)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">SABnzbd API key</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_apikey" id="sab_apikey"
                                       value="${sickrage.srCore.srConfig.SAB_APIKEY}"
                                       class="form-control input-sm input350"
                                       autocapitalize="off"/>
                                <div class="clear-left"><p>locate at... SABnzbd Config -> General -> API Key</p>
                                </div>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use SABnzbd category</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_category" id="sab_category"
                                       value="${sickrage.srCore.srConfig.SAB_CATEGORY}"
                                       class="form-control input-sm input200"/>
                                <p>add downloads to this category (e.g. TV)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use SABnzbd category (backlog episodes)</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_category_backlog" id="sab_category_backlog"
                                       value="${sickrage.srCore.srConfig.SAB_CATEGORY_BACKLOG}"
                                       class="form-control input-sm input200"/>
                                <p>add downloads of old episodes to this category (e.g. TV)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use SABnzbd category for anime</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_category_anime" id="sab_category_anime"
                                       value="${sickrage.srCore.srConfig.SAB_CATEGORY_ANIME}"
                                       class="form-control input-sm input200"/>
                                <p>add anime downloads to this category (e.g. anime)</p>
                            </div>
                        </label>
                    </div>


                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use SABnzbd category for anime (backlog episodes)</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="sab_category_anime_backlog"
                                       id="sab_category_anime_backlog"
                                       value="${sickrage.srCore.srConfig.SAB_CATEGORY_ANIME_BACKLOG}"
                                       class="form-control input-sm input200"/>
                                <p>add anime downloads of old episodes to this category (e.g. anime)</p>
                            </div>
                        </label>
                    </div>

                    % if sickrage.srCore.srConfig.ALLOW_HIGH_PRIORITY == True:
                        <div class="row field-pair">
                            <label for="sab_forced">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">Use forced priority</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="sab_forced" class="enabler"
                                           id="sab_forced" ${('', 'selected="selected"')[bool(sickrage.srCore.srConfig.SAB_FORCED)]}/>
                                    <p>enable to change priority from HIGH to FORCED</p></div>
                            </label>
                        </div>
                    % endif
                </div>

                <div id="nzbget_settings">
                    <div class="row field-pair">
                        <label for="nzbget_use_https">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Connect using HTTPS</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input id="nzbget_use_https" type="checkbox" class="enabler"
                                       name="nzbget_use_https" ${('', 'selected="selected"')[bool(sickrage.srCore.srConfig.NZBGET_USE_HTTPS)]}/>
                                <p><b>note:</b> enable Secure control in NZBGet and set the correct Secure Port
                                    here</p>
                            </div>
                        </label>

                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">NZBget host:port</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_host" id="nzbget_host"
                                       value="${sickrage.srCore.srConfig.NZBGET_HOST}"
                                       class="form-control input-sm input350"
                                       autocapitalize="off"/>
                                <p>(e.g. localhost:6789)</p>
                                <div class="clear-left"><p>NZBget RPC host name and port number (not
                                    NZBgetweb!)</p></div>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">NZBget username</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_username"
                                       value="${sickrage.srCore.srConfig.NZBGET_USERNAME}"
                                       class="form-control input-sm input200" autocapitalize="off"/>
                                <p>locate in nzbget.conf (default:nzbget)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">NZBget password</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="password" name="nzbget_password" id="nzbget_password"
                                       value="${sickrage.srCore.srConfig.NZBGET_PASSWORD}"
                                       class="form-control input-sm input200" autocapitalize="off"/>
                                <p>locate in nzbget.conf (default:tegbzn6789)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use NZBget category</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_category" id="nzbget_category"
                                       value="${sickrage.srCore.srConfig.NZBGET_CATEGORY}"
                                       class="form-control input-sm input200"/>
                                <p>send downloads marked this category (e.g. TV)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use NZBget category (backlog episodes)</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_category_backlog" id="nzbget_category_backlog"
                                       value="${sickrage.srCore.srConfig.NZBGET_CATEGORY_BACKLOG}"
                                       class="form-control input-sm input200"/>
                                <p>send downloads of old episodes marked this category (e.g. TV)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use NZBget category for anime</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_category_anime" id="nzbget_category_anime"
                                       value="${sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME}"
                                       class="form-control input-sm input200"/>
                                <p>send anime downloads marked this category (e.g. anime)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Use NZBget category for anime (backlog episodes)</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="nzbget_category_anime_backlog"
                                       id="nzbget_category_anime_backlog"
                                       value="${sickrage.srCore.srConfig.NZBGET_CATEGORY_ANIME_BACKLOG}"
                                       class="form-control input-sm input200"/>
                                <p>send anime downloads of old episodes marked this category (e.g. anime)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NZBget priority</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select name="nzbget_priority" id="nzbget_priority"
                                    class="form-control input-sm">
                                <option value="-100" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == -100]}>
                                    Very low
                                </option>
                                <option value="-50" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == -50]}>
                                    Low
                                </option>
                                <option value="0" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == 0]}>
                                    Normal
                                </option>
                                <option value="50" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == 50]}>
                                    High
                                </option>
                                <option value="100" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == 100]}>
                                    Very high
                                </option>
                                <option value="900" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NZBGET_PRIORITY == 900]}>
                                    Force
                                </option>
                            </select>
                            <label for="nzbget_priority">priority for daily snatches (no backlog)</label>
                        </div>
                    </div>
                </div>

                <div class="testNotification" id="testSABnzbd_result">Click below to test</div>
                <input class="btn test-button" type="button" value="Test SABnzbd" id="testSABnzbd"/>
                <input type="submit" class="btn config_submitter" value="Save Changes"/><br>

            </div><!-- /content_use_nzbs //-->

        </fieldset>
    </div><!-- /tab-pane2 //-->

    <div id="core-tab-pane3" class="tab-pane fade">

        <div class="tab-pane-desc">
            <h3>Torrent Clients</h3>
            <p>How to handle Torrent search results for clients.</p>
        </div>

        <fieldset class="tab-pane-list">

            <div class="row field-pair">
                <label for="use_torrents">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable torrent searches</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="use_torrents" class="enabler"
                               id="use_torrents" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_TORRENTS)]}/>
                    </div>
                </label>
            </div>

            <div id="content_use_torrents">
                <div class="row field-pair">
                    <label for="torrent_method">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Send .torrent files to:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select name="torrent_method" id="torrent_method" class="form-control input-sm">
                                <% torrent_method_text = {'blackhole': "Black hole", 'utorrent': "uTorrent", 'transmission': "Transmission", 'deluge': "Deluge (via WebUI)", 'deluged': "Deluge (via Daemon)", 'download_station': "Synology DS", 'rtorrent': "rTorrent", 'qbittorrent': "qbittorrent", 'mlnet': "MLDonkey", 'putio': "Putio"} %>
                                % for curAction in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet', 'putio'):
                                    <option value="${curAction}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TORRENT_METHOD == curAction]}>${torrent_method_text[curAction]}</option>
                                % endfor
                            </select>
                        </div>
                    </label>

                    <div id="options_torrent_blackhole">
                        <div class="row field-pair">
                            <label>
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">Black hole folder location</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input name="torrent_dir" id="torrent_dir"
                                           value="${sickrage.srCore.srConfig.TORRENT_DIR}"
                                           class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                    <div class="clear-left">
                                        <p>
                                            <b>.torrent</b> files are stored at this location for
                                            external software to find and use
                                        </p>
                                    </div>
                                </div>
                            </label>
                        </div>

                        <div></div>
                        <input type="submit" class="btn config_submitter" value="Save Changes"/><br>
                    </div>
                </div>

                <div id="options_torrent_clients">
                    <div class="row field-pair">
                        <label>
                            <span class="component-title" id="host_title">Torrent host:port</span>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="torrent_host" id="torrent_host"
                                       value="${sickrage.srCore.srConfig.TORRENT_HOST}"
                                       class="form-control input-sm input350"
                                       autocapitalize="off"/>
                                <div class="clear-left">
                                    <p id="host_desc_torrent">URL to your torrent client (e.g.
                                        http://localhost:8000/)</p>
                                </div>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_rpcurl_option">
                        <label>
                            <span class="component-title" id="rpcurl_title">Torrent RPC URL</span>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="torrent_rpcurl" id="torrent_rpcurl"
                                       value="${sickrage.srCore.srConfig.TORRENT_RPCURL}"
                                       class="form-control input-sm input350"
                                       autocapitalize="off"/>
                                <div class="clear-left">
                                    <p id="rpcurl_desc_">The path without leading and trailing slashes (e.g.
                                        transmission)</p>
                                </div>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_auth_type_option">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Http Authentication</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <select name="torrent_auth_type" id="torrent_auth_type"
                                        class="form-control input-sm">
                                    <% http_authtype = {'none': "None", 'basic': "Basic", 'digest': "Digest"} %>
                                    % for authvalue, authname in http_authtype.items():
                                        <option id="torrent_auth_type_value"
                                                value="${authvalue}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TORRENT_AUTH_TYPE == authvalue]}>${authname}</option>
                                    % endfor
                                </select>
                                <p></p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_verify_cert_option">
                        <label for="torrent_verify_cert">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Verify certificate</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_verify_cert" class="enabler"
                                       id="torrent_verify_cert" ${('', 'checked')[bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT)]}/>
                                <p id="torrent_verify_deluge">disable if you get "Deluge: Authentication Error"
                                    in your log</p>
                                <p id="torrent_verify_rtorrent">Verify SSL certificates for HTTPS requests</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_username_option">
                        <label>
                            <span class="component-title" id="username_title">Client username</span>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="torrent_username" id="torrent_username"
                                       value="${sickrage.srCore.srConfig.TORRENT_USERNAME}"
                                       class="form-control input-sm input200" autocapitalize="off"/>
                                <p>(blank for none)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_password_option">
                        <label>
                            <span class="component-title" id="password_title">Client password</span>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="password" name="torrent_password" id="torrent_password"
                                       value="${sickrage.srCore.srConfig.TORRENT_PASSWORD}"
                                       class="form-control input-sm input200" autocapitalize="off"/>
                                <p>(blank for none)</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_label_option">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Add label to torrent</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input name="torrent_label" id="torrent_label"
                                           value="${sickrage.srCore.srConfig.TORRENT_LABEL}"
                                           class="form-control input-sm input200"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="torrent_label">
                                        (blank spaces are not allowed)<br/>
                                        note: label plugin must be enabled in Deluge clients
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row field-pair" id="torrent_label_anime_option">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Add label to torrent for anime</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input name="torrent_label_anime" id="torrent_label_anime"
                                           value="${sickrage.srCore.srConfig.TORRENT_LABEL_ANIME}"
                                           class="form-control input-sm input200"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="torrent_label_anime">
                                        (blank spaces are not allowed)<br/>
                                        note: label plugin must be enabled in Deluge clients
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row field-pair" id="torrent_path_option">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Downloaded files location</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input name="torrent_path" id="torrent_path"
                                   value="${sickrage.srCore.srConfig.TORRENT_PATH}"
                                   class="form-control input-sm input350"
                                   autocapitalize="off"/>
                            <label for="torrent_path">
                                where the torrent client will save downloaded files (blank for client default)<br/>
                                <b>note:</b> the destination has to be a shared folder for Synology DS
                            </label>
                        </div>
                    </div>

                    <div class="row field-pair" id="torrent_seed_time_option">
                        <label>
                            <span class="component-title" id="torrent_seed_time_label">Minimum seeding time is</span>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc"><input type="number"
                                                                                                    step="1"
                                                                                                    name="torrent_seed_time"
                                                                                                    id="torrent_seed_time"
                                                                                                    value="${sickrage.srCore.srConfig.TORRENT_SEED_TIME}"
                                                                                                    class="form-control input-sm input100"/>
                                <p>hours. (default:'0' passes blank to client and '-1' passes nothing)</p></div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_paused_option">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Start torrent paused</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_paused" class="enabler"
                                       id="torrent_paused" ${('', 'checked')[bool(sickrage.srCore.srConfig.TORRENT_PAUSED)]}/>
                                <p>add .torrent to client but do <b style="font-weight:900">not</b> start
                                    downloading</p>
                            </div>
                        </label>
                    </div>

                    <div class="row field-pair" id="torrent_high_bandwidth_option">
                        <label>
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Allow high bandwidth</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="torrent_high_bandwidth" class="enabler"
                                       id="torrent_high_bandwidth" ${('', 'checked')[bool(sickrage.srCore.srConfig.TORRENT_HIGH_BANDWIDTH)]}/>
                                <p>use high bandwidth allocation if priority is high</p>
                            </div>
                        </label>
                    </div>

                    <div class="testNotification" id="test_torrent_result">Click below to test</div>
                    <input class="btn test-button" type="button" value="Test Connection"
                           id="test_torrent"/>
                    <input type="submit" class="btn config_submitter" value="Save Changes"/><br>
                </div>
            </div><!-- /content_use_torrents //-->
        </fieldset>
    </div><!-- /tab-pane3 //-->
</%block>