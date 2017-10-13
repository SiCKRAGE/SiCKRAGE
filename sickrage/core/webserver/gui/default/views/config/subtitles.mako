<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveSubtitles' %></%def>
<%!
    import sickrage
    import sickrage.subtitles
    from sickrage.core.helpers import anon_url
%>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Subtitles Search</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Subtitles Plugin</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane3">Plugin Settings</a></li>
</%block>
<%block name="pages">
    <%
        providerLoginDict = {'legendastv': {'user': sickrage.srCore.srConfig.LEGENDASTV_USER, 'pass': sickrage.srCore.srConfig.LEGENDASTV_PASS},
                            'itasa': {'user': sickrage.srCore.srConfig.ITASA_USER, 'pass': sickrage.srCore.srConfig.ITASA_PASS},
                            'addic7ed': {'user': sickrage.srCore.srConfig.ADDIC7ED_USER, 'pass': sickrage.srCore.srConfig.ADDIC7ED_PASS},
                            'opensubtitles': {'user': sickrage.srCore.srConfig.OPENSUBTITLES_USER, 'pass': sickrage.srCore.srConfig.OPENSUBTITLES_PASS}}
    %>
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Subtitles Search</h3>
                <p>Settings that dictate how SickRage handles subtitles search results.</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox"
                               class="enabler" ${('', ' checked="checked"')[bool(sickrage.srCore.srConfig.USE_SUBTITLES)]}
                               id="use_subtitles" name="use_subtitles">
                        <label for="use_subtitles">Search Subtitles</label>
                    </div>
                </div>

                <div id="content_use_subtitles">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Subtitle Languages')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-flag"></span>
                                </div>
                                <input class="form-control "
                                       id="subtitles_languages"
                                       name="subtitles_languages"
                                       title="Select subtitle languages"
                                       value="${','.join(code for code in sickrage.subtitles.wanted_languages())}"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Subtitles History')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="subtitles_history"
                                   id="subtitles_history" ${('', 'checked')[bool(sickrage.srCore.srConfig.SUBTITLES_HISTORY)]}/>
                            <label for="subtitles_history"><p>Log downloaded Subtitle on History page?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Subtitles Multi-Language')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="subtitles_multi"
                                   id="subtitles_multi" ${('', 'checked')[bool(sickrage.srCore.srConfig.SUBTITLES_MULTI)]}/>
                            <label for="subtitles_multi"><p>Append language codes to subtitle filenames?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Embedded Subtitles')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="embedded_subtitles_all"
                                   id="embedded_subtitles_all" ${('', 'checked')[bool(sickrage.srCore.srConfig.EMBEDDED_SUBTITLES_ALL)]}/>
                            <label for="embedded_subtitles_all">
                                Ignore subtitles embedded inside video file?<br/>
                                <b>Warning: </b>this will ignore <u>all</u> embedded subtitles for every video file!
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Hearing Impaired Subtitles')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="subtitles_hearing_impaired"
                                   id="subtitles_hearing_impaired" ${('', 'checked')[bool(sickrage.srCore.srConfig.SUBTITLES_HEARING_IMPAIRED)]}/>
                            <label for="subtitles_hearing_impaired"><p>Download hearing impaired style subtitles?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Subtitle Directory')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-folder-open"></span>
                                </div>
                                <input value="${sickrage.srCore.srConfig.SUBTITLES_DIR}"
                                       id="subtitles_dir"
                                       name="subtitles_dir" class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="subtitles_dir">
                                The directory where SickRage should store your <i>Subtitles</i> files.<br/>
                                <b>NOTE:</b> Leave empty if you want store subtitle in episode path.
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Subtitle Find Frequency')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-time"></span>
                                </div>
                                <input type="number" name="subtitles_finder_frequency"
                                       value="${sickrage.srCore.srConfig.SUBTITLE_SEARCHER_FREQ}" hours="1"
                                       placeholder="1"
                                       title="time in hours between scans"
                                       class="form-control"/>
                                <div class="input-group-addon">
                                    hours
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Extra Scripts')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-file"></span>
                                </div>
                                <input name="subtitles_extra_scripts" id="subtitles_extra_scripts"
                                       value="<% '|'.join(sickrage.srCore.srConfig.SUBTITLES_EXTRA_SCRIPTS) %>"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="subtitles_extra_scripts"><b>NOTE:</b>
                                <ul>
                                    <li>
                                        See <a
                                            href="https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/Subtitle%20Scripts">
                                        <span style="color: red; "><b>Wiki</b></span></a> for a script arguments
                                        description.
                                    </li>
                                    <li>Additional scripts separated by <b>|</b>.</li>
                                    <li>Scripts are called after each episode has searched and downloaded subtitles.
                                    </li>
                                    <li>For any scripted languages, include the interpreter executable before the
                                        script.
                                        See
                                        the following example:
                                    </li>
                                    <ul>
                                        <li>
                                            For Windows:
                                            <pre>C:\Python27\pythonw.exe C:\Script\test.py</pre>
                                        </li>
                                        <li>
                                            For Linux:
                                            <pre>python /Script/test.py</pre>
                                        </li>
                                    </ul>
                                </ul>
                            </label>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input type="submit" class="btn config_submitter" value="Save Changes"/>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Subtitle Plugins</h3>
                <p>Check off and drag the plugins into the order you want them to be used.</p>
                <p class="note">At least one plugin is required.</p>
                <p class="note"><span style="font-size: 16px;">*</span> Web-scraping plugin</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row">
                    <div class="col-md-12">
                        <ul id="service_order_list">
                            % for curService in sickrage.subtitles.sortedServiceList():
                                <li class="ui-state-default" id="${curService['name']}">
                                    <input type="checkbox" id="enable_${curService['name']}"
                                           class="service_enabler" ${('', 'checked')[curService['enabled'] == True]}/>
                                    <label for="enable_${curService['name']}">
                                        <a href="${anon_url(curService['url'])}" class="imgLink" target="_new">
                                            <img src="${srWebRoot}/images/subtitles/${curService['image']}"
                                                 alt="${curService['url']}" title="${curService['url']}" width="16"
                                                 height="16" style="vertical-align:middle;"/>
                                        </a>
                                        <span style="vertical-align:middle;">${curService['name'].capitalize()}</span>
                                        <i class="fa fa-arrows-v blue-text pull-right"
                                           style="vertical-align:middle;"></i>
                                        <i class="fa ${('fa-unlock green-text','fa-lock red-text')[curService['name'] in providerLoginDict]} pull-right"
                                           style="vertical-align:middle;"></i>
                                    </label>
                                </li>
                            % endfor
                        </ul>
                    </div>
                </div>

                <input type="hidden" name="service_order" id="service_order"
                       value="<% ''.join(['%s:%d' % (x['name'], x['enabled']) for x in sickrage.subtitles.sortedServiceList()])%>"/>

                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    <div id="core-tab-pane3" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>Subtitle Settings</h3>
                <p>Set user and password for each provider</p>
            </div><!-- /tab-pane-desc //-->

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                % for curService in sickrage.subtitles.sortedServiceList():
                    % if curService['name'] in providerLoginDict.keys():
                    ##<div class="field-pair${(' hidden', '')[curService['enabled']}"> ## Need js to show/hide on save

                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${curService['name'].capitalize()} ${_('User Name')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="${curService['name']}_user"
                                           id="${curService['name']}_user"
                                           value="${providerLoginDict[curService['name']]['user']}"
                                           title="${curService['name'].capitalize()} User Name"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${curService['name'].capitalize()} ${_('Password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
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
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane3 //-->
</%block>