<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveGeneral' %></%def>
<%!
    import datetime
    import locale

    from tornado._locale_data import LOCALE_NAMES

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickrage.core.helpers.srdatetime import srDateTime, date_presets, time_presets
    from sickrage.core.helpers import anon_url
    from sickrage.indexers import srIndexerApi
    from sickrage.metadata import GenericMetadata

    def lang_name(code):
        return LOCALE_NAMES.get(code, {}).get("name", "Unknown")
%>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Misc</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Interface</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane3">Advanced Settings</a></li>
</%block>
<%block name="pages">
    <% indexer = 0 %>
    % if sickrage.srCore.srConfig.INDEXER_DEFAULT:
        <% indexer = sickrage.srCore.srConfig.INDEXER_DEFAULT %>
    % endif
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Misc</h3>
                <p>Startup options. Indexer options. Log and show file locations.</p>
                <p><b>Some options may require a manual restart to take effect.</b></p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Default Indexer Language</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-flag"></span>
                            </div>
                            <select name="indexerDefaultLang" id="indexerDefaultLang"
                                    class="form-control form-control-inline bfh-languages"
                                    title="for adding shows and metadata providers"
                                    data-language=${sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE} data-available="${','.join(srIndexerApi().indexer().languages.keys())}">
                            </select>
                        </div>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Launch browser</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="launch_browser"
                               id="launch_browser" ${('', 'checked')[bool(sickrage.srCore.srConfig.LAUNCH_BROWSER)]}/>
                        <label for="launch_browser">open the SickRage home page on startup</label>
                    </div>
                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Initial page</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="fa fa-book"></span>
                            </div>
                            <select id="default_page" name="default_page" class="form-control"
                                    title="when launching SickRage interface">
                                <option value="home" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'home']}>
                                    Shows
                                </option>
                                <option value="schedule" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'schedule']}>
                                    Schedule
                                </option>
                                <option value="history" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'history']}>
                                    History
                                </option>
                                <option value="IRC" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DEFAULT_PAGE == 'IRC']}>
                                    IRC
                                </option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Daily show updates start time</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="showupdate_hour" id="showupdate_hour"
                                   value="${sickrage.srCore.srConfig.SHOWUPDATE_HOUR}"
                                   class="form-control"/>
                            <div class="input-group-addon">
                                24hr
                            </div>
                        </div>
                        <label for="showupdate_hour">
                            with information such as next air dates, show ended, etc.<br/>
                            Use 15 for 3pm, 4 for 4am etc. Anything over 23 or under 0 will be set to 0 (12am)
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Daily show updates stale shows</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="showupdate_stale"
                               id="showupdate_stale" ${('', 'checked')[bool(sickrage.srCore.srConfig.SHOWUPDATE_STALE)]}/>
                        <label for="showupdate_stale">should ended shows last updated less then 90 days get
                            updated and refreshed
                            automatically ?</label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Send to trash for actions</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="trash_remove_show"
                               id="trash_remove_show" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRASH_REMOVE_SHOW)]}/>
                        <label for="trash_remove_show">when using show "Remove" and delete files</label>
                        <br/>
                        <input type="checkbox" name="trash_rotate_logs"
                               id="trash_rotate_logs" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRASH_ROTATE_LOGS)]}/>
                        <label for="trash_rotate_logs">
                            on scheduled deletes of the oldest log files
                        </label>
                        <label>
                            <pre>selected actions use trash (recycle bin) instead of the default permanent delete</pre>
                        </label>
                    </div>
                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Number of Log files saved</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-file"></span>
                            </div>
                            <input name="log_nr" id="log_nr"
                                   value="${sickrage.srCore.srConfig.LOG_NR}"
                                   placeholder="default = 5"
                                   title="number of log files saved when rotating logs (REQUIRES RESTART)"
                                   class="form-control"/>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Size of Log files saved</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-file"></span>
                            </div>
                            <input name="log_size" id="log_size"
                                   value="${sickrage.srCore.srConfig.LOG_SIZE}"
                                   placeholder="default = 1048576 (1MB)"
                                   title="maximum size of a log file saved (REQUIRES RESTART)"
                                   class="form-control"/>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Default indexer for adding shows</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="fa fa-linode"></span>
                            </div>
                            <select id="indexer_default" name="indexer_default"
                                    title="default indexer selection when adding new shows"
                                    class="form-control">
                                <option value="0" ${('', 'selected="selected"')[indexer == 0]}>All
                                    Indexers
                                </option>
                                % for indexer in srIndexerApi().indexers:
                                    <option value="${indexer}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.INDEXER_DEFAULT == indexer]}>${srIndexerApi().indexers[indexer]}</option>
                                % endfor
                            </select>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Show indexer timeout</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="indexer_timeout" id="indexer_timeout"
                                   value="${sickrage.srCore.srConfig.INDEXER_TIMEOUT}"
                                   placeholder="default = 10"
                                   title="seconds of inactivity when finding new shows"
                                   class="form-control"/>
                            <div class="input-group-addon">
                                secs
                            </div>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Show root directories</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <%include file="../includes/root_dirs.mako"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>

            </fieldset>
        </div>

        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Updates</h3>
                <p>Options for software updates.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Check software updates</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="version_notify"
                               id="version_notify" ${('', 'checked')[bool(sickrage.srCore.srConfig.VERSION_NOTIFY)]}/>
                        <label for="version_notify">
                            and display notifications when updates are available. Checks are run on startup
                            and at the frequency set below*
                        </label>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Automatically update</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="auto_update"
                               id="auto_update" ${('', 'checked')[bool(sickrage.srCore.srConfig.AUTO_UPDATE)]}/>
                        <label for="auto_update">
                            fetch and install software updates.Updates are run on startupand in the
                            background at the frequency setbelow*
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Check the server every*</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <input name="update_frequency" id="update_frequency"
                                   value="${sickrage.srCore.srConfig.VERSION_UPDATER_FREQ}"
                                   placeholder="default = 12 (hours)"
                                   title="hours between software updates"
                                   class="form-control"/>
                            <div class="input-group-addon">
                                hours
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Notify on software update</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="notify_on_update"
                               id="notify_on_update" ${('', 'checked')[bool(sickrage.srCore.srConfig.NOTIFY_ON_UPDATE)]}/>
                        <label for="notify_on_update">send a message to all enabled notifiers when SickRage
                            has been updated</label>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>

            </fieldset>

        </div>
    </div><!-- /tab-pane1 //-->
    <div id="core-tab-pane2" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>User Interface</h3>
                <p>Options for visual appearance.</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Interface Language:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="fa fa-language"></span>
                                    </div>
                                    <select id="gui_language" name="gui_language" class="form-control">
                                        <option value="" ${('', 'selected="selected"')[sickrage.srCore.srConfig.GUI_LANG == ""]}>System Language</option>
                                        % for lang in sickrage.srCore.LANGUAGES:
                                            <option value="${lang}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.GUI_LANG == lang]}>${lang_name(lang)}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <label for="gui_language" class="red-text">
                                    for appearance to take effect, save then refresh your browser
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Display theme:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="fa fa-themeisle"></span>
                            </div>
                            <select id="theme_name" name="theme_name" class="form-control"
                                    title="for appearance to take effect, save then refresh your browser">
                                <option value="dark" ${('', 'selected="selected"')[sickrage.srCore.srConfig.THEME_NAME == 'dark']}>
                                    Dark
                                </option>
                                <option value="light" ${('', 'selected="selected"')[sickrage.srCore.srConfig.THEME_NAME == 'light']}>
                                    Light
                                </option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Show all seasons</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="display_all_seasons"
                               id="display_all_seasons" ${('', 'checked')[bool(sickrage.srCore.srConfig.DISPLAY_ALL_SEASONS)]}>
                        <label for="display_all_seasons">
                            on the show summary page
                        </label>
                    </div>

                </div>
                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Sort with "The", "A", "An"</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="sort_article"
                               id="sort_article" ${('', 'checked')[bool(sickrage.srCore.srConfig.SORT_ARTICLE)]}/>
                        <label for="sort_article">include articles ("The", "A", "An") when sorting show
                            lists</label>
                    </div>

                </div>
                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Filter Row</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="filter_row"
                               id="filter_row" ${('', 'checked')[bool(sickrage.srCore.srConfig.FILTER_ROW)]}/>
                        <label for="filter_row">
                            Add a filter row to the show display on the home page
                        </label>
                    </div>

                </div>
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Missed episodes range</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar"></span>
                            </div>
                            <input type="number" step="1" min="7" name="coming_eps_missed_range"
                                   id="coming_eps_missed_range"
                                   value="${sickrage.srCore.srConfig.COMING_EPS_MISSED_RANGE}"
                                   placeholder="# of days"
                                   title="Set the range in days of the missed episodes in the Schedule page"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>
                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Display fuzzy dates</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="fuzzy_dating"
                               id="fuzzy_dating"
                               class="viewIf datePresets" ${('', 'checked')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}/>
                        <label
                                for="fuzzy_dating">move absolute dates into tooltips and display e.g. "Last
                            Thu", "On Tue"</label>
                    </div>

                </div>
                <div class="row field-pair show_if_fuzzy_dating ${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Trim zero padding</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="trim_zero"
                               id="trim_zero" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRIM_ZERO)]}/>
                        <label for="trim_zero">
                            remove the leading number "0" shown on hour of day, and date of month
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Date style:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select class="form-control ${(' metadataDiv', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                id="date_presets${('_na', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                name="date_preset${('_na', '')[bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                            % for cur_preset in date_presets:
                                <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == cur_preset or ("%x" == sickrage.srCore.srConfig.DATE_PRESET and cur_preset == '%a, %b %d, %Y')]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset).decode(sickrage.srCore.SYS_ENCODING)}</option>
                            % endfor
                        </select>
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar"></span>
                            </div>
                            <select class="form-control ${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                    id="date_presets${(' metadataDiv', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}"
                                    name="date_preset${('_na', '')[not bool(sickrage.srCore.srConfig.FUZZY_DATING)]}">
                                <option value="%x" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == '%x']}>
                                    Use System Default
                                </option>
                                % for cur_preset in date_presets:
                                    <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.DATE_PRESET == cur_preset]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset).decode(sickrage.srCore.SYS_ENCODING)}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Time style:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-time"></span>
                            </div>
                            <select id="time_presets" name="time_preset" class="form-control"
                                    title="seconds are only shown on the History page">
                                % for cur_preset in time_presets:
                                    <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TIME_PRESET_W_SECONDS == cur_preset]}>${srDateTime.now().srftime(show_seconds=True, t_preset=cur_preset)}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Timezone:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="radio" name="timezone_display" id="local"
                               value="local" ${('', 'checked')[sickrage.srCore.srConfig.TIMEZONE_DISPLAY == "local"]} />
                        <label for="local">Local</label>
                        <br/>
                        <input type="radio" name="timezone_display" id="network"
                               value="network" ${('', 'checked')[sickrage.srCore.srConfig.TIMEZONE_DISPLAY == "network"]} />
                        <label for="network">Network</label>
                        <div class="row">
                            <div class="col-md-12">
                                display dates and times in either your timezone or the shows network
                                timezone<br/>
                                <b>Note:</b> Use local timezone to start searching for episodes minutes after
                                show ends (depends on your dailysearch frequency)
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Download url</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-globe"></span>
                            </div>
                            <input name="download_url" id="download_url" class="form-control"
                                   value="${sickrage.srCore.srConfig.DOWNLOAD_URL}"
                                   title="URL where the shows can be downloaded."
                                   autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Show fanart in the background</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="fanart_background"

                               id="fanart_background" ${('', 'checked')[bool(sickrage.srCore.srConfig.FANART_BACKGROUND)]}>
                        <label for="fanart_background">
                            on the show summary page
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Fanart transparency</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-transfer"></span>
                            </div>
                            <input type="number" step="0.1" min="0.1" max="1.0"
                                   name="fanart_background_opacity" id="fanart_background_opacity"
                                   value="${sickrage.srCore.srConfig.FANART_BACKGROUND_OPACITY}"
                                   title="transparency of the fanart in the background"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>
            </fieldset>
        </div><!-- /User interface tab-pane -->

        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Web Interface</h3>
                <p>It is recommended that you enable a username and password to secure SickRage from
                    being tampered with remotely.</p>
                <p><b>These options require a manual restart to take effect.</b></p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">API key</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-cloud"></span>
                                    </div>
                                    <input name="api_key" id="api_key"
                                           value="${sickrage.srCore.srConfig.API_KEY}"
                                           class="form-control"/>
                                    <div class="input-group-addon">
                                        <input class="button" type="button" id="generate_new_apikey"
                                               value="Generate">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <label for="api_key">
                                    used to give 3rd party programs limited access to SiCKRAGE you can try all the
                                    features of the API <a href="${srWebRoot}/apibuilder/">here</a>
                                </label>
                            </div>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">HTTP logs</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="web_log"
                               id="web_log" ${('', 'checked')[bool(sickrage.srCore.srConfig.WEB_LOG)]}/>
                        <label for="web_log">enable logs from the internal Tornado web server</label>
                    </div>
                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">HTTP username</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-user"></span>
                            </div>
                            <input name="web_username" id="web_username"
                                   value="${sickrage.srCore.srConfig.WEB_USERNAME}"
                                   title="WebUI username"
                                   placeholder="blank = no authentication"
                                   class="form-control"
                                   autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">HTTP password</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-lock"></span>
                            </div>
                            <input type="password" name="web_password" id="web_password"
                                   value="${sickrage.srCore.srConfig.WEB_PASSWORD}"
                                   title="WebUI password"
                                   placeholder="blank = no authentication"
                                   class="form-control"
                                   autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">HTTP port</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-globe"></span>
                            </div>
                            <input name="web_port" id="web_port"
                                   value="${sickrage.srCore.srConfig.WEB_PORT}"
                                   placeholder="8081"
                                   title="web port to browse and access WebUI"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Listen on IPv6</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="web_ipv6"
                               id="web_ipv6" ${('', 'checked')[bool(sickrage.srCore.srConfig.WEB_IPV6)]}/>
                        <label for="web_ipv6">attempt binding to any available IPv6 address</label>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable HTTPS</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="enable_https" class="enabler"
                               id="enable_https" ${('', 'checked')[bool(sickrage.srCore.srConfig.ENABLE_HTTPS)]}/>
                        <label for="enable_https">
                            enable access to the web interface using a HTTPS address
                        </label>
                    </div>

                </div>
                <div id="content_enable_https">
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">HTTPS certificate</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input name="https_cert" id="https_cert"
                                           value="${sickrage.srCore.srConfig.HTTPS_CERT}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="https_cert">
                                        file name or path to HTTPS certificate
                                    </label>
                                </div>
                            </div>
                        </div>

                    </div>
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">HTTPS key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input name="https_key" id="https_key"
                                           value="${sickrage.srCore.srConfig.HTTPS_KEY}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="https_key">file name or path to HTTPS key</label>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Reverse proxy headers</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="handle_reverse_proxy"
                               id="handle_reverse_proxy" ${('', 'checked')[bool(sickrage.srCore.srConfig.HANDLE_REVERSE_PROXY)]}/>
                        <label for="handle_reverse_proxy">
                            accept the following reverse proxy headers (advanced)...<br>
                            (X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Proto)
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Notify on login</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="notify_on_login"
                               id="notify_on_login" ${('', 'checked')[bool(sickrage.srCore.srConfig.NOTIFY_ON_LOGIN)]}/>
                        <label for="notify_on_login">
                            send a message to all enabled notifiers when someone logs into SiCKRAGE from a public IP
                            address
                        </label>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>


            </fieldset>

        </div><!-- /tab-pane2 //-->
    </div><!-- /tab-pane2 //-->
    <div id="core-tab-pane3" class="tab-pane fade">

        <div class="row tab-pane">

            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Advanced Settings</h3>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">CPU throttling:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="fa fa-microchip"></span>
                            </div>
                            <select id="cpu_presets" name="cpu_preset" class="form-control"
                                    title="Normal (default). High is lower and Low is higher CPU use">
                                % for cur_preset in cpu_presets:
                                    <option value="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.CPU_PRESET == cur_preset]}>${cur_preset.capitalize()}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Anonymous redirect</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-globe"></span>
                            </div>
                            <input id="anon_redirect" name="anon_redirect"
                                   value="${sickrage.srCore.srConfig.ANON_REDIRECT}"
                                   title="backlink protection via anonymizer service, must end in ?"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable debug</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="debug"
                               id="debug" ${('', 'checked')[bool(sickrage.srCore.srConfig.DEBUG)]}/>
                        <label for="debug">
                            Enable debug logs
                        </label>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Verify SSL Certs</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="ssl_verify"
                               id="ssl_verify" ${('', 'checked')[bool(sickrage.srCore.srConfig.SSL_VERIFY)]}/>
                        <label for="ssl_verify">
                            Verify SSL Certificates (Disable this for broken SSL installs (Like QNAP)
                        </label>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">No Restart</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="no_restart"
                               title="Only select this when you have external software restarting SR automatically when it stops (like FireDaemon)"
                               id="no_restart" ${('', 'checked')[bool(sickrage.srCore.srConfig.NO_RESTART)]}/>
                        <label for="no_restart">
                            Shutdown SiCKRAGE on restarts (external service must restart SiCKRAGE on its own).
                        </label>
                    </div>


                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Encrypt settings</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="encryption_version"
                               id="encryption_version" ${('', 'checked')[bool(sickrage.srCore.srConfig.ENCRYPTION_VERSION)]}/>
                        <label for="encryption_version">
                            in the <code>${sickrage.CONFIG_FILE}</code> file.
                        </label>
                    </div>

                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Unprotected calendar</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="calendar_unprotected"
                               id="calendar_unprotected" ${('', 'checked')[bool(sickrage.srCore.srConfig.CALENDAR_UNPROTECTED)]}/>
                        <label for="calendar_unprotected">
                            allow subscribing to the calendar without user and password.
                            Some services like Google Calendar only work this way
                        </label>
                    </div>


                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Google Calendar Icons</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="calendar_icons"
                               id="calendar_icons" ${('', 'checked')[bool(sickrage.srCore.srConfig.CALENDAR_ICONS)]}/>
                        <label for="calendar_icons">
                            show an icon next to exported calendar events in Google Calendar.
                        </label>
                    </div>


                </div>

                <div class="row field-pair" style="display: none">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Link Google Account</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input class="btn btn-inline" type="button" id="google_link" value="Link">
                        <label for="google_link">
                            link your google account to SiCKRAGE for advanced feature usage such as
                            settings/database storage
                        </label>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Proxy host</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-globe"></span>
                            </div>
                            <input id="proxy_setting" name="proxy_setting"
                                   value="${sickrage.srCore.srConfig.PROXY_SETTING}"
                                   title="Proxy SiCKRAGE connections"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Use proxy for indexers</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="proxy_indexers"
                               id="proxy_indexers" ${('', 'checked')[bool(sickrage.srCore.srConfig.PROXY_INDEXERS)]}/>
                        <label for="proxy_indexers">
                            use proxy host for connecting to indexers (thetvdb)
                        </label>
                    </div>
                </div>

                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Skip Remove Detection</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" name="skip_removed_files"
                               id="skip_removed_files" ${('', 'checked')[bool(sickrage.srCore.srConfig.SKIP_REMOVED_FILES)]}/>
                        <label for="skip_removed_files">
                            Skip detection of removed files. If disable it will set default deleted status<br/>
                            <b>NOTE:</b> This may mean SickRage misses renames as well
                        </label>
                    </div>

                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Default deleted episode status:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-erase"></span>
                                    </div>
                                    % if not sickrage.srCore.srConfig.SKIP_REMOVED_FILES:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status"
                                                class="form-control">
                                            % for defStatus in [SKIPPED, IGNORED, ARCHIVED]:
                                                <option value="${defStatus}" ${('', 'selected="selected"')[int(sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS) == defStatus]}>${statusStrings[defStatus]}</option>
                                            % endfor
                                        </select>
                                    % else:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status"
                                                class="form-control" disabled="disabled">
                                            % for defStatus in [SKIPPED, IGNORED]:
                                                <option value="${defStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS == defStatus]}>${statusStrings[defStatus]}</option>
                                            % endfor
                                        </select>
                                        <input type="hidden" name="ep_default_deleted_status"
                                               value="${sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS}"/>
                                    % endif
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <label for="ep_default_deleted_status">
                                    Define the status to be set for media file that has been deleted.<br/>
                                    <b>NOTE:</b> Archived option will keep previous downloaded quality<br/>
                                    Example: Downloaded (1080p WEB-DL) ==> Archived (1080p WEB-DL)
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">PIP executable path</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-file"></span>
                            </div>
                            <input id="pip_path" name="pip_path"
                                   value="${sickrage.srCore.srConfig.PIP_PATH}"
                                   placeholder="ex: /path/to/pip"
                                   title="only needed if OS is unable to locate pip from env"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>

            </fieldset>
        </div>

        % if sickrage.srCore.VERSIONUPDATER.updater.type == "git":
        <%
            git_branch = sickrage.srCore.VERSIONUPDATER.updater.remote_branches
        %>

            <div class="row tab-pane">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                    <h3>Git Settings</h3>
                </div>
                <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Git Branch(s):</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-git"></span>
                                </div>
                                <select id="branchVersion"
                                        class="form-control form-control-inline pull-left"
                                        title="GIT Branch Version">
                                    % if git_branch:
                                        % for cur_branch in git_branch:
                                            % if sickrage.srCore.srConfig.DEVELOPER:
                                                <option value="${cur_branch}" ${('', 'selected="selected"')[sickrage.srCore.VERSIONUPDATER.updater.current_branch == cur_branch]}>${cur_branch}</option>
                                            % elif cur_branch in ['master', 'develop']:
                                                <option value="${cur_branch}" ${('', 'selected="selected"')[sickrage.srCore.VERSIONUPDATER.updater.current_branch == cur_branch]}>${cur_branch}</option>
                                            % endif
                                        % endfor
                                    % endif
                                </select>
                            </div>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    % if not git_branch:
                                        <input class="btn btn-inline" style="margin-left: 6px;"
                                               type="button"
                                               id="branchCheckout" value="Checkout Branch" disabled>
                                        <label for="branchCheckout">Error: No branches found.</label>>
                                    % else:
                                        <input class="btn btn-inline" style="margin-left: 6px;"
                                               type="button"
                                               id="branchCheckout" value="Checkout Branch">
                                        <label for="branchCheckout">select branch to use (restart required)</label>
                                    % endif
                                </div>
                            </div>

                        </div>

                    </div>

                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">GIT executable path</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-file"></span>
                                </div>
                                <input id="git_path" name="git_path"
                                       value="${sickrage.srCore.srConfig.GIT_PATH}"
                                       placeholder="ex: /path/to/git"
                                       title="only needed if OS is unable to locate git from env"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>

                    <div class="row field-pair" hidden>

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Git reset</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="git_reset"
                                   id="git_reset" ${('', 'checked')[bool(sickrage.srCore.srConfig.GIT_RESET)]}/>
                            <label for="git_reset">
                                removes untracked files and performs a hard reset on git branch
                                automatically to help resolve update issues
                            </label>
                        </div>

                    </div>

                    <div class="row field-pair" hidden>

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Git auto-issues submit</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="git_autoissues"
                                   id="git_autoissues" ${('', 'checked')[bool(sickrage.srCore.srConfig.GIT_AUTOISSUES)]}
                                   disabled="disabled"/>
                            <label for="git_autoissues">
                                automatically submit bug/issue reports to our issue tracker when errors are
                                logged
                            </label>
                        </div>

                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input type="submit" class="btn config_submitter" value="Save Changes"/>
                        </div>
                    </div>

                </fieldset>

            </div>
        % endif
    </div><!-- /tab-pane3 //-->
</%block>