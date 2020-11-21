<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveSubtitles' %></%def>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.subtitles import Subtitles
%>
<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#subtitles-search">${_('Subtitles Search')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#subtitles-plugin">${_('Subtitles Plugin')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#plugin-settings">${_('Plugin Settings')}</a>
    </li>
</%block>
<%block name="pages">
    <%
        providerLoginDict = {'legendastv': {'user': sickrage.app.config.subtitles.legendastv_user, 'pass': sickrage.app.config.subtitles.legendastv_pass},
                            'itasa': {'user': sickrage.app.config.subtitles.itasa_user, 'pass': sickrage.app.config.subtitles.itasa_pass},
                            'addic7ed': {'user': sickrage.app.config.subtitles.addic7ed_user, 'pass': sickrage.app.config.subtitles.addic7ed_pass},
                            'opensubtitles': {'user': sickrage.app.config.subtitles.opensubtitles_user, 'pass': sickrage.app.config.subtitles.opensubtitles_pass}}
    %>
    <div id="subtitles-search" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Subtitles Search')}</h3>
                <small class="form-text text-muted">
                    <p>${_('Settings that dictate how SickRage handles subtitles search results.')}</p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_subtitles">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   ${('', ' checked="checked"')[bool(sickrage.app.config.subtitles.enable)]}
                                   id="use_subtitles" name="use_subtitles">
                            ${_('Search Subtitles')}
                        </label>
                    </div>
                </div>

                <div id="content_use_subtitles">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Subtitle Languages')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div id="subtitles_languages"></div>
                            </div>
                            <label class="text-info" for="subtitles_languages">
                                <b>${_('NOTE:')}</b> ${_('Leave empty to default language to English.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Subtitles History')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="subtitles_history">
                                <input type="checkbox" class="toggle color-primary is-material" name="subtitles_history"
                                       id="subtitles_history" ${('', 'checked')[bool(sickrage.app.config.subtitles.history)]}/>
                                ${_('Log downloaded Subtitle on History page?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Subtitles Multi-Language')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="subtitles_multi">
                                <input type="checkbox" class="toggle color-primary is-material" name="subtitles_multi"
                                       id="subtitles_multi" ${('', 'checked')[bool(sickrage.app.config.subtitles.multi)]}/>
                                ${_('Append language codes to subtitle filenames?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Embedded Subtitles')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label class="form-check-label">
                                <input type="checkbox" class="toggle color-primary is-material" name="enable_embedded_subtitles"
                                       id="enable_embedded_subtitles" ${('', 'checked')[bool(sickrage.app.config.subtitles.enable_embedded)]}/>
                                ${_('Ignore subtitles embedded inside video file?')}<br/>
                                <div class="text-info">
                                    <b>${_('Warning:')}</b> ${_('this will ignore <u>all</u> embedded subtitles for every video file!')}
                                </div>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Hearing Impaired Subtitles')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="subtitles_hearing_impaired">
                                <input type="checkbox" class="toggle color-primary is-material" name="subtitles_hearing_impaired"
                                       id="subtitles_hearing_impaired" ${('', 'checked')[bool(sickrage.app.config.subtitles.hearing_impaired)]}/>
                                ${_('Download hearing impaired style subtitles?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Subtitle Directory')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-folder-open"></span></span>
                                </div>
                                <input value="${sickrage.app.config.subtitles.dir}"
                                       id="subtitles_dir"
                                       name="subtitles_dir" class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="subtitles_dir">
                                ${_('The directory where SickRage should store your')}
                                <i>${_('Subtitles')}</i> ${_('files.')}<br/>
                                <b>${_('NOTE:')}</b> ${_('Leave empty if you want store subtitle in episode path.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Subtitle Find Frequency')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-clock"></span>
                                    </span>
                                </div>
                                <input type="number" name="subtitles_finder_frequency"
                                       value="${sickrage.app.config.general.subtitle_searcher_freq}" hours="1"
                                       placeholder="${_('1')}"
                                       title="time in hours between scans"
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
                            <label class="component-title">${_('Extra Scripts')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-file"></span>
                                    </span>
                                </div>
                                <input name="subtitles_extra_scripts" id="subtitles_extra_scripts"
                                       value="<% '|'.join(sickrage.app.config.subtitles.extra_scripts) %>"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="subtitles_extra_scripts">
                                <b>${_('NOTE:')}</b>
                                <ul>
                                    <li>
                                        ${_('See')}
                                        <a href="https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/Subtitle%20Scripts">
                                            <span style="color: red; "><b>${_('Wiki')}</b></span>
                                        </a>
                                        ${_('for a script arguments description.')}
                                    </li>
                                    <li>
                                        ${_('Additional scripts separated by')} <b>|</b>.
                                    </li>
                                    <li>
                                        ${_('Scripts are called after each episode has searched and downloaded subtitles.')}
                                    </li>
                                    <li>
                                        ${_('For any scripted languages, include the interpreter executable before the script. See the following example:')}
                                    </li>
                                    <ul>
                                        <li>
                                            ${_('For Windows:')}
                                            <small class="text-muted">C:\Python37\pythonw.exe C:\Script\test.py</small>
                                        </li>
                                        <li>
                                            ${_('For Linux:')}
                                            <small class="text-muted">python3 /Script/test.py</small>
                                        </li>
                                    </ul>
                                </ul>
                            </label>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="subtitles-plugin" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Subtitle Plugins')}</h3>
                <small class="form-text text-muted">
                    <p>${_('Check off and drag the plugins into the order you want them to be used.')}</p>
                    ${_('At least one plugin is required.')}<br/>
                    <span style="font-size: 16px;">*</span> ${_('Web-scraping plugin')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row">
                    <div class="col-md-12">
                        <div class="list-group w-50" id="service_order_list">
                            % for curService in Subtitles().sortedServiceList():
                                <div class="list-group-item list-group-item-action list-group-item-dark rounded mb-1 p-2" id="${curService['name']}">
                                    <div class="align-middle">
                                        <label class="form-check-label">
                                            <input type="checkbox" id="enable_${curService['name']}"
                                                   class="service_enabler" ${('', 'checked')[curService['enabled'] == True]}/>
                                            <a href="${anon_url(curService['url'])}" class="imgLink" target="_new">
                                                <i class="sickrage-subtitles sickrage-subtitles-${curService['name']}"
                                                   title="${curService['url']}"></i>
                                            </a>
                                            <span class="font-weight-bold">${curService['name'].capitalize()}</span>
                                        </label>
                                        <span class="d-inline-block float-right">
                                            <i class="fas ${('fa-unlock text-success','fa-lock text-danger')[curService['name'] in providerLoginDict]}"></i>
                                        </span>
                                    </div>
                                </div>
                            % endfor
                        </div>
                    </div>
                </div>

                <input type="hidden" name="service_order" id="service_order"
                       value="<% ''.join(['%s:%d' % (x['name'], x['enabled']) for x in Subtitles().sortedServiceList()])%>"/>

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    <div id="plugin-settings" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Subtitle Settings')}</h3>
                <small class="form-text text-muted">
                    <p>${_('Set user and password for each provider')}</p>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                % for curService in Subtitles().sortedServiceList():
                    % if curService['name'] in providerLoginDict.keys():
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${curService['name'].capitalize()} ${_('User Name')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="${curService['name']}_user"
                                           id="${curService['name']}_user"
                                           value="${providerLoginDict[curService['name']]['user']}"
                                           title="${curService['name'].capitalize()} User Name"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${curService['name'].capitalize()} ${_('Password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="${curService['name']}_pass"
                                           id="${curService['name']}_pass"
                                           value="${providerLoginDict[curService['name']]['pass']}"
                                           title="${curService['name'].capitalize()} Password"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    % endif
                % endfor
                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane3 //-->
</%block>