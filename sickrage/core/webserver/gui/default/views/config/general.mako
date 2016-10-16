<%inherit file="../layouts/main.mako"/>
<%!
    import datetime
    import locale

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickrage.core.helpers.srdatetime import srDateTime, date_presets, time_presets
    from sickrage.core.helpers import anon_url
    from sickrage.indexers import srIndexerApi
    from sickrage.metadata import GenericMetadata

%>
<%block name="content">

    <% indexer = 0 %>
    % if sickrage.srCore.srConfig.INDEXER_DEFAULT:
        <% indexer = sickrage.srCore.srConfig.INDEXER_DEFAULT %>
    % endif

    <div id="config">
        <div id="ui-content">
            <form id="configForm" action="saveGeneral" method="post">
                <div id="ui-components">
                    <ul>
                        <li><a href="#core-component-group1">Misc</a></li>
                        <li><a href="#core-component-group2">Interface</a></li>
                        <li><a href="#core-component-group3">Advanced Settings</a></li>
                    </ul>

                    <div id="core-component-group1">
                        <div class="component-group">

                            <div class="component-group-desc">
                                <h3>Misc</h3>
                                <p>Startup options. Indexer options. Log and show file locations.</p>
                                <p><b>Some options may require a manual restart to take effect.</b></p>
                            </div>

                            <fieldset class="component-group-list">
                                <div class="field-pair">
                                    <label for="indexerDefaultLang">
                                        <span class="component-title">Default Indexer Language</span>
                                <span class="component-desc">
                                    <select name="indexerDefaultLang" id="indexerDefaultLang"
                                            class="form-control form-control-inline input-sm bfh-languages"
                                            data-language=${sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE} data-available="${','.join(srIndexerApi().indexer().languages.keys())}"></select>
                                    <span>for adding shows and metadata providers</span>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="launch_browser">
                                        <span class="component-title">Launch browser</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="launch_browser"
                                           id="launch_browser" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.LAUNCH_BROWSER)]}/>
                                    <p>open the SickRage home page on startup</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="default_page">
                                        <span class="component-title">Initial page</span>
                                <span class="component-desc">
                                    <select id="default_page" name="default_page" class="form-control input-sm">
                                        <option value="home" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'home']}>
                                            Shows
                                        </option>
                                        <option value="schedule" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'schedule']}>
                                            Schedule
                                        </option>
                                        <option value="history" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'history']}>
                                            History
                                        </option>
                                        <option value="news" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'news']}>
                                            News
                                        </option>
                                        <option value="IRC" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'IRC']}>
                                            IRC
                                        </option>
                                    </select>
                                    <span>when launching SickRage interface</span>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="showupdate_hour">
                                        <span class="component-title">Daily show updates start time</span>
                                        <span class="component-desc">
                                            <input type="text" name="showupdate_hour" id="showupdate_hour"
                                                   value="${sickrage.srCore.srConfig.SHOWUPDATE_HOUR}"
                                                   class="form-control input-sm input75"/>
                                            <p>with information such as next air dates, show ended, etc. Use 15 for 3pm, 4 for 4am etc. Anything over 23 or under 0 will be set to 0 (12am)</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="showupdate_hour">
                                        <span class="component-title">Daily show updates stale shows</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="showupdate_stale"
                                                   id="showupdate_stale" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SHOWUPDATE_STALE)]}/>
                                            <p>should ended shows last updated less then 90 days get updated and refreshed automatically ?</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <span class="component-title">Send to trash for actions</span>
                            <span class="component-desc">
                                <label for="trash_remove_show" class="nextline-block">
                                    <input type="checkbox" name="trash_remove_show"
                                           id="trash_remove_show" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.TRASH_REMOVE_SHOW)]}/>
                                    <p>when using show "Remove" and delete files</p>
                                </label>
                                <label for="trash_rotate_logs" class="nextline-block">
                                    <input type="checkbox" name="trash_rotate_logs"
                                           id="trash_rotate_logs" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.TRASH_ROTATE_LOGS)]}/>
                                    <p>on scheduled deletes of the oldest log files</p>
                                </label>
                                <div class="clear-left"><p>selected actions use trash (recycle bin) instead of the default permanent delete</p></div>
                            </span>
                                </div>

                                <div class="field-pair">
                                    <label for="log_dir">
                                        <span class="component-title">Log file folder location</span>
                                <span class="component-desc">
                                    <input type="text" name="log_dir" id="log_dir"
                                           value="${sickrage.srCore.srConfig.LOG_DIR}"
                                           class="form-control input-sm input350" autocapitalize="off"/>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="log_nr">
                                        <span class="component-title">Number of Log files saved</span>
                                <span class="component-desc">
                                    <input type="text" name="log_nr" id="log_nr"
                                           value="${sickrage.srCore.srConfig.LOG_NR}"
                                           class="form-control input-sm input75"/>
                                    <p>number of log files saved when rotating logs (default: 5) (REQUIRES RESTART)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="log_size">
                                        <span class="component-title">Size of Log files saved</span>
                                <span class="component-desc">
                                    <input type="text" name="log_size" id="log_size"
                                           value="${sickrage.srCore.srConfig.LOG_SIZE}"
                                           class="form-control input-sm input75"/>
                                    <p>maximum size of a log file saved (default: 1048576 (1MB)) (REQUIRES RESTART)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="indexer_default">
                                        <span class="component-title">Use initial indexer set to</span>
                                <span class="component-desc">
                                    <select id="indexer_default" name="indexer_default" class="form-control input-sm">
                                        <option value="0" ${('', 'selected="selected"')[indexer == 0]}>All Indexers</option>
                                        % for indexer in srIndexerApi().indexers:
                                            <option value="${indexer}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.INDEXER_DEFAULT == indexer]}>${srIndexerApi().indexers[indexer]}</option>
                                        % endfor
                                    </select>
                                    <span>as the default selection when adding new shows</span>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="indexer_timeout">
                                        <span class="component-title">Timeout show indexer at</span>
                                <span class="component-desc">
                                    <input type="text" name="indexer_timeout" id="indexer_timeout"
                                           value="${sickrage.srCore.srConfig.INDEXER_TIMEOUT}"
                                           class="form-control input-sm input75"/>
                                    <p>seconds of inactivity when finding new shows (default:10)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Show root directories</span>
                                <span class="component-desc">
                                    <p>where the files of shows are located</p>
                                    <%include file="../includes/root_dirs.mako"/>
                                </span>
                                    </label>
                                </div>

                                <input type="submit" class="btn config_submitter" value="Save Changes"/>
                            </fieldset>
                        </div>
                        <div class="component-group">

                            <div class="component-group-desc">
                                <h3>Updates</h3>
                                <p>Options for software updates.</p>
                            </div>
                            <fieldset class="component-group-list">

                                <div class="field-pair">
                                    <label for="version_notify">
                                        <span class="component-title">Check software updates</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="version_notify"
                                           id="version_notify" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.VERSION_NOTIFY)]}/>
                                    <p>and display notifications when updates are available.
                                    Checks are run on startup and at the frequency set below*</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="auto_update">
                                        <span class="component-title">Automatically update</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="auto_update"
                                           id="auto_update" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.AUTO_UPDATE)]}/>
                                    <p>fetch and install software updates.
                                    Updates are run on startup and in the background at the frequency set below*</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Check the server every*</span>
                                <span class="component-desc">
                                    <input type="text" name="update_frequency" id="update_frequency"
                                           value="${sickrage.srCore.srConfig.VERSION_UPDATER_FREQ}"
                                           class="form-control input-sm input75"/>
                                    <p>hours for software updates (default:12)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="notify_on_update">
                                        <span class="component-title">Notify on software update</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="notify_on_update"
                                           id="notify_on_update" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.NOTIFY_ON_UPDATE)]}/>
                                    <p>send a message to all enabled notifiers when SickRage has been updated</p>
                                </span>
                                    </label>
                                </div>

                                <input type="submit" class="btn config_submitter" value="Save Changes"/>
                            </fieldset>

                        </div>
                    </div><!-- /component-group1 //-->


                    <div id="core-component-group2">
                        <div class="component-group">

                            <div class="component-group-desc">
                                <h3>User Interface</h3>
                                <p>Options for visual appearance.</p>
                            </div>

                            <fieldset class="component-group-list">

                                <div class="field-pair">
                                    <label for="theme_name">
                                        <span class="component-title">Display theme:</span>
                                <span class="component-desc">
                                    <select id="theme_name" name="theme_name" class="form-control input-sm">
                                        <option value="dark" ${('', 'selected="selected"')[sickrage.srCore.srConfig.THEME_NAME == 'dark']}>
                                            Dark
                                        </option>
                                        <option value="light" ${('', 'selected="selected"')[sickrage.srCore.srConfig.THEME_NAME == 'light']}>
                                            Light
                                        </option>
                                    </select>
                                    <span class="red-text">for appearance to take effect, save then refresh your browser</span>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="display_all_seasons">
                                        <span class="component-title">Show all seasons</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="display_all_seasons"
                                           id="display_all_seasons" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.DISPLAY_ALL_SEASONS)]}>
                                    <p>on the show summary page</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="sort_article">
                                        <span class="component-title">Sort with "The", "A", "An"</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="sort_article"
                                           id="sort_article" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SORT_ARTICLE)]}/>
                                    <p>include articles ("The", "A", "An") when sorting show lists</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="filter_row">
                                        <span class="component-title">Filter Row</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="filter_row"
                                           id="filter_row" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.FILTER_ROW)]}/>
                                    <p>Add a filter row to the show display on the home page</p>
                                    <p>Supports =, >, >=, <=, <, xx to yy , xx - yy</p>
                                    <p><b>Note:</b> =, >, >=, <=, < should be first, followed by a space, then the value.</p>
                                    <p>Examples: '> 90', '= 100', '0 to 99'</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="coming_eps_missed_range">
                                        <span class="component-title">Missed episodes range</span>
                                <span class="component-desc">
                                    <input type="number" step="1" min="7" name="coming_eps_missed_range"
                                           id="coming_eps_missed_range"
                                           value="${sickrage.srCore.srConfig.COMING_EPS_MISSED_RANGE}"
                                           class="form-control input-sm input75"/>
                                    <p>Set the range in days of the missed episodes in the Schedule page</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="fuzzy_dating">
                                        <span class="component-title">Display fuzzy dates</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="fuzzy_dating" id="fuzzy_dating"
                                           class="viewIf datePresets" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}/>
                                    <p>move absolute dates into tooltips and display e.g. "Last Thu", "On Tue"</p>
                                </span>
                                    </label>
                                </div>
                                <div class="field-pair show_if_fuzzy_dating ${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                                    <label for="trim_zero">
                                        <span class="component-title">Trim zero padding</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="trim_zero"
                                           id="trim_zero" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.TRIM_ZERO)]}/>
                                    <p>remove the leading number "0" shown on hour of day, and date of month</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="date_presets">
                                        <span class="component-title">Date style:</span>
                                <span class="component-desc">
                                    <select class="form-control input-sm ${(' metadataDiv', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                            id="date_presets${('_na', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                            name="date_preset${('_na', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                                        % for cur_preset in date_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == cur_preset or ("%x" == sickrage.srCore.srConfig.DATE_PRESET and cur_preset == '%a, %b %d, %Y')]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset)}</option>
                                        % endfor
                                    </select>
                                    <select class="form-control input-sm ${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                            id="date_presets${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                            name="date_preset${('_na', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                                        <option value="%x" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == '%x']}>
                                            Use System Default
                                        </option>
                                        % for cur_preset in date_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == cur_preset]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset)}</option>
                                        % endfor
                                    </select>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="time_presets">
                                        <span class="component-title">Time style:</span>
                                <span class="component-desc">
                                    <select id="time_presets" name="time_preset" class="form-control input-sm">
                                        % for cur_preset in time_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS == cur_preset]}>${srDateTime.now().srftime(show_seconds=True, t_preset=cur_preset)}</option>
                                        % endfor
                                    </select>
                                    <span><b>note:</b> seconds are only shown on the History page</span>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <span class="component-title">Timezone:</span>
                            <span class="component-desc">
                                <label for="local" class="space-right">
                                    <input type="radio" name="timezone_display" id="local"
                                           value="local" ${('', 'checked="checked"')[sickrage.srCore.srConfig.TIMEZONE_DISPLAY == "local"]} />Local
                                </label>
                                <label for="network">
                                    <input type="radio" name="timezone_display" id="network"
                                           value="network" ${('', 'checked="checked"')[sickrage.srCore.srConfig.TIMEZONE_DISPLAY == "network"]} />Network
                                </label>
                                <div class="clear-left">
                                <p>display dates and times in either your timezone or the shows network timezone</p>
                                </div>
                                <div class="clear-left">
                                <p> <b>Note:</b> Use local timezone to start searching for episodes minutes after show ends (depends on your dailysearch frequency)</p>
                                </div>
                            </span>
                                </div>

                                <div class="field-pair">
                                    <label for="download_url">
                                        <span class="component-title">Download url</span>
                                        <input type="text" name="download_url" id="download_url"
                                               value="${sickrage.srCore.srConfig.DOWNLOAD_URL}" size="35"
                                               autocapitalize="off"/>
                                    </label>
                                    <label>
                                        <span class="component-title">&nbsp;</span>
                                        <span class="component-desc">URL where the shows can be downloaded.</span>
                                    </label>
                                </div>


                                <input type="submit" class="btn config_submitter" value="Save Changes"/>

                            </fieldset>

                        </div><!-- /User interface component-group -->

                        <div class="component-group">

                            <div class="component-group-desc">
                                <h3>Web Interface</h3>
                                <p>It is recommended that you enable a username and password to secure SickRage from
                                    being tampered with remotely.</p>
                                <p><b>These options require a manual restart to take effect.</b></p>
                            </div>

                            <fieldset class="component-group-list">

                                <div class="field-pair">
                                    <label for="api_key">
                                        <span class="component-title">API key</span>
                                <span class="component-desc">
                                    <input type="text" name="api_key" id="api_key"
                                           value="${sickrage.srCore.srConfig.API_KEY}"
                                           class="form-control input-sm input300" readonly="readonly"/>
                                    <input class="btn btn-inline" type="button" id="generate_new_apikey"
                                           value="Generate">
                                    <div class="clear-left">
                                        <p>used to give 3rd party programs limited access to SickRage</p>
                                        <p>you can try all the features of the API <a href="/apibuilder/">here</a></p>
                                    </div>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="web_log">
                                        <span class="component-title">HTTP logs</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="web_log"
                                           id="web_log" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.WEB_LOG)]}/>
                                    <p>enable logs from the internal Tornado web server</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="web_username">
                                        <span class="component-title">HTTP username</span>
                                <span class="component-desc">
                                    <input type="text" name="web_username" id="web_username"
                                           value="${sickrage.srCore.srConfig.WEB_USERNAME}"
                                           class="form-control input-sm input300"
                                           autocapitalize="off"/>
                                    <p>set blank for no login</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="web_password">
                                        <span class="component-title">HTTP password</span>
                                <span class="component-desc">
                                    <input type="password" name="web_password" id="web_password"
                                           value="${sickrage.srCore.srConfig.WEB_PASSWORD}"
                                           class="form-control input-sm input300"
                                           autocapitalize="off"/>
                                    <p>blank = no authentication</span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="web_port">
                                        <span class="component-title">HTTP port</span>
                                <span class="component-desc">
                                    <input type="text" name="web_port" id="web_port"
                                           value="${sickrage.srCore.srConfig.WEB_PORT}"
                                           class="form-control input-sm input100"/>
                                    <p>web port to browse and access SickRage (default:8081)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="web_ipv6">
                                        <span class="component-title">Listen on IPv6</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="web_ipv6"
                                                   id="web_ipv6" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.WEB_IPV6)]}/>
                                            <p>attempt binding to any available IPv6 address</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="enable_https">
                                        <span class="component-title">Enable HTTPS</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="enable_https" class="enabler"
                                           id="enable_https" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.ENABLE_HTTPS)]}/>
                                    <p>enable access to the web interface using a HTTPS address</p>
                                </span>
                                    </label>
                                </div>
                                <div id="content_enable_https">
                                    <div class="field-pair">
                                        <label for="https_cert">
                                            <span class="component-title">HTTPS certificate</span>
                                    <span class="component-desc">
                                        <input type="text" name="https_cert" id="https_cert"
                                               value="${sickrage.srCore.srConfig.HTTPS_CERT}"
                                               class="form-control input-sm input300"
                                               autocapitalize="off"/>
                                        <div class="clear-left"><p>file name or path to HTTPS certificate</p></div>
                                    </span>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="https_key">
                                            <span class="component-title">HTTPS key</span>
                                    <span class="component-desc">
                                        <input type="text" name="https_key" id="https_key"
                                               value="${sickrage.srCore.srConfig.HTTPS_KEY}"
                                               class="form-control input-sm input300" autocapitalize="off"/>
                                        <div class="clear-left"><p>file name or path to HTTPS key</p></div>
                                    </span>
                                        </label>
                                    </div>
                                </div>

                                <div class="field-pair">
                                    <label for="handle_reverse_proxy">
                                        <span class="component-title">Reverse proxy headers</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="handle_reverse_proxy"
                                           id="handle_reverse_proxy" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.HANDLE_REVERSE_PROXY)]}/>
                                    <p>accept the following reverse proxy headers (advanced)...<br>(X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Proto)</p>
                                </span>
                                    </label>
                                </div>

                                <input type="submit" class="btn config_submitter" value="Save Changes"/>

                            </fieldset>

                        </div><!-- /component-group2 //-->
                    </div>


                    <div id="core-component-group3" class="component-group">

                        <div class="component-group">

                            <div class="component-group-desc">
                                <h3>Advanced Settings</h3>
                            </div>

                            <fieldset class="component-group-list">

                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">CPU throttling:</span>
                                <span class="component-desc">
                                    <select id="cpu_presets" name="cpu_preset" class="form-control input-sm">
                                        % for cur_preset in cpu_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.CPU_PRESET == cur_preset]}>${cur_preset.capitalize()}</option>
                                        % endfor
                                    </select>
                                    <span>Normal (default). High is lower and Low is higher CPU use</span>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Anonymous redirect</span>
                                <span class="component-desc">
                                    <input type="text" name="anon_redirect"
                                           value="${sickrage.srCore.srConfig.ANON_REDIRECT}"
                                           class="form-control input-sm input300" autocapitalize="off"/>
                                    <div class="clear-left"><p>backlink protection via anonymizer service, must end in "?"</p></div>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="debug">
                                        <span class="component-title">Enable debug</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="debug"
                                           id="debug" ${('', 'checked="checked"')[bool(sickrage.DEBUG)]}/>
                                    <p>Enable debug logs<p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="ssl_verify">
                                        <span class="component-title">Verify SSL Certs</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="ssl_verify"
                                               id="ssl_verify" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SSL_VERIFY)]}/>
                                        <p>Verify SSL Certificates (Disable this for broken SSL installs (Like QNAP)<p>
                                    </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="no_restart">
                                        <span class="component-title">No Restart</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="no_restart"
                                           id="no_restart" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.NO_RESTART)]}/>
                                    <p>Only shutdown when restarting SR.
                                    Only select this when you have external software restarting SR automatically when it stops (like FireDaemon)</p>
                                </span>

                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="encryption_version">
                                        <span class="component-title">Encrypt settings</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="encryption_version"
                                           id="encryption_version" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.ENCRYPTION_VERSION)]}/>
                                    <p>in the <code>${sickrage.CONFIG_FILE}</code> file.</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="calendar_unprotected">
                                        <span class="component-title">Unprotected calendar</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="calendar_unprotected"
                                           id="calendar_unprotected" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.CALENDAR_UNPROTECTED)]}/>
                                    <p>allow subscribing to the calendar without user and password.
                                    Some services like Google Calendar only work this way</p>
                                </span>

                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="calendar_icons">
                                        <span class="component-title">Google Calendar Icons</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="calendar_icons"
                                           id="calendar_icons" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.CALENDAR_ICONS)]}/>
                                    <p>show an icon next to exported calendar events in Google Calendar.</p>
                                </span>

                                    </label>
                                </div>

                                <div class="field-pair" style="display: none">
                                    <label for="google_link">
                                        <span class="component-title">Link Google Account</span>
                                        <span class="component-desc">
                                            <input class="btn btn-inline" type="button" id="google_link" value="Link">
                                            <p>link your google account to SiCKRAGE for advanced feature usage such as settings/database storage</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Proxy host</span>
                                <span class="component-desc">
                                    <input type="text" name="proxy_setting"
                                           value="${sickrage.srCore.srConfig.PROXY_SETTING}"
                                           class="form-control input-sm input300" autocapitalize="off"/>
                                    <div class="clear-left"><p>blank to disable or proxy to use when connecting to providers</p></div>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="proxy_indexers">
                                        <span class="component-title">Use proxy for indexers</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="proxy_indexers"
                                           id="proxy_indexers" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.PROXY_INDEXERS)]}/>
                                    <p>use proxy host for connecting to indexers (thetvdb)</p>
                                </span>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="skip_removed_files">
                                        <span class="component-title">Skip Remove Detection</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="skip_removed_files"
                                           id="skip_removed_files" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SKIP_REMOVED_FILES)]}/>
                                    <p>Skip detection of removed files. If disable it will set default deleted
                                        status</p>
                                 </span>
                                        <div class="clear-left">
                                            <span class="component-desc"><b>NOTE:</b> This may mean SickRage misses renames as well</span>
                                        </div>
                                    </label>
                                </div>

                                <div class="field-pair">
                                    <label for="ep_default_deleted_status">
                                        <span class="component-title">Default deleted episode status:</span>
                                    <span class="component-desc">
