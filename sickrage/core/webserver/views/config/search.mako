<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveSearch' %></%def>
<%!
    import sickrage
    from sickrage.core.enums import NzbMethod, TorrentMethod, CheckPropersInterval
%>
<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#search-setttings">${_('Search Settings')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#nzb-clients">${_('NZB Clients')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#torrent-clients">${_('Torrent Clients')}</a>
    </li>
</%block>
<%block name="pages">
    <div id="search-setttings" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Search Settings')}</h3>
                <small class="form-text text-muted">
                    <p>${_('How to manage searching with')} <a
                            href="${srWebRoot}/config/providers">${_('providers')}</a>.</p>
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Randomize Providers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="randomize_providers">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="randomize_providers" id="randomize_providers"
                                ${('', 'checked')[bool(sickrage.app.config.general.randomize_providers)]}/>
                            ${_('randomize the provider search order')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Download propers')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="download_propers">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="download_propers" id="download_propers"
                                ${('', 'checked')[bool(sickrage.app.config.general.download_propers)]}/>
                            ${_('replace original download with "Proper" or "Repack" if nuked')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable provider RSS cache')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="enable_rss_cache">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="enable_rss_cache" id="enable_rss_cache"
                                ${('', 'checked')[bool(sickrage.app.config.general.enable_rss_cache)]}/>
                            ${_('enables/disables provider RSS feed caching')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Download UNVERIFIED torrent magnet links')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="download_unverified_magnet_link">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="download_unverified_magnet_link"
                                   id="download_unverified_magnet_link"
                                ${('', 'checked')[bool(sickrage.app.config.general.download_unverified_magnet_link)]}/>
                            ${_('enables/disables downloading of unverified torrent magnet links via clients')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Convert provider torrent file links to magnetic links')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="torrent_file_to_magnet">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="torrent_file_to_magnet" id="torrent_file_to_magnet"
                                ${('', 'checked')[bool(sickrage.app.config.general.torrent_file_to_magnet)]}/>
                            ${_('enables/disables converting of public torrent provider file links to magnetic links')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Convert provider torrent magnetic links to torrent files')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="torrent_magnet_to_file">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="torrent_magnet_to_file" id="torrent_magnet_to_file"
                                ${('', 'checked')[bool(sickrage.app.config.general.torrent_magnet_to_file)]}/>
                            ${_('enables/disables converting of public torrent provider magnetic links to torrent files')}
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable failed snatch handling')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_failed_snatcher">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="use_failed_snatcher" id="use_failed_snatcher"
                                ${('', 'checked')[bool(sickrage.app.config.failed_snatches.enable)]}/>
                            ${_('enables/disables failed snatch handling, automatically retries failed snatches')}
                        </label>
                    </div>
                </div>

                <div id="content_use_failed_snatcher">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Check for failed snatches aged')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-clock"></span>
                                    </span>
                                </div>
                                <select id="failed_snatch_age" name="failed_snatch_age" class="form-control"
                                        title="minimum allowed time ${sickrage.app.min_failed_snatch_age} hours">
                                    % for hour in range(1,25):
                                        <option value="${hour}" ${('', 'selected')[sickrage.app.config.failed_snatches.age == hour]}>${hour}</option>
                                    % endfor
                                </select>
                                <div class="input-group-append">
                                    <span class="input-group-text">
                                        hours
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="content_download_propers">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Check propers every:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-clock"></span>
                                    </span>
                                </div>
                                <select id="check_propers_interval" name="check_propers_interval"
                                        class="form-control" title="Interval to check for propers">
                                    % for item in CheckPropersInterval:
                                        <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.proper_searcher_interval == item]}>${item.display_name}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Backlog search frequency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="backlog_frequency"
                                   id="backlog_frequency"
                                   value="${sickrage.app.config.general.backlog_searcher_freq}"
                                   placeholder="${_('time in minutes')}"
                                   title="minimum allowed time ${sickrage.app.min_backlog_searcher_freq} minutes"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    min
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Daily search frequency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="dailysearch_frequency"
                                   id="dailysearch_frequency"
                                   value="${sickrage.app.config.general.daily_searcher_freq}"
                                   placeholder="${_('time in minutes')}"
                                   title="minimum allowed time ${sickrage.app.min_auto_postprocessor_freq} minutes"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    min
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Usenet retention')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input name="usenet_retention"
                                   id="usenet_retention"
                                   value="${sickrage.app.config.general.usenet_retention}"
                                   title="age limit in days (ex. 500)"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    days
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Ignore words')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-font"></span></span>
                            </div>
                            <input name="ignore_words"
                                   value="${sickrage.app.config.general.ignore_words}"
                                   placeholder="${_('ex. word1,word2,word3')}"
                                   title="Results with one or more word from this list will be ignored separate words with a comma"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Require words')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-font"></span></span>
                            </div>
                            <input name="require_words"
                                   value="${sickrage.app.config.general.require_words}"
                                   placeholder="${_('ex. word1,word2,word3')}"
                                   title="Results with no word from this list will be ignored separate words with a comma"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Ignore language names in subbed results')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-font"></span></span>
                            </div>
                            <input name="ignored_subs_list"
                                   value="${sickrage.app.config.general.ignored_subs_list}"
                                   placeholder="${_('ex. lang1,lang2,lang3')}"
                                   title="Ignore subbed releases based on language names, ex: dk will ignore words: dksub, dksubs, dksubbed, dksubed"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Allow high priority')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="allow_high_priority">
                            <input type="checkbox" class="toggle color-primary is-material" name="allow_high_priority"
                                   id="allow_high_priority" ${('', 'checked')[bool(sickrage.app.config.general.allow_high_priority)]}/>
                            ${_('Set downloads of recently aired episodes to high priority')}
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
    </div><!-- /tab-pane1 //-->

    <div id="nzb-clients" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('NZB Clients')}</h3>
                <small class="form-text text-muted">
                    <p>${_('How to handle NZB search results for clients.')}</p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_nzbs">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_nzbs"
                                   title="Enable NZB searches"
                                   id="use_nzbs" ${('', 'checked')[bool(sickrage.app.config.general.use_nzbs)]}/>
                            ${_('enable NZB searches')}
                        </label>
                    </div>
                </div>

                <div id="content_use_nzbs">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Send .nzb files to:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud-upload-alt"></span></span>
                                </div>
                                <select name="nzb_method" id="nzb_method" class="form-control" title="NZB Clients">
                                    % for item in NzbMethod:
                                        <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.nzb_method == item]}>${item.display_name}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="blackhole_settings">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Black hole folder location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <input name="nzb_dir" id="nzb_dir"
                                           value="${sickrage.app.config.blackhole.nzb_dir}"
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
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('SABnzbd server URL')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input id="sab_host" name="sab_host"
                                           value="${sickrage.app.config.sabnzbd.host}"
                                           placeholder="${_('ex. http://localhost:8080')}"
                                           class="form-control" autocapitalize="off"
                                           type="url"
                                           pattern="https?:\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?">
                                    <div class="invalid-tooltip">
                                        Please fill in a valid URL.
                                    </div>
                                </div>
                                <label for="sab_host">
                                    <p>
                                        ${_('do not include a trailing slash at the end of your host')}
                                    </p>
                                </label>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('SABnzbd username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="sab_username" id="sab_username"
                                           value="${sickrage.app.config.sabnzbd.username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('SABnzbd password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="sab_password" id="sab_password"
                                           value="${sickrage.app.config.sabnzbd.password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('SABnzbd API key')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                    </div>
                                    <input name="sab_apikey" id="sab_apikey"
                                           value="${sickrage.app.config.sabnzbd.apikey}"
                                           class="form-control"
                                           title="locate at... SABnzbd Config -> General -> API Key"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use SABnzbd category')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="sab_category" id="sab_category"
                                           value="${sickrage.app.config.sabnzbd.category}"
                                           placeholder="${_('ex. TV')}"
                                           title="SABNzbd download category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use SABnzbd category (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="sab_category_backlog" id="sab_category_backlog"
                                           value="${sickrage.app.config.sabnzbd.category_backlog}"
                                           placeholder="${_('ex. TV')}"
                                           title="add downloads of old episodes to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use SABnzbd category for anime')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="sab_category_anime" id="sab_category_anime"
                                           value="${sickrage.app.config.sabnzbd.category_anime}"
                                           placeholder="${_('ex. anime')}"
                                           title="add anime downloads to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>


                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use SABnzbd category for anime (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="sab_category_anime_backlog"
                                           id="sab_category_anime_backlog"
                                           value="${sickrage.app.config.sabnzbd.category_anime_backlog}"
                                           placeholder="${_('ex. anime')}"
                                           title="add anime downloads of old episodes to this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        % if sickrage.app.config.general.allow_high_priority == True:
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5">
                                    <label class="component-title">${_('Use forced priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                    <label for="sab_forced">
                                        <input type="checkbox" class="enabler toggle color-primary is-material"
                                               name="sab_forced"
                                               id="sab_forced" ${('', 'selected')[bool(sickrage.app.config.sabnzbd.forced)]}/>
                                        ${_('enable to change priority from HIGH to FORCED')}
                                    </label>
                                </div>
                            </div>
                        % endif
                    </div>

                    <div id="nzbget_settings">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Connect using HTTPS')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="nzbget_use_https">
                                    <input id="nzbget_use_https" type="checkbox"
                                           class="enabler toggle color-primary is-material"
                                           name="nzbget_use_https" ${('', 'selected')[bool(sickrage.app.config.nzbget.use_https)]}/>
                                    ${_('enable secure control')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('NZBget host:port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input name="nzbget_host" id="nzbget_host"
                                           value="${sickrage.app.config.nzbget.host}"
                                           placeholder="${_('ex. http://localhost:6789')}"
                                           title="NZBget RPC host name and port number (not NZBgetweb!"
                                           class="form-control"
                                           autocapitalize="off"
                                           type="url"
                                           pattern="https?:\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?">
                                    <div class="invalid-tooltip">
                                        Please fill in a valid host:port
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('NZBget username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="nzbget_username" id="nzbget_username"
                                           value="${sickrage.app.config.nzbget.username}"
                                           placeholder="${_('default = nzbget')}"
                                           title="locate in nzbget.conf"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('NZBget password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="nzbget_password" id="nzbget_password"
                                           value="${sickrage.app.config.nzbget.password}"
                                           placeholder="${_('default = tegbzn6789')}"
                                           title="locate in nzbget.conf"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use NZBget category')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="nzbget_category" id="nzbget_category"
                                           value="${sickrage.app.config.nzbget.category}"
                                           placeholder="${_('ex. TV')}"
                                           title="send downloads marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use NZBget category (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="nzbget_category_backlog" id="nzbget_category_backlog"
                                           value="${sickrage.app.config.nzbget.category_backlog}"
                                           placeholder="${_('ex. TV')}"
                                           title="send downloads of old episodes marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use NZBget category for anime')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="nzbget_category_anime" id="nzbget_category_anime"
                                           value="${sickrage.app.config.nzbget.category_anime}"
                                           placeholder="${_('ex. anime')}"
                                           title="send anime downloads marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Use NZBget category for anime (backlog episodes)')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-book"></span></span>
                                    </div>
                                    <input name="nzbget_category_anime_backlog"
                                           id="nzbget_category_anime_backlog"
                                           value="${sickrage.app.config.nzbget.category_anime_backlog}"
                                           placeholder="${_('ex. anime')}"
                                           title="send anime downloads of old episodes marked this category"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('NZBget priority')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-exclamation-triangle"></span>
                                        </span>
                                    </div>
                                    <select name="nzbget_priority" id="nzbget_priority"
                                            title="priority for daily snatches (no backlog)"
                                            class="form-control">
                                        <option value="-100" ${('', 'selected')[sickrage.app.config.nzbget.priority == -100]}>
                                            ${_('Very low')}
                                        </option>
                                        <option value="-50" ${('', 'selected')[sickrage.app.config.nzbget.priority == -50]}>
                                            ${_('Low')}
                                        </option>
                                        <option value="0" ${('', 'selected')[sickrage.app.config.nzbget.priority == 0]}>
                                            ${_('Normal')}
                                        </option>
                                        <option value="50" ${('', 'selected')[sickrage.app.config.nzbget.priority == 50]}>
                                            ${_('High')}
                                        </option>
                                        <option value="100" ${('', 'selected')[sickrage.app.config.nzbget.priority == 100]}>
                                            ${_('Very high')}
                                        </option>
                                        <option value="900" ${('', 'selected')[sickrage.app.config.nzbget.priority == 900]}>
                                            ${_('Force')}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="download_station_settings">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Synology DSM host:port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input name="syno_dsm_host" id="syno_dsm_host"
                                           value="${sickrage.app.config.synology.host}"
                                           placeholder="${_('ex. http://localhost:5000/')}"
                                           title="URL to your Synology DSM"
                                           class="form-control"
                                           autocapitalize="off"
                                           type="url"
                                           pattern="https?:\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?">
                                    <div class="invalid-tooltip">
                                        Please fill in a valid host:port
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Synology DSM username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="syno_dsm_username" id="syno_dsm_username"
                                           value="${sickrage.app.config.synology.username}"
                                           placeholder="${_('blank for none')}"
                                           title="Synology DSM username"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Synology DSM password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="syno_dsm_password" id="syno_dsm_password"
                                           value="${sickrage.app.config.synology.password}"
                                           placeholder="${_('blank for none')}"
                                           title="Synology DSM password"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_path_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Downloaded files location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <input name="syno_dsm_path" id="syno_dsm_path"
                                           value="${sickrage.app.config.synology.path}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                                <label for="syno_dsm_path">
                                    ${_('where Synology Download Station will save downloaded files (blank for client default)')}
                                    <br/>
                                    <b>${_('NOTE:')}</b> ${_('the destination has to be a shared folder for Synology DS devices')}
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testSABnzbd_result">${_('Click below to test')}</div>
                            <div class="testNotification" id="testSynologyDSM_result">${_('Click below to test')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn test-button" type="button" value="${_('Test SABnzbd')}"
                                   id="testSABnzbd"/>
                            <input class="btn test-button" type="button" value="${_('Test Synology DSM')}"
                                   id="testSynologyDSM"/>
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/><br>
                        </div>
                    </div>

                </div><!-- /content_use_nzbs //-->

            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    <div id="torrent-clients" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Torrent Clients')}</h3>
                <small class="form-text text-muted">
                    <p>${_('How to handle Torrent search results for clients.')}</p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_torrents">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_torrents"
                                   id="use_torrents" ${('', 'checked')[bool(sickrage.app.config.general.use_torrents)]}/>
                            ${_('Enable torrent searches')}
                        </label>
                    </div>
                </div>

                <div id="content_use_torrents">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Send .torrent files to:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud-upload-alt"></span></span>
                                </div>
                                <select name="torrent_method" id="torrent_method" class="form-control"
                                        title="Torrent Clients">
                                    % for item in TorrentMethod:
                                        <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.torrent_method == item]}>${item.display_name}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="options_torrent_blackhole">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Black hole folder location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <input name="torrent_dir" id="torrent_dir"
                                           value="${sickrage.app.config.blackhole.torrent_dir}"
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
                        <input type="submit" class="btn config_submitter"
                               value="${_('Save Changes')}"/><br>
                    </div>

                    <div id="options_torrent_clients">
                        <div class="form-row form-group" id="torrent_host_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title" id="host_title">${_('Torrent host:port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input name="torrent_host" id="torrent_host"
                                           value="${sickrage.app.config.torrent.host}"
                                           title="URL to your torrent client"
                                           class="form-control"
                                           autocapitalize="off"
                                           type="url"
                                           pattern="(scgi|https?):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?">
                                    <div class="invalid-tooltip">
                                        Please fill in a valid URL.
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_rpc_url_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title" id="rpcurl_title">${_('Torrent RPC URL')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                    </div>
                                    <input name="torrent_rpc_url" id="torrent_rpc_url"
                                           value="${sickrage.app.config.torrent.rpc_url}"
                                           placeholder="${_('ex. transmission')}"
                                           title="The path without leading and trailing slashes"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_auth_type_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('HTTP Authentication')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <select name="torrent_auth_type" id="torrent_auth_type" title="Client AUTH type"
                                            class="form-control">
                                        <% http_authtype = {'none': _("None"), 'basic': _("Basic"), 'digest': _("Digest")} %>
                                        % for authvalue, authname in http_authtype.items():
                                            <option id="torrent_auth_type_value"
                                                    value="${authvalue}" ${('', 'selected')[sickrage.app.config.torrent.auth_type == authvalue]}>${authname}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_verify_cert_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Verify certificate')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="torrent_verify_cert">
                                    <input type="checkbox" class="enabler toggle color-primary is-material"
                                           name="torrent_verify_cert"
                                           id="torrent_verify_cert" ${('', 'checked')[bool(sickrage.app.config.torrent.verify_cert)]}/>
                                    <p id="torrent_verify_deluge">
                                        ${_('disable if you get "Deluge: Authentication Error" in your log')}
                                    </p>
                                    <p id="torrent_verify_rtorrent">
                                        ${_('Verify SSL certificates for HTTPS requests')}
                                    </p>
                                </label>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_username_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title" id="username_title">${_('Client username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="torrent_username" id="torrent_username"
                                           value="${sickrage.app.config.torrent.username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_password_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title" id="password_title">${_('Client password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="torrent_password" id="torrent_password"
                                           value="${sickrage.app.config.torrent.password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_label_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Add label to torrent')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-tag"></span></span>
                                    </div>
                                    <input name="torrent_label" id="torrent_label"
                                           value="${sickrage.app.config.torrent.label}"
                                           placeholder="${_('blank spaces are not allowed')}"
                                           title="label plugin must be enabled in Deluge clients"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_label_anime_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Add anime label to torrent')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-tag"></span></span>
                                    </div>
                                    <input name="torrent_label_anime" id="torrent_label_anime"
                                           value="${sickrage.app.config.torrent.label_anime}"
                                           placeholder="${_('blank spaces are not allowed')}"
                                           title="label plugin must be enabled in Deluge clients"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_path_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Downloaded files location')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <input name="torrent_path" id="torrent_path"
                                           value="${sickrage.app.config.torrent.path}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                                <label for="torrent_path">
                                    ${_('where the torrent client will save downloaded files (blank for client default)')}
                                    <br/>
                                    <b>${_('NOTE:')}</b> ${_('the destination has to be a shared folder for Synology DS devices')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_seed_time_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title" id="torrent_seed_time_label">
                                    ${_('Minimum seeding time is')}
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-upload"></span></span>
                                    </div>
                                    <input type="number"
                                           step="1"
                                           name="torrent_seed_time"
                                           id="torrent_seed_time"
                                           value="${sickrage.app.config.torrent.seed_time}"
                                           title="hours. (default:'0' passes blank to client and '-1' passes nothing)"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_paused_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Start torrent paused')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="torrent_paused">
                                    <input type="checkbox" class="enabler toggle color-primary is-material"
                                           name="torrent_paused"
                                           id="torrent_paused" ${('', 'checked')[bool(sickrage.app.config.torrent.paused)]}/>
                                    ${_('add .torrent to client but do <b>not</b> start downloading')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row form-group" id="torrent_high_bandwidth_option">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Allow high bandwidth')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="torrent_high_bandwidth">
                                    <input type="checkbox" class="enabler toggle color-primary is-material"
                                           name="torrent_high_bandwidth"
                                           id="torrent_high_bandwidth" ${('', 'checked')[bool(sickrage.app.config.torrent.high_bandwidth)]}/>
                                    ${_('use high bandwidth allocation if priority is high')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="testNotification" id="test_torrent_result">${_('Click below to test')}</div>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <input class="btn test-button" type="button"
                                       value="${_('Test Connection')}"
                                       id="test_torrent"/>
                                <input type="submit" class="btn config_submitter"
                                       value="${_('Save Changes')}"/><br>
                            </div>
                        </div>

                    </div>
                </div><!-- /content_use_torrents //-->
            </fieldset>
        </div>
    </div><!-- /tab-pane3 //-->
</%block>