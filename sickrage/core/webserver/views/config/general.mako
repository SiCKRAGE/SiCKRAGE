c<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveGeneral' %></%def>
<%!
    import datetime
    import locale
    import tornado.locale

    from oauthlib.oauth2 import MissingTokenError

    import sickrage
    from sickrage.core.common import Quality, EpisodeStatus
    from sickrage.core.helpers.srdatetime import SRDateTime, date_presets, time_presets
    from sickrage.core.helpers import anon_url
    from sickrage.metadata_providers import MetadataProvider
    from sickrage.core.enums import DefaultHomePage, UITheme, TimezoneDisplay,  SeriesProviderID, CpuPreset
%>
<%block name="menus">
    <li class="nav-item px-1">
        <a class="nav-link" data-toggle="tab" href="#misc">${_('Misc')}</a>
    </li>
    <li class="nav-item px-1">
        <a class="nav-link" data-toggle="tab" href="#interface">${_('Interface')}</a>
    </li>
    <li class="nav-item px-1">
        <a class="nav-link" data-toggle="tab" href="#network-settings">${_('Network')}</a>
    </li>
    <li class="nav-item px-1">
        <a class="nav-link" data-toggle="tab" href="#advanced-settings">${_('Advanced Settings')}</a>
    </li>
</%block>
<%block name="pages">
    <div id="misc" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Misc')}</h3>
                <small class="form-text text-muted">
                    ${_('Startup options. Series provider options. Log and show file locations.')}
                    <p><b>${_('Some options may require a manual restart to take effect.')}</b></p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Default Series Provider Language')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-language"></span>
                                </span>
                            </div>
                            <select name="series_provider_default_language" id="series_provider_default_language" class="form-control"
                                    title="${_('Choose language')}">
                                % for language in sickrage.app.series_providers[sickrage.app.config.general.series_provider_default].languages():
                                    <option value="${language['abbreviation']}" ${('', 'selected')[sickrage.app.config.general.series_provider_default_language == language['abbreviation']]}>
                                        ${language['englishname']}
                                    </option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Launch browser')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="launch_browser">
                            <input type="checkbox" class="toggle color-primary is-material" name="launch_browser"
                                   id="launch_browser" ${('', 'checked')[bool(sickrage.app.config.general.launch_browser)]}/>
                            ${_('open the SickRage home page on startup')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Initial page')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-book"></span>
                                </span>
                            </div>
                            <select id="default_page" name="default_page" class="form-control"
                                    title="${_('when launching SickRage interface')}">
                                % for item in DefaultHomePage:
                                    <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.default_page == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Daily show updates start time')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="show_update_hour" id="show_update_hour"
                                   value="${sickrage.app.config.general.show_update_hour}"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    24hr
                                </span>
                            </div>
                        </div>
                        <label class="text-info" for="show_update_hour">
                            ${_('with information such as next air dates, show ended, etc.')}<br/>
                            ${_('Use 15 for 3pm, 4 for 4am etc. Anything over 23 or under 0 will be set to 0 (12am)')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Daily show updates stale shows')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="show_update_stale">
                            <input type="checkbox" class="toggle color-primary is-material" name="show_update_stale"
                                   id="show_update_stale" ${('', 'checked')[bool(sickrage.app.config.general.show_update_stale)]}/>
                            ${_('should ended shows last updated less then 90 days get updated and refreshed automatically ?')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Send to trash for actions')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="trash_remove_show">
                            <input type="checkbox" class="toggle color-primary is-material" name="trash_remove_show"
                                   id="trash_remove_show" ${('', 'checked')[bool(sickrage.app.config.general.trash_remove_show)]}/>
                            ${_('when using show "Remove" and delete files')}
                        </label>
                        <br/>
                        <label for="trash_rotate_logs">
                            <input type="checkbox" class="toggle color-primary is-material" name="trash_rotate_logs"
                                   id="trash_rotate_logs" ${('', 'checked')[bool(sickrage.app.config.general.trash_rotate_logs)]}/>
                            ${_('on scheduled deletes of the oldest log files')}
                        </label>
                        <br/>
                        <div class="text-info">
                            ${_('selected actions use trash (recycle bin) instead of the default permanent delete')}
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Number of Log files saved')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-file"></span>
                                </span>
                            </div>
                            <input name="log_nr" id="log_nr"
                                   value="${sickrage.app.config.general.log_nr}"
                                   placeholder="${_('default = 5')}"
                                   title="number of log files saved when rotating logs (REQUIRES RESTART)"
                                   class="form-control"/>
                        </div>
                    </div>

                </div>

                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Size of Log files saved')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-file"></span>
                                </span>
                            </div>
                            <input name="log_size" id="log_size"
                                   value="${sickrage.app.config.general.log_size}"
                                   placeholder="${_('default = 1048576 (1MB)')}"
                                   title="maximum size of a log file saved (REQUIRES RESTART)"
                                   class="form-control"/>
                        </div>
                    </div>

                </div>

                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Default series provider for adding shows')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-list"></span>
                                </span>
                            </div>
                            <select id="series_provider_default" name="series_provider_default"
                                    title="default series provider selection when adding new shows"
                                    class="form-control">
                                % for item in SeriesProviderID:
                                    <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.series_provider_default == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>

                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Series provider timeout')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="series_provider_timeout" id="series_provider_timeout"
                                   value="${sickrage.app.config.general.series_provider_timeout}"
                                   placeholder="${_('default = 10')}"
                                   title="seconds of inactivity when finding new shows"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    secs
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Show root directories')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <%include file="../includes/root_dirs.mako"/>
                    </div>
                </div>

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>

            </fieldset>
        </div>

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Updates')}</h3>
                <small class="form-text text-muted">
                    ${_('Options for software updates.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">

                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Check software updates')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="version_notify">
                            <input type="checkbox" class="toggle color-primary is-material" name="version_notify"
                                   id="version_notify" ${('', 'checked')[bool(sickrage.app.config.general.version_notify)]}/>
                            ${_('and display notifications when updates are available. Checks are run on startup and at '
                            'the frequency set below')}
                        </label>
                    </div>

                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Automatically update')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="auto_update">
                            <input type="checkbox" class="toggle color-primary is-material" name="auto_update"
                                   id="auto_update" ${('', 'checked')[bool(sickrage.app.config.general.auto_update)]}/>
                            ${_('fetch and install software updates.Updates are run on startupand in the background at '
                            'the frequency setbelow')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Check the server every')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="update_frequency" id="update_frequency"
                                   value="${sickrage.app.config.general.version_updater_freq}"
                                   placeholder="${_('default = 12 (hours)')}"
                                   title="hours between software updates"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    hours
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Notify on software update')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="notify_on_update">
                            <input type="checkbox" class="toggle color-primary is-material" name="notify_on_update"
                                   id="notify_on_update" ${('', 'checked')[bool(sickrage.app.config.general.notify_on_update)]}/>
                            ${_('send a message to all enabled notification providers when SiCKRAGE has been updated')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Backup on software update')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="backup_on_update">
                            <input type="checkbox" class="toggle color-primary is-material" name="backup_on_update"
                                   id="backup_on_update" ${('', 'checked')[bool(sickrage.app.config.general.backup_on_update)]}/>
                            ${_('backup SiCKRAGE config and databases before performing updates')}
                        </label>
                    </div>
                </div>

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>

            </fieldset>
        </div>
    </div><!-- misc.tab-pane1 -->

    <div id="interface" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('User Interface')}</h3>
                <small class="form-text text-muted">
                    ${_('Options for visual appearance.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Interface Language')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-language"></span>
                                        </span>
                                    </div>
                                    <select id="gui_language" name="gui_language" class="form-control">
                                        <option value="" ${('', 'selected')[sickrage.app.config.gui.gui_lang == ""]}>
                                            ${_('System Language')}
                                        </option>
                                        % for lang in sickrage.app.languages:
                                            <option value="${lang}" ${('', 'selected')[sickrage.app.config.gui.gui_lang == lang]}>${tornado.locale.get(lang).name}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="gui_language" class="text-info">
                                    ${_('for appearance to take effect, save then refresh your browser')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Display theme')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fab fa-themeisle"></span>
                                </span>
                            </div>
                            <select id="theme_name" name="theme_name" class="form-control"
                                    title="for appearance to take effect, save then refresh your browser">
                                % for item in UITheme:
                                    <option value="${item.name}" ${('', 'selected')[sickrage.app.config.gui.theme_name == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Show all seasons')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="display_all_seasons">
                            <input type="checkbox" class="toggle color-primary is-material" name="display_all_seasons"
                                   id="display_all_seasons" ${('', 'checked')[bool(sickrage.app.config.general.display_all_seasons)]}>
                            ${_('on the show summary page')}
                        </label>
                    </div>

                </div>
                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Sort with "The", "A", "An"')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="sort_article">
                            <input type="checkbox" class="toggle color-primary is-material" name="sort_article"
                                   id="sort_article" ${('', 'checked')[bool(sickrage.app.config.general.sort_article)]}/>
                            ${_('include articles ("The", "A", "An") when sorting show lists')}
                        </label>
                    </div>

                </div>
                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Filter form-row')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="filter_row">
                            <input type="checkbox" class="toggle color-primary is-material" name="filter_row"
                                   id="filter_row" ${('', 'checked')[bool(sickrage.app.config.gui.filter_row)]}/>
                            ${_('Add a filter form-row to the show display on the home page')}
                        </label>
                    </div>

                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Missed episodes range')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-calendar"></span>
                                </span>
                            </div>
                            <input type="number" step="1" min="7" name="coming_eps_missed_range"
                                   id="coming_eps_missed_range"
                                   value="${sickrage.app.config.gui.coming_eps_missed_range}"
                                   placeholder="${_('# of days')}"
                                   title="Set the range in days of the missed episodes in the Schedule page"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Display fuzzy dates')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="fuzzy_dating">
                            <input type="checkbox" class="toggle color-primary is-material" name="fuzzy_dating"
                                   id="fuzzy_dating"
                                   class="viewIf datePresets" ${('', 'checked')[bool(sickrage.app.config.gui.fuzzy_dating)]}/>
                            ${_('move absolute dates into tooltips and display e.g. "Last Thu", "On Tue"')}
                        </label>
                    </div>

                </div>
                <div class="form-row form-group show_if_fuzzy_dating ${(' metadataDiv', '')[not bool(sickrage.app.config.gui.fuzzy_dating)]}">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Trim zero padding')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="trim_zero">
                            <input type="checkbox" class="toggle color-primary is-material" name="trim_zero"
                                   id="trim_zero" ${('', 'checked')[bool(sickrage.app.config.gui.trim_zero)]}/>
                            ${_('remove the leading number "0" shown on hour of day, and date of month')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Date style')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-calendar"></span>
                                </span>
                            </div>
                            <select class="form-control ${(' metadataDiv', '')[not bool(sickrage.app.config.gui.fuzzy_dating)]}"
                                    id="date_presets${(' metadataDiv', '')[not bool(sickrage.app.config.gui.fuzzy_dating)]}"
                                    name="date_preset${('_na', '')[not bool(sickrage.app.config.gui.fuzzy_dating)]}">
                                <option value="%x" ${('', 'selected')[sickrage.app.config.gui.date_preset == '%x']}>
                                    ${_('Use System Default')}
                                </option>
                                % for cur_preset in date_presets:
                                    <option value="${cur_preset}" ${('', 'selected')[sickrage.app.config.gui.date_preset == cur_preset]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset)}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Time style')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <select id="time_presets" name="time_preset" class="form-control"
                                    title="seconds are only shown on the History page">
                                % for cur_preset in time_presets:
                                    <option value="${cur_preset}" ${('', 'selected')[sickrage.app.config.gui.time_preset_w_seconds == cur_preset]}>${SRDateTime(datetime.datetime.now()).srftime(show_seconds=True, t_preset=cur_preset)}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Timezone')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <input type="radio" name="timezone_display" id="local"
                               value="${TimezoneDisplay.LOCAL.name}" ${('', 'checked')[sickrage.app.config.gui.timezone_display == TimezoneDisplay.LOCAL]} />
                        <label for="local">${TimezoneDisplay.LOCAL.display_name}</label>
                        <br/>
                        <input type="radio" name="timezone_display" id="network"
                               value="${TimezoneDisplay.NETWORK.name}" ${('', 'checked')[sickrage.app.config.gui.timezone_display == TimezoneDisplay.NETWORK]} />
                        <label for="network">${TimezoneDisplay.NETWORK.display_name}</label>
                        <div class="form-row">
                            <div class="col-md-12 text-info">
                                ${_('display dates and times in either your timezone or the shows network timezone')}
                                <br/>
                                <b>${_('NOTE:')}</b> ${_('Use local timezone to start searching for episodes minutes after show ends (depends on your dailysearch frequency)')}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Download url')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-globe"></span>
                                </span>
                            </div>
                            <input name="download_url" id="download_url" class="form-control"
                                   value="${sickrage.app.config.general.download_url}"
                                   title="URL where the shows can be downloaded."
                                   autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Show fanart in the background')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="fanart_background">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="fanart_background"

                                   id="fanart_background" ${('', 'checked')[bool(sickrage.app.config.gui.fanart_background)]}>
                            ${_('on the show summary page')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Fanart transparency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-exchange-alt"></span>
                                </span>
                            </div>
                            <input type="number" step="0.1" min="0.1" max="1.0"
                                   name="fanart_background_opacity" id="fanart_background_opacity"
                                   value="${sickrage.app.config.gui.fanart_background_opacity}"
                                   title="transparency of the fanart in the background"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div><!-- User interface section -->
    </div><!-- interface.tab-pane -->

    <div id="network-settings" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Network')}</h3>
                <small class="form-text text-muted">
                    ${_('It is recommended that you enable a username and password to secure SiCKRAGE from being tampered with remotely.')}
                    <p><b>${_('These options require a manual restart to take effect.')}</b></p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div id="content_enable_upnp">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('HTTP public port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-globe"></span>
                                            </span>
                                        </div>
                                        <input name="web_external_port" id="web_external_port"
                                               value="${sickrage.app.config.general.web_external_port}"
                                               title="external web port to remotely access SiCKRAGE"
                                               class="form-control"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label class="text-info" for="web_external_port">
                                        ${_('used by UPnP to setup a remote port forwarding to remotely access SiCKRAGE over a public external IP address')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('HTTP private port')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-globe"></span>
                                        </span>
                                    </div>
                                    <input name="web_port" id="web_port"
                                           value="${sickrage.app.config.general.web_port}"
                                           placeholder="${_('8081')}"
                                           title="${_('Web port to browse and access WebUI')}"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="web_port">
                                    ${_('used to access SiCKRAGE over a private internal IP address')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('HTTP web root')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-globe"></span>
                                        </span>
                                    </div>
                                    <input name="web_root" id="web_root"
                                           value="${sickrage.app.config.general.web_root}"
                                           placeholder="${'/'}"
                                           title="${_('Web root used in URL to browse and access WebUI')}"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="web_root">
                                    ${_('used in URL to access SiCKRAGE WebUI, DO NOT include a trailing slash at end.')}
                                    <br>
                                    <b>${_('this option require a manual restart to take effect.')}</b>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Application API key')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-cloud"></span>
                                        </span>
                                    </div>
                                    <input name="api_key" id="api_key"
                                           value="${sickrage.app.config.general.api_v1_key}"
                                           class="form-control"/>
                                    <div class="input-group-append">
                                        <span class="btn" id="generate_new_apikey">
                                            ${_('Generate')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="api_key">
                                    ${_('used to give 3rd party programs limited access to SiCKRAGE you can try all the features of the API')}
                                    <a href="${srWebRoot}/apibuilder/">${_('here')}</a>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Web Authentication Method')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-cloud"></span>
                                    </span>
                            </div>
                            <select id="web_auth_method" name="web_auth_method" class="form-control">
                                <option value="sso_auth" ${('', 'selected="selected"')[sickrage.app.config.general.sso_auth_enabled]}>
                                    SSO Authentication
                                </option>
                                <option value="local_auth" ${('', 'selected="selected"')[sickrage.app.config.general.local_auth_enabled]}>
                                    Local Authentication
                                </option>
                            </select>
                        </div>
                    </div>
                </div>

                <div id="content_use_local_auth">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Web Username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-user"></span>
                                        </span>
                                </div>
                                <input name="web_username" id="web_username"
                                       value="${sickrage.app.config.user.username}"
                                       class="form-control"/>
                                <div class="invalid-tooltip">
                                    Please fill in a web username.
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Web Password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-key"></span>
                                        </span>
                                </div>
                                <input name="web_password" id="web_password"
                                       value="${sickrage.app.config.user.password}"
                                       class="form-control"
                                       type="password"/>
                                <div class="invalid-tooltip">
                                    Please fill in a web password.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Whitelisted IP Authentication')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="ip_whitelist_localhost_enabled"
                                       id="ip_whitelist_localhost_enabled" ${('', 'checked')[bool(sickrage.app.config.general.ip_whitelist_localhost_enabled)]}/>
                                ${_('bypass web authentication for clients on localhost')}
                                <br/>
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="ip_whitelist_enabled"
                                       id="ip_whitelist_enabled" ${('', 'checked')[bool(sickrage.app.config.general.ip_whitelist_enabled)]}/>
                                ${_('bypass web authentication for clients in whitelisted IP list')}
                                <br/>
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-cloud"></span>
                                        </span>
                                    </div>
                                    <input name="ip_whitelist" id="ip_whitelist"
                                           value="${sickrage.app.config.general.ip_whitelist}"
                                           title="${_('List of IP addresses and networks that are allowed without auth')}"
                                           placeholder="ex: 192.168.1.50 or 192.168.1.0/24"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="api_key">
                                    ${_('comma separated list of IP addresses or IP/netmask entries for networks that are allowed to bypass web authorization.')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('HTTP logs')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="web_log">
                            <input type="checkbox" class="toggle color-primary is-material" name="web_log"
                                   id="web_log" ${('', 'checked')[bool(sickrage.app.config.general.web_log)]}/>
                            ${_('enable logs from the internal Tornado web server')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable UPnP')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="enable_upnp">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="enable_upnp"
                                   id="enable_upnp" ${('', 'checked')[bool(sickrage.app.config.general.enable_upnp)]}/>
                            ${_('automatically sets up port-forwarding from external IP to SiCKRAGE')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Listen on IPv6')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="web_ipv6">
                            <input type="checkbox" class="toggle color-primary is-material" name="web_ipv6"
                                   id="web_ipv6" ${('', 'checked')[bool(sickrage.app.config.general.web_ipv6)]}/>
                            ${_('attempt binding to any available IPv6 address')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable HTTPS')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="enable_https">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="enable_https"
                                   id="enable_https" ${('', 'checked')[bool(sickrage.app.config.general.enable_https)]}/>
                            ${_('enable access to the web interface using a HTTPS address')}
                        </label>
                    </div>
                </div>

##                 <div id="content_enable_https">
##                     <div class="form-row form-group">
##
##                         <div class="col-lg-3 col-md-4 col-sm-5">
##                             <label class="component-title">${_('HTTPS certificate')}</label>
##                         </div>
##                         <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
##                             <div class="form-row">
##                                 <div class="col-md-12">
##                                     <input name="https_cert" id="https_cert"
##                                            value="${sickrage.app.config.general.https_cert}"
##                                            class="form-control"
##                                            autocapitalize="off"/>
##                                 </div>
##                             </div>
##                             <div class="form-row">
##                                 <div class="col-md-12">
##                                     <label for="https_cert">
##                                         ${_('file name or path to HTTPS certificate')}
##                                     </label>
##                                 </div>
##                             </div>
##                         </div>
##                     </div>
##
##                     <div class="form-row form-group">
##                         <div class="col-lg-3 col-md-4 col-sm-5">
##                             <label class="component-title">${_('HTTPS key')}</label>
##                         </div>
##                         <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
##                             <div class="form-row">
##                                 <div class="col-md-12">
##                                     <input name="https_key" id="https_key"
##                                            value="${sickrage.app.config.general.https_key}"
##                                            class="form-control" autocapitalize="off"/>
##                                 </div>
##                             </div>
##                             <div class="form-row">
##                                 <div class="col-md-12">
##                                     <label for="https_key">${_('file name or path to HTTPS key')}</label>
##                                 </div>
##                             </div>
##                         </div>
##                     </div>
##                 </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Reverse proxy headers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="handle_reverse_proxy">
                            <input type="checkbox" class="toggle color-primary is-material" name="handle_reverse_proxy"
                                   id="handle_reverse_proxy" ${('', 'checked')[bool(sickrage.app.config.general.handle_reverse_proxy)]}/>
                            ${_('accept the following reverse proxy headers (advanced) - (X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Proto)')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Notify on login')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="notify_on_login">
                            <input type="checkbox" class="toggle color-primary is-material" name="notify_on_login"
                                   id="notify_on_login" ${('', 'checked')[bool(sickrage.app.config.general.notify_on_login)]}/>
                            ${_('send a message to all enabled notification providers when someone logs into SiCKRAGE from a public IP address')}
                        </label>
                    </div>
                </div>

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>

        </div><!-- Network section -->
    </div><!-- network.tab-pane -->

    <div id="advanced-settings" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Advanced Settings')}</h3>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('CPU throttling')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-microchip"></span>
                                </span>
                            </div>
                            <select id="cpu_presets" name="cpu_preset" class="form-control"
                                    title="${_('Normal (default). High is lower and Low is higher CPU use')}">
                                % for item in CpuPreset:
                                    <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.cpu_preset == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Max queue workers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-microchip"></span>
                                </span>
                            </div>
                            <input id="max_queue_workers" name="max_queue_workers" type="number"
                                   value="${sickrage.app.config.general.max_queue_workers}" min="1"
                                   title="${_('Maximum allowed items to be processed from queue at same time')}"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Anonymous redirect')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-globe"></span>
                                </span>
                            </div>
                            <input id="anon_redirect" name="anon_redirect"
                                   value="${sickrage.app.config.general.anon_redirect}"
                                   title="${_('Backlink protection via anonymizer service, must end in ?')}"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>

                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable debug')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="debug">
                            <input type="checkbox" class="toggle color-primary is-material" name="debug"
                                   id="debug" ${('', 'checked')[bool(sickrage.app.config.general.debug)]}/>
                            ${_('Enable debug logs')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Verify SSL Certs')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="ssl_verify">
                            <input type="checkbox" class="toggle color-primary is-material" name="ssl_verify"
                                   id="ssl_verify" ${('', 'checked')[bool(sickrage.app.config.general.ssl_verify)]}/>
                            ${_('Verify SSL Certificates (Disable this for broken SSL installs (Like QNAP)')}
                        </label>
                    </div>

                </div>

                <div class="form-row form-group">

                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('No Restart')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="no_restart">
                            <input type="checkbox" class="toggle color-primary is-material" name="no_restart"
                                   title="${_('Only select this when you have external software restarting SR automatically when it stops (like FireDaemon)')}"
                                   id="no_restart" ${('', 'checked')[bool(sickrage.app.config.general.no_restart)]}/>
                            ${_('Shutdown SiCKRAGE on restarts (external service must restart SiCKRAGE on its own).')}
                        </label>
                    </div>


                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Unprotected calendar')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="calendar_unprotected">
                            <input type="checkbox" class="toggle color-primary is-material" name="calendar_unprotected"
                                   id="calendar_unprotected" ${('', 'checked')[bool(sickrage.app.config.general.calendar_unprotected)]}/>
                            ${_('allow subscribing to the calendar without user and password. Some services like Google Calendar only work this way')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Google Calendar Icons')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="calendar_icons">
                            <input type="checkbox" class="toggle color-primary is-material" name="calendar_icons"
                                   id="calendar_icons" ${('', 'checked')[bool(sickrage.app.config.general.calendar_icons)]}/>
                            ${_('show an icon next to exported calendar events in Google Calendar.')}
                        </label>
                    </div>


                </div>

                <div class="form-row form-group" style="display: none">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Link Google Account')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <input class="btn btn-inline" type="button" id="google_link" value="${_('Link')}">
                        <label for="google_link">
                            ${_('link your google account to SiCKRAGE for advanced feature usage such as settings/database storage')}
                        </label>
                    </div>

                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Proxy host')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-globe"></span>
                                </span>
                            </div>
                            <input id="proxy_setting" name="proxy_setting"
                                   value="${sickrage.app.config.general.proxy_setting}"
                                   title="${_('Proxy SiCKRAGE connections')}"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Use proxy for series providers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label class="form-check-label">
                            <input type="checkbox" class="toggle color-primary is-material" name="proxy_series_providers"
                                   id="proxy_series_providers" ${('', 'checked')[bool(sickrage.app.config.general.proxy_series_providers)]}/>
                            ${_('use proxy host for connecting to series providers (TheTVDB)')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Skip Remove Detection')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label class="form-check-label">
                            <input type="checkbox" class="toggle color-primary is-material" name="skip_removed_files"
                                   id="skip_removed_files" ${('', 'checked')[bool(sickrage.app.config.general.skip_removed_files)]}/>
                            ${_('Skip detection of removed files. If disable it will set default deleted status')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('This may mean SiCKRAGE misses renames as well')}</div>
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Default deleted episode status')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-eraser"></span>
                                        </span>
                                    </div>
                                    % if not sickrage.app.config.general.skip_removed_files:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status"
                                                class="form-control">
                                            % for item in [EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED, EpisodeStatus.ARCHIVED]:
                                                <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.ep_default_deleted_status == item]}>${item.display_name}</option>
                                            % endfor
                                        </select>
                                    % else:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status"
                                                class="form-control" disabled="disabled">
                                            % for item in [EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED]:
                                                <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.ep_default_deleted_status == item]}>${item.display_name}</option>
                                            % endfor
                                        </select>
                                    % endif
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="ep_default_deleted_status">
                                    ${_('Define the status to be set for media file that has been deleted.')}
                                    <br/>
                                    <b>${_('NOTE:')}</b> ${_('Archived option will keep previous downloaded quality')}
                                    <br/>
                                    ${_('Example: Downloaded (1080p WEB-DL) ==> Archived (1080p WEB-DL)')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Allowed video file extensions')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-file"></span>
                                </span>
                            </div>
                            <input name="allowed_video_file_exts" id="allowed_video_file_exts"
                                   value="${sickrage.app.config.general.allowed_video_file_exts}"
                                   placeholder="${_('ex: avi,mp4,mkv')}"
                                   title="comma separated list of video file extensions you want to allow, do not include dots"
                                   class="form-control"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Strip special filesystem bits from files')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label class="form-check-label">
                            <input type="checkbox" class="toggle color-primary is-material"
                                   name="strip_special_file_bits"
                                   id="strip_special_file_bits" ${('', 'checked')[bool(sickrage.app.config.general.strip_special_file_bits)]}/>
                            ${_('Strips special filesystem bits from files, if disabled will leave special bits intact.')}
                            <br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('This will strip inherited permissions')}
                            </div>
                        </label>
                    </div>
                </div>

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('SiCKRAGE API')}</h3>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable SiCKRAGE API')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="enable_sickrage_api">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="enable_sickrage_api"
                                   id="enable_sickrage_api" ${('', 'checked')[bool(sickrage.app.config.general.enable_sickrage_api)]}/>
                            ${_('enable SiCKRAGE API extra features')}
                        </label>
                        <br/>
                        <div class="text-info">
                            <b>${_('NOTE:')}</b> ${_('Enabling this will pop-up a window for you to login to the SiCKRAGE API')}
                        </div>
                    </div>
                </div>
            </fieldset>
        </div>

        % if sickrage.app.version_updater.updater.type == "git":
        <%
            git_branches = sickrage.app.version_updater.updater.remote_branches
            git_current_branch = sickrage.app.version_updater.updater.current_branch
        %>

            <hr/>

            <div class="form-row">
                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                    <h3>${_('GIT Settings')}</h3>
                </div>
                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Git Branches')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fab fa-git"></span>
                                            </span>
                                        </div>
                                        <select id="branchVersion" class="form-control"
                                                title=${_('GIT Branch Version')}>
                                            % if git_branches:
                                                % for git_branch in git_branches:
                                                <%
                                                    if not sickrage.app.developer and git_branch not in ['master', 'develop']:
                                                        continue
                                                %>
                                                    <option value="${git_branch}" ${('', 'selected')[git_current_branch == git_branch]}>${git_branch}</option>
                                                % endfor
                                            % endif
                                        </select>
                                        <div class="input-group-append">
                                            <span class="btn" id="branchCheckout" ${('', 'disabled')[not git_branches]}>
                                                ${_('Checkout Branch')}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('GIT executable path')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-file"></span>
                                            </span>
                                        </div>
                                        <input id="git_path" name="git_path"
                                               value="${sickrage.app.config.general.git_path}"
                                               placeholder="${_('ex: /path/to/git')}"
                                               title="only needed if OS is unable to locate git from env"
                                               class="form-control" autocapitalize="off"/>
                                        <div class="input-group-append">
                                            <span class="btn" id="verifyGitPath">
                                                ${_('Verify Path')}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <p></p>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="testNotification"
                                         id="testGIT-result">${_('Click verify path to test.')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group d-none">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Git reset')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="git_reset">
                                <input type="checkbox" class="toggle color-primary is-material" name="git_reset"
                                       id="git_reset" ${('', 'checked')[bool(sickrage.app.config.general.git_reset)]}/>
                                ${_('removes untracked files and performs a hard reset on git branch automatically to help resolve update issues')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </fieldset>

            </div>
        % endif
    </div><!-- advanced-settings.tab-pane -->
</%block>