% if not sickrage.srCore.srConfig.SKIP_REMOVED_FILES:
    <select name="ep_default_deleted_status" id="ep_default_deleted_status" class="form-control input-sm">
        % for defStatus in [SKIPPED, IGNORED, ARCHIVED]:
            <option value="${defStatus}" ${('', 'selected="selected"')[int(sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS) == defStatus]}>${statusStrings[defStatus]}</option>
        % endfor
    </select>
% else:
    <select name="ep_default_deleted_status" id="ep_default_deleted_status" class="form-control input-sm"
            disabled="disabled">
        % for defStatus in [SKIPPED, IGNORED]:
            <option value="${defStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS == defStatus]}>${statusStrings[defStatus]}</option>
        % endfor
    </select>
                                        <input type="hidden" name="ep_default_deleted_status"
                                               value="${sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS}"/>
% endif
                                        <span>Define the status to be set for media file that has been deleted.</span>
                                    <div class="clear-left">
                                    <p> <b>NOTE:</b> Archived option will keep previous downloaded quality</p>
                                    <p>Example: Downloaded (1080p WEB-DL) ==> Archived (1080p WEB-DL)</p>
                                    </div>
                                </span>
                                    </label>
                                </div>

                                <input type="submit" class="btn config_submitter" value="Save Changes"/>
                            </fieldset>
                        </div>

                        % if sickrage.srCore.VERSIONUPDATER.updater.type == "git":
                        <%
                            git_branch = sickrage.srCore.VERSIONUPDATER.updater.remote_branches
                        %>

                            <div class="component-group">

                                <div class="component-group-desc">
                                    <h3>Git Settings</h3>
                                </div>
                                <fieldset class="component-group-list">

                                    <div class="field-pair">
                                        <label>
                                            <span class="component-title">Git Branch(s):</span>
                                <span class="component-desc">
                                    <select id="branchVersion"
                                            class="form-control form-control-inline input-sm pull-left">
                                        % if git_branch:
                                            % for cur_branch in git_branch:
                                                % if sickrage.DEVELOPER:
                                                    <option value="${cur_branch}" ${('', 'selected="selected"')[sickrage.srCore.VERSIONUPDATER.updater.current_branch == cur_branch]}>${cur_branch}</option>
                                                % elif cur_branch in ['master', 'develop']:
                                                    <option value="${cur_branch}" ${('', 'selected="selected"')[sickrage.srCore.VERSIONUPDATER.updater.current_branch == cur_branch]}>${cur_branch}</option>
                                                % endif
                                            % endfor
                                        % endif
                                    </select>
                                    % if not git_branch:
                                        <input class="btn btn-inline" style="margin-left: 6px;" type="button"
                                               id="branchCheckout" value="Checkout Branch" disabled>
                                    % else:
                                        <input class="btn btn-inline" style="margin-left: 6px;" type="button"
                                               id="branchCheckout" value="Checkout Branch">
                                    % endif
                                    % if not git_branch:
                                        <div class="clear-left"
                                             style="color:#FF0000"><p>Error: No branches found.</p></div>
                                    % else:
                                        <div class="clear-left"><p>select branch to use (restart required)</p></div>
                                    % endif
                                </span>
                                        </label>
                                    </div>

                                    <div class="field-pair">
                                        <label>
                                            <span class="component-title">Git executable path</span>
                                <span class="component-desc">
                                    <input type="text" name="git_path" value="${sickrage.srCore.srConfig.GIT_PATH}"
                                           class="form-control input-sm input300" autocapitalize="off"/>
                                    <div class="clear-left"><p>only needed if OS is unable to locate git from env</p></div>
                                </span>
                                        </label>
                                    </div>

                                    <div class="field-pair" hidden>
                                        <label for="git_reset">
                                            <span class="component-title">Git reset</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="git_reset"
                                           id="git_reset" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.GIT_RESET)]}/>
                                    <p>removes untracked files and performs a hard reset on git branch automatically to help resolve update issues</p>
                                </span>
                                        </label>
                                    </div>

                                    <div class="field-pair" hidden>
                                        <label for="git_autoissues">
                                            <span class="component-title">Git auto-issues submit</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="git_autoissues"
                                           id="git_autoissues" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.GIT_AUTOISSUES)]}
                                           disable/>
                                    <p>automatically submit bug/issue reports to our issue tracker when errors are logged</p>
                                </span>
                                        </label>
                                    </div>

                                    <input type="submit" class="btn config_submitter" value="Save Changes"/>
                                </fieldset>

                            </div>
                        % endif
                    </div><!-- /component-group3 //-->

                    <br>
                    <h6 class="pull-right"><b>All non-absolute folder locations are relative to <span
                            class="path">${sickrage.DATA_DIR}</span></b></h6>
                    <input type="submit" class="btn pull-left config_submitter button" value="Save Changes"/>
                </div><!-- /ui-components //-->

            </form>
        </div>
    </div>

    <div></div>
    <div id="login-dialog"></div><!-- login model dialog //-->
</%block>