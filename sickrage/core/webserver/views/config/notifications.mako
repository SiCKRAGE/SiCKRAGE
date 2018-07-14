<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveNotifications' %></%def>
<%!
    import re

    import sickrage
    from sickrage.core.traktapi import srTraktAPI
    from sickrage.core.helpers import anon_url
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickrage.indexers import IndexerApi
%>
<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link bg-dark text-white" href="#home-theater-nas">${_('Home Theater')} / ${_('NAS')}</a></li>
    <li class="nav-item px-1"><a class="nav-link bg-dark text-white" href="#devices">${_('Devices')}</a></li>
    <li class="nav-item px-1"><a class="nav-link bg-dark text-white" href="#social">${_('Social')}</a></li>
</%block>
<%block name="pages">
    <div id="home-theater-nas" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/kodi.png" alt=""
                     title="KODI"/>
                <h3><a href="${anon_url('http://kodi.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">KODI</a></h3>
                <p>${_('A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_kodi"
                               id="use_kodi" ${('', 'checked')[bool(sickrage.app.config.use_kodi)]}/>
                        <label for="use_kodi">${_('send KODI commands?')}</label>
                    </div>
                </div>

                <div id="content_use_kodi">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Always on')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_always_on"
                                   id="kodi_always_on" ${('', 'checked')[bool(sickrage.app.config.kodi_always_on)]}/>
                            <label for="kodi_always_on">
                                <p>${_('log errors when unreachable?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_onsnatch"
                                   id="kodi_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_onsnatch)]}/>
                            <label for="kodi_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_ondownload"
                                   id="kodi_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_ondownload)]}/>
                            <label for="kodi_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_onsubtitledownload"
                                   id="kodi_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_onsubtitledownload)]}/>
                            <label for="kodi_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Update library')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_library"
                                   id="kodi_update_library" ${('', 'checked')[bool(sickrage.app.config.kodi_update_library)]}/>
                            <label for="kodi_update_library">
                                <p>${_('update KODI library when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Full library update')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_full"
                                   id="kodi_update_full" ${('', 'checked')[bool(sickrage.app.config.kodi_update_full)]}/>
                            <label for="kodi_update_full">
                                <p>${_('perform a full library update if update per-show fails?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Only update first host')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_onlyfirst"
                                   id="kodi_update_onlyfirst" ${('', 'checked')[bool(sickrage.app.config.kodi_update_onlyfirst)]}/>
                            <label for="kodi_update_onlyfirst">
                                <p>${_('only send library updates to the first active host?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('KODI IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-globe"></span>
                                    </span>
                                </div>
                                <input name="kodi_host" id="kodi_host"
                                       value="${sickrage.app.config.kodi_host}"
                                       placeholder="${_('ex. 192.168.1.100:8080, 192.168.1.101:8080')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('KODI username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-user"></span>
                                    </span>
                                </div>
                                <input name="kodi_username" id="kodi_username"
                                       value="${sickrage.app.config.kodi_username}"
                                       class="form-control"
                                       placeholder="${_('blank = no authentication')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('KODI password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-lock"></span>
                                    </span>
                                </div>
                                <input type="password" name="kodi_password" id="kodi_password"
                                       value="${sickrage.app.config.kodi_password}"
                                       class="form-control"
                                       placeholder="${_('blank = no authentication')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testKODI-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test KODI')}" id="testKODI"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_kodi //-->
            </fieldset>
        </div><!-- /kodi tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/plex.png" alt=""
                     title="Plex Media Server"/>
                <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Plex Media Server</a></h3>
                <p>${_('Experience your media on a visually stunning, easy to use interface on your Mac connected to your TV. Your media library has never looked this good!')}</p>
                <p class="plexinfo hide">${_('For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port')}
                    <b>3005</b>.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_plex"
                               id="use_plex" ${('', 'checked')[bool(sickrage.app.config.use_plex)]}/>
                        <label for="use_plex">
                            <p>${_('send Plex commands?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_plex">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Plex Media Server Auth Token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-cloud"></span>
                                            </span>
                                        </div>
                                        <input name="plex_server_token" id="plex_server_token"
                                               value="${sickrage.app.config.plex_server_token}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="plex_server_token">
                                        ${_('Auth Token used by Plex')}
                                        (<a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}"
                                            rel="noreferrer"
                                            onclick="window.open(this.href, '_blank'); return false;">
                                        <u>${_('Finding your account token')}</u></a>)
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Server Username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="plex_username" id="plex_username"
                                           value="${sickrage.app.config.plex_username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Server/client password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="plex_password" id="plex_password"
                                           value="${sickrage.app.config.plex_password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Update server library')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="plex_update_library"
                                       id="plex_update_library" ${('', 'checked')[bool(sickrage.app.config.plex_update_library)]}/>
                                <label for="plex_update_library">
                                    ${_('update Plex Media Server library after download finishes')}
                                </label>
                            </div>
                        </div>
                        <div id="content_plex_update_library">
                            <div class="form-row form-group">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Plex Media Server IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                        </div>
                                        <input name="plex_server_host"
                                               id="plex_server_host"
                                               placeholder="${_('ex. 192.168.1.1:32400, 192.168.1.2:32400')}"
                                               value="${re.sub(r'\b,\b', ', ', sickrage.app.config.plex_server_host)}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPMS-result">
                                        ${_('Click below to test Plex servers')}
                                    </div>
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="col-md-12">
                                    <input class="btn btn-secondary" type="button" value="${_('Test Plex Server')}" id="testPMS"/>
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </div><!-- /content_use_plex -->
            </fieldset>
        </div><!-- /plex media server tab-pane -->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/plex.png" alt=""
                     title="Plex Media Client"/>
                <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">${_('Plex Media Client')}</a></h3>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_plex"
                               id="use_plex_client" ${('', 'checked')[bool(sickrage.app.config.use_plex_client)]}/>
                        <label for="use_plex_client">
                            <p>${_('send Plex commands?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_plex_client">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_onsnatch"
                                   id="plex_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.plex_notify_onsnatch)]}/>
                            <label for="plex_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_ondownload"
                                   id="plex_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.plex_notify_ondownload)]}/>
                            <label for="plex_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_onsubtitledownload"
                                   id="plex_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.plex_notify_onsubtitledownload)]}/>
                            <label for="plex_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Plex Client IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="plex_host" id="plex_host"
                                       value="${sickrage.app.config.plex_host}"
                                       placeholder="${_('ex. 192.168.1.100:3000, 192.168.1.101:3000')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-row form-group">

                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Server Username')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-user"></span></span>
                                    </div>
                                    <input name="plex_client_username" id="plex_client_username"
                                           value="${sickrage.app.config.plex_client_username}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Client Password')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input type="password" name="plex_client_password" id="plex_client_password"
                                           value="${sickrage.app.config.plex_client_password}"
                                           placeholder="${_('blank = no authentication')}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="testNotification" id="testPMC-result">
                                    ${_('Click below to test Plex client(s)')}
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <input class="btn btn-secondary" type="button" value="${_('Test Plex Client')}" id="testPMC"/>
                                <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                            </div>
                        </div>
                    </div>
                </div><!-- /content_use_plex_client -->
            </fieldset>
        </div><!-- /plex client tab-pane -->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/emby.png" alt=""
                     title="Emby"/>
                <h3><a href="${anon_url('http://emby.media/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Emby</a></h3>
                <p>${_('A home media server built using other popular open source technologies.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_emby"
                               id="use_emby" ${('', 'checked')[bool(sickrage.app.config.use_emby)]} />
                        <label class="control-label" for="use_emby">
                            ${_('send update commands to Emby?')}
                        </label>
                    </div>
                </div>
                <div id="content_use_emby">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Emby IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="emby_host" id="emby_host"
                                       value="${sickrage.app.config.emby_host}"
                                       placeholder="${_('ex. 192.168.1.100:8096')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Emby API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="emby_apikey" id="emby_apikey"
                                       value="${sickrage.app.config.emby_apikey}"
                                       class="form-control"
                                       autocapitalize="off" title="Emby API key"/>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="emby_notify_onsnatch"
                                   id="emby_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.emby_notify_onsnatch)]}/>
                            <label for="emby_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="emby_notify_ondownload"
                                   id="emby_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.emby_notify_ondownload)]}/>
                            <label for="emby_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="emby_notify_onsubtitledownload"
                                   id="emby_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.emby_notify_onsubtitledownload)]}/>
                            <label for="emby_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testEMBY-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Emby')}" id="testEMBY"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_emby //-->
            </fieldset>
        </div><!-- /emby tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nmj.png" alt=""
                     title="Networked Media Jukebox"/>
                <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">NMJ</a></h3>
                <p>${_('The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nmj"
                               id="use_nmj" ${('', 'checked')[bool(sickrage.app.config.use_nmj)]}/>
                        <label for="use_nmj">
                            <p>${_('send update commands to NMJ?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_nmj">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Popcorn IP address')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="nmj_host" id="nmj_host"
                                       value="${sickrage.app.config.nmj_host}"
                                       placeholder="${_('ex. 192.168.1.100')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Get settings')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input class="btn btn-secondary btn-inline" type="button" value="${_('Get Settings')}"
                                   id="settingsNMJ"/>
                            <label for="settingsNMJ">
                                ${_('the Popcorn Hour device must be powered on and NMJ running.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('NMJ database')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <input name="nmj_database" id="nmj_database"
                                       value="${sickrage.app.config.nmj_database}"
                                       class="form-control"
                                       placeholder="${_('automatically filled via the Get Settings')}"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.app.config.nmj_database == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('NMJ mount url')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <input name="nmj_mount" id="nmj_mount"
                                       value="${sickrage.app.config.nmj_mount}"
                                       class="form-control"
                                       placeholder="${_('automatically filled via the Get Settings')}"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.app.config.nmj_mount == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMJ-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test NMJ')}" id="testNMJ"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_nmj //-->
            </fieldset>
        </div><!-- /nmj tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nmj.png" alt=""
                     title="Networked Media Jukebox v2"/>
                <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">NMJv2</a></h3>
                <p>${_('The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nmjv2"
                               id="use_nmjv2" ${('', 'checked')[bool(sickrage.app.config.use_nmjv2)]}/>
                        <label for="use_nmjv2">
                            <p>${_('send update commands to NMJv2?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_nmjv2">
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Popcorn IP address')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="nmjv2_host" id="nmjv2_host"
                                       value="${sickrage.app.config.nmjv2_host}"
                                       placeholder="${_('ex. 192.168.1.100')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Database location')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="radio" NAME="nmjv2_dbloc" VALUE="local"
                                           id="NMJV2_DBLOC_A" ${('', 'checked')[sickrage.app.config.nmjv2_dbloc == 'local']}/>PCH
                                    <label for="NMJV2_DBLOC_A" class="space-right">
                                        ${_('Local Media')}
                                    </label>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="radio" NAME="nmjv2_dbloc" VALUE="network"
                                           id="NMJV2_DBLOC_B" ${('', 'checked')[sickrage.app.config.nmjv2_dbloc == 'network']}/>
                                    <label for="NMJV2_DBLOC_B">
                                        ${_('PCH Network Media')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Database instance')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <select id="NMJv2db_instance" class="form-control ">
                                    <option value="0">#1</option>
                                    <option value="1">#2</option>
                                    <option value="2">#3</option>
                                    <option value="3">#4</option>
                                    <option value="4">#5</option>
                                    <option value="5">#6</option>
                                    <option value="6">#7</option>
                                </select>
                            </div>
                            <label for="NMJv2db_instance">
                                ${_('adjust this value if the wrong database is selected.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Find database')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="button" class="btn btn-secondary btn-inline" value="${_('Find Database')}"
                                   id="settingsNMJv2"/>
                            <label for="settingsNMJv2">
                                ${_('the Popcorn Hour device must be powered on.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('NMJv2 database')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <input name="nmjv2_database" id="nmjv2_database"
                                       value="${sickrage.app.config.nmjv2_database}"
                                       class="form-control"
                                       placeholder="${_('automatically filled via the Find Database')}"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.app.config.nmjv2_database == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMJv2-result">${_('Click below to test.')}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test NMJv2')}" id="testNMJv2"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_nmjv2 //-->
            </fieldset>
        </div><!-- /nmjv2 tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/synoindex.png" alt=""
                     title="Synology"/>
                <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Synology</a></h3>
                <p>${_('The Synology DiskStation NAS.')}</p>
                <p>${_('Synology Indexer is the daemon running on the Synology NAS to build its media database.')}</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_synoindex"
                               id="use_synoindex" ${('', 'checked')[bool(sickrage.app.config.use_synoindex)]}/>
                        <label for="use_synoindex">
                            ${_('send Synology notifications?')}<br/>
                            <b>${_('NOTE:')}</b> ${_('requires SickRage to be running on your Synology NAS.')}
                        </label>
                    </div>
                </div>

                <div id="content_use_synoindex">
                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_synoindex //-->
            </fieldset>
        </div><!-- /synoindex tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/synologynotifier.png" alt=""
                     title="Synology Indexer"/>
                <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Synology ${_('Notifier')}</a></h3>
                <p>${_('Synology Notifier is the notification system of Synology DSM')}</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_synologynotifier"
                               id="use_synologynotifier" ${('', 'checked')[bool(sickrage.app.config.use_synologynotifier)]}/>
                        <label for="use_synologynotifier">
                            ${_('send notifications to the Synology Notifier?')}<br/>
                            <b>${_('NOTE:')}</b> ${_('requires SickRage to be running on your Synology DSM.')}
                        </label>
                    </div>
                </div>
                <div id="content_use_synologynotifier">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_onsnatch"
                                   id="synologynotifier_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_onsnatch)]}/>
                            <label for="synologynotifier_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_ondownload"
                                   id="synologynotifier_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_ondownload)]}/>
                            <label for="synologynotifier_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_onsubtitledownload"
                                   id="synologynotifier_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_onsubtitledownload)]}/>
                            <label for="synologynotifier_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div><!-- /synology notifier tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pytivo.png" alt=""
                     title="pyTivo"/>
                <h3><a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">pyTivo</a>
                </h3>
                <p>${_('pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pytivo"
                               id="use_pytivo" ${('', 'checked')[bool(sickrage.app.config.use_pytivo)]}/>
                        <label for="use_pytivo">
                            ${_('send notifications to pyTivo?')}<br/>
                            <b>${_('NOTE:')}</b> ${_('requires the downloaded files to be accessible by pyTivo.')}
                        </label>
                    </div>
                </div>

                <div id="content_use_pytivo">
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('pyTivo IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="pytivo_host" id="pytivo_host"
                                       value="${sickrage.app.config.pytivo_host}"
                                       class="form-control"
                                       placeholder="${_('ex. 192.168.1.1:9032')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('pyTivo share name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-book"></span></span>
                                </div>
                                <input name="pytivo_share_name" id="pytivo_share_name"
                                       value="${sickrage.app.config.pytivo_share_name}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pytivo_share_name">
                                ${_('value used in pyTivo Web Configuration to name the share.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Tivo name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-book"></span></span>
                                </div>
                                <input name="pytivo_tivo_name" id="pytivo_tivo_name"
                                       value="${sickrage.app.config.pytivo_tivo_name}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pytivo_tivo_name">
                                ${_('(Messages and Settings > Account and System Information > System Information > DVR name)')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_pytivo //-->
            </fieldset>
        </div><!-- /tab-pane //-->
    </div>

    <div id="devices" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/growl.png" alt=""
                     title="Growl"/>
                <h3><a href="${anon_url('http://growl.info/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Growl</a></h3>
                <p>${_('A cross-platform unobtrusive global notification system.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_growl"
                               id="use_growl" ${('', 'checked')[bool(sickrage.app.config.use_growl)]}/>
                        <label for="use_growl">
                            <p>${_('send Growl notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_growl">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_onsnatch"
                                   id="growl_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.growl_notify_onsnatch)]}/>
                            <label for="growl_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_ondownload"
                                   id="growl_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.growl_notify_ondownload)]}/>
                            <label for="growl_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_onsubtitledownload"
                                   id="growl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.growl_notify_onsubtitledownload)]}/>
                            <label for="growl_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Growl IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="growl_host" id="growl_host"
                                       value="${sickrage.app.config.growl_host}"
                                       placeholder="${_('ex. 192.168.1.100:23053')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Growl password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                </div>
                                <input type="password" name="growl_password" id="growl_password"
                                       value="${sickrage.app.config.growl_password}"
                                       class="form-control"
                                       placeholder="${_('blank = no authentication')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testGrowl-result">
                                ${_('Click below to rex.ster and test Growl, this is required for Growl notifications to work.')}
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Register Growl')}" id="testGrowl"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_growl //-->

            </fieldset>
        </div><!-- /growl tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/prowl.png" alt="Prowl"
                     title="Prowl"/>
                <h3><a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Prowl</a></h3>
                <p>${_('A Growl client for iOS.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_prowl"
                               id="use_prowl" ${('', 'checked')[bool(sickrage.app.config.use_prowl)]}/>
                        <label for="use_prowl">
                            <p>${_('send Prowl notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_prowl">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_onsnatch"
                                   id="prowl_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_onsnatch)]}/>
                            <label for="prowl_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_ondownload"
                                   id="prowl_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_ondownload)]}/>
                            <label for="prowl_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_onsubtitledownload"
                                   id="prowl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_onsubtitledownload)]}/>
                            <label for="prowl_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Prowl API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="prowl_api" id="prowl_api"
                                       value="${sickrage.app.config.prowl_api}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="prowl_api">
                                ${_('get your key at:')}
                                <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;">https://www.prowlapp.com/api_settings.php</a>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Prowl priority')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-exclamation"></span>
                                    </span>
                                </div>
                                <select id="prowl_priority" name="prowl_priority" class="form-control ">
                                    <option value="-2" ${('', 'selected')[sickrage.app.config.prowl_priority == '-2']}>
                                        Very Low
                                    </option>
                                    <option value="-1" ${('', 'selected')[sickrage.app.config.prowl_priority == '-1']}>
                                        Moderate
                                    </option>
                                    <option value="0" ${('', 'selected')[sickrage.app.config.prowl_priority == '0']}>
                                        Normal
                                    </option>
                                    <option value="1" ${('', 'selected')[sickrage.app.config.prowl_priority == '1']}>
                                        High
                                    </option>
                                    <option value="2" ${('', 'selected')[sickrage.app.config.prowl_priority == '2']}>
                                        Emergency
                                    </option>
                                </select>
                            </div>
                            <label for="prowl_priority">
                                ${_('priority of Prowl messages from SickRage.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testProwl-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Prowl')}" id="testProwl"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_prowl //-->

            </fieldset>
        </div><!-- /prowl tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/libnotify.png" alt=""
                     title="Libnotify"/>
                <h3><a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Libnotify</a></h3>
                <p>
                    ${_('The standard desktop notification API for Linux/*nix systems. This notifier will only function if the pynotify module is installed')}
                    (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).
                </p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_libnotify"
                               id="use_libnotify" ${('', 'checked')[bool(sickrage.app.config.use_libnotify)]}/>
                        <label for="use_libnotify">
                            <p>${_('send Libnotify notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_libnotify">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_onsnatch"
                                   id="libnotify_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_onsnatch)]}/>
                            <label for="libnotify_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_ondownload"
                                   id="libnotify_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_ondownload)]}/>
                            <label for="libnotify_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_onsubtitledownload"
                                   id="libnotify_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_onsubtitledownload)]}/>
                            <label for="libnotify_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testLibnotify-result">${_('Click below to test.')}</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Libnotify')}" id="testLibnotify"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_libnotify //-->
            </fieldset>
        </div><!-- /libnotify tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushover.png" alt=""
                     title="Pushover"/>
                <h3><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushover</a></h3>
                <p>${_('Pushover makes it easy to send real-time notifications to your Android and iOS devices.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushover"
                               id="use_pushover" ${('', 'checked')[bool(sickrage.app.config.use_pushover)]}/>
                        <label for="use_pushover">
                            <p>${_('send Pushover notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_pushover">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_onsnatch"
                                   id="pushover_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_onsnatch)]}/>
                            <label for="pushover_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_ondownload"
                                   id="pushover_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_ondownload)]}/>
                            <label for="pushover_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_onsubtitledownload"
                                   id="pushover_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_onsubtitledownload)]}/>
                            <label for="pushover_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushover key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                </div>
                                <input name="pushover_userkey" id="pushover_userkey"
                                       value="${sickrage.app.config.pushover_userkey}"
                                       class="form-control"
                                       placeholder="${_('user key of your Pushover account')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushover API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="pushover_apikey" id="pushover_apikey"
                                       value="${sickrage.app.config.pushover_apikey}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pushover_apikey">
                                <a href="${anon_url('https://pushover.net/apps/clone/sickrage')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;"><b>${_('Click here')}</b></a> ${_('to create a Pushover API key')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushover devices')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list-alt"></span></span>
                                </div>
                                <input name="pushover_device" id="pushover_device"
                                       value="${sickrage.app.config.pushover_device}"
                                       placeholder="${_('ex. device1,device2')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushover notification sound')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-music"></span></span>
                                </div>
                                <select id="pushover_sound" name="pushover_sound" class="form-control ">
                                    <option value="pushover" ${('', 'selected')[sickrage.app.config.pushover_sound == 'pushover']}>
                                        ${_('Pushover')}
                                    </option>
                                    <option value="bike" ${('', 'selected')[sickrage.app.config.pushover_sound == 'bike']}>
                                        ${_('Bike')}
                                    </option>
                                    <option value="bugle" ${('', 'selected')[sickrage.app.config.pushover_sound == 'bugle']}>
                                        ${_('Bugle')}
                                    </option>
                                    <option value="cashregister" ${('', 'selected')[sickrage.app.config.pushover_sound == 'cashregister']}>
                                        ${_('Cash Register')}
                                    </option>
                                    <option value="classical" ${('', 'selected')[sickrage.app.config.pushover_sound == 'classical']}>
                                        ${_('Classical')}
                                    </option>
                                    <option value="cosmic" ${('', 'selected')[sickrage.app.config.pushover_sound == 'cosmic']}>
                                        ${_('Cosmic')}
                                    </option>
                                    <option value="falling" ${('', 'selected')[sickrage.app.config.pushover_sound == 'falling']}>
                                        ${_('Falling')}
                                    </option>
                                    <option value="gamelan" ${('', 'selected')[sickrage.app.config.pushover_sound == 'gamelan']}>
                                        ${_('Gamelan')}
                                    </option>
                                    <option value="incoming" ${('', 'selected')[sickrage.app.config.pushover_sound == 'incoming']}>
                                        ${_('Incoming')}
                                    </option>
                                    <option value="intermission" ${('', 'selected')[sickrage.app.config.pushover_sound == 'intermission']}>
                                        ${_('Intermission')}
                                    </option>
                                    <option value="magic" ${('', 'selected')[sickrage.app.config.pushover_sound == 'magic']}>
                                        ${_('Magic')}
                                    </option>
                                    <option value="mechanical" ${('', 'selected')[sickrage.app.config.pushover_sound == 'mechanical']}>
                                        ${_('Mechanical')}
                                    </option>
                                    <option value="pianobar" ${('', 'selected')[sickrage.app.config.pushover_sound == 'pianobar']}>
                                        ${_('Piano Bar')}
                                    </option>
                                    <option value="siren" ${('', 'selected')[sickrage.app.config.pushover_sound == 'siren']}>
                                        ${_('Siren')}
                                    </option>
                                    <option value="spacealarm" ${('', 'selected')[sickrage.app.config.pushover_sound == 'spacealarm']}>
                                        ${_('Space Alarm')}
                                    </option>
                                    <option value="tugboat" ${('', 'selected')[sickrage.app.config.pushover_sound == 'tugboat']}>
                                        ${_('Tug Boat')}
                                    </option>
                                    <option value="alien" ${('', 'selected')[sickrage.app.config.pushover_sound == 'alien']}>
                                        ${_('Alien Alarm (long)')}
                                    </option>
                                    <option value="climb" ${('', 'selected')[sickrage.app.config.pushover_sound == 'climb']}>
                                        ${_('Climb (long)')}
                                    </option>
                                    <option value="persistent" ${('', 'selected')[sickrage.app.config.pushover_sound == 'persistent']}>
                                        ${_('Persistent (long)')}
                                    </option>
                                    <option value="echo" ${('', 'selected')[sickrage.app.config.pushover_sound == 'echo']}>
                                        ${_('Pushover Echo (long)')}
                                    </option>
                                    <option value="updown" ${('', 'selected')[sickrage.app.config.pushover_sound == 'updown']}>
                                        ${_('Up Down (long)')}
                                    </option>
                                    <option value="none" ${('', 'selected')[sickrage.app.config.pushover_sound == 'none']}>
                                        ${_('None (silent)')}
                                    </option>
                                    <option value="default" ${('', 'selected')[sickrage.app.config.pushover_sound == 'default']}>
                                        ${_('Device specific')}
                                    </option>
                                </select>
                            </div>
                            <label for="pushover_sound">
                                ${_('Choose notification sound to use')}
                            </label>
                        </div>
                    </div>
                    <div class="testNotification" id="testPushover-result">Click below to test.</div>
                    <input class="btn btn-secondary" type="button" value="${_('Test Pushover')}" id="testPushover"/>
                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                </div><!-- /content_use_pushover //-->

            </fieldset>
        </div><!-- /pushover tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/boxcar2.png" alt=""
                     title="Boxcar2"/>
                <h3><a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Boxcar2</a></h3>
                <p>${_('Read your messages where and when you want them!')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_boxcar2"
                               id="use_boxcar2" ${('', 'checked')[bool(sickrage.app.config.use_boxcar2)]}/>
                        <label for="use_boxcar2">
                            <p>${_('send Boxcar2 notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_boxcar2">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_onsnatch"
                                   id="boxcar2_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_onsnatch)]}/>
                            <label for="boxcar2_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_ondownload"
                                   id="boxcar2_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_ondownload)]}/>
                            <label for="boxcar2_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_onsubtitledownload"
                                   id="boxcar2_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_onsubtitledownload)]}/>
                            <label for="boxcar2_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Boxcar2 access token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="boxcar2_accesstoken" id="boxcar2_accesstoken"
                                       value="${sickrage.app.config.boxcar2_accesstoken}"
                                       placeholder="${_('access token for your Boxcar2 account')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testBoxcar2-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Boxcar2')}" id="testBoxcar2"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_boxcar2 //-->

            </fieldset>
        </div><!-- /boxcar2 tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nma.png" alt="" title="NMA"/>
                <h3><a href="${anon_url('http://nma.usk.bz')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Notify My Android</a></h3>
                <p>${_('Notify My Android is a Prowl-like Android App and API that offers an easy way to send notifications from your application directly to your Android device.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nma"
                               id="use_nma" ${('', 'checked')[bool(sickrage.app.config.use_nma)]}/>
                        <label for="use_nma">
                            <p>${_('send NMA notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_nma">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_onsnatch"
                                   id="nma_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.nma_notify_onsnatch)]}/>
                            <label for="nma_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_ondownload"
                                   id="nma_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.nma_notify_ondownload)]}/>
                            <label for="nma_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_onsubtitledownload"
                                   id="nma_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.nma_notify_onsubtitledownload)]}/>
                            <label for="nma_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('NMA API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="nma_api" id="nma_api"
                                       value="${sickrage.app.config.nma_api}"
                                       placeholder="${_('ex. key1,key2 (max 5)')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('NMA priority')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-exclamation-sign"></span></span>
                                </div>
                                <select id="nma_priority" name="nma_priority" class="form-control ">
                                    <option value="-2" ${('', 'selected')[sickrage.app.config.nma_priority == '-2']}>
                                        ${_('Very Low')}
                                    </option>
                                    <option value="-1" ${('', 'selected')[sickrage.app.config.nma_priority == '-1']}>
                                        ${_('Moderate')}
                                    </option>
                                    <option value="0" ${('', 'selected')[sickrage.app.config.nma_priority == '0']}>
                                        ${_('Normal')}
                                    </option>
                                    <option value="1" ${('', 'selected')[sickrage.app.config.nma_priority == '1']}>
                                        ${_('High')}
                                    </option>
                                    <option value="2" ${('', 'selected')[sickrage.app.config.nma_priority == '2']}>
                                        ${_('Emergency')}
                                    </option>
                                </select>
                            </div>
                            <label for="nma_priority">
                                ${_('priority of NMA messages from SickRage.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMA-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test NMA')}" id="testNMA"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_nma //-->

            </fieldset>
        </div><!-- /nma tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushalot.png" alt=""
                     title="Pushalot"/>
                <h3><a href="${anon_url('https://pushalot.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushalot</a></h3>
                <p>${_('Pushalot is a platform for receiving custom push notifications to connected devices running Windows Phone or Windows 8.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushalot"
                               id="use_pushalot" ${('', 'checked')[bool(sickrage.app.config.use_pushalot)]}/>
                        <label for="use_pushalot">
                            <p>${_('send Pushalot notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_pushalot">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_onsnatch"
                                   id="pushalot_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_onsnatch)]}/>
                            <label for="pushalot_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_ondownload"
                                   id="pushalot_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_ondownload)]}/>
                            <label for="pushalot_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_onsubtitledownload"
                                   id="pushalot_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_onsubtitledownload)]}/>
                            <label for="pushalot_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushalot authorization token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="pushalot_authorizationtoken"
                                       id="pushalot_authorizationtoken"
                                       value="${sickrage.app.config.pushalot_authorizationtoken}"
                                       placeholder="${_('authorization token of your Pushalot account.')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testPushalot-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn btn-secondary" value="${_('Test Pushalot')}" id="testPushalot"/>
                            <input type="submit" class="btn btn-secondary config_submitter" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_pushalot //-->

            </fieldset>
        </div><!-- /pushalot tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushbullet.png" alt=""
                     title="Pushbullet"/>
                <h3><a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushbullet</a></h3>
                <p>${_('Pushbullet is a platform for receiving custom push notifications to connected devices running Android and desktop Chrome browsers.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushbullet"
                               id="use_pushbullet" ${('', 'checked')[bool(sickrage.app.config.use_pushbullet)]}/>
                        <label for="use_pushbullet">
                            <p>${_('send Pushbullet notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_pushbullet">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_onsnatch"
                                   id="pushbullet_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_onsnatch)]}/>
                            <label for="pushbullet_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_ondownload"
                                   id="pushbullet_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_ondownload)]}/>
                            <label for="pushbullet_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_onsubtitledownload"
                                   id="pushbullet_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_onsubtitledownload)]}/>
                            <label for="pushbullet_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushbullet API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="pushbullet_api" id="pushbullet_api"
                                       value="${sickrage.app.config.pushbullet_api}"
                                       class="form-control"
                                       placeholder="${_('API key of your Pushbullet account')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Pushbullet devices')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-list"></span></span>
                                        </div>
                                        <select name="pushbullet_device_list" id="pushbullet_device_list"
                                                class="form-control "></select>
                                    </div>
                                    <label for="pushbullet_device_list">${_('select device you wish to push to.')}</label>
                                </div>
                            </div>
                            <br/>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="hidden" id="pushbullet_device"
                                           value="${sickrage.app.config.pushbullet_device}">
                                    <input type="button" class="btn btn-secondary btn-inline" value="${_('Update device list')}"
                                           id="getPushbulletDevices"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testPushbullet-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn btn-secondary" value="${_('Test Pushbullet')}" id="testPushbullet"/>
                            <input type="submit" class="btn btn-secondary config_submitter" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_pushbullet //-->

            </fieldset>
        </div><!-- /pushbullet tab-pane //-->
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/freemobile.png" alt=""
                     title="Free Mobile"/>
                <h3><a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Free Mobile</a></h3>
                <p>${_('Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_freemobile"
                               id="use_freemobile" ${('', 'checked')[bool(sickrage.app.config.use_freemobile)]}/>
                        <label for="use_freemobile">
                            <p>${_('send SMS notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_freemobile">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_onsnatch"
                                   id="freemobile_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_onsnatch)]}/>
                            <label for="freemobile_notify_onsnatch">
                                <p>${_('send a SMS when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_ondownload"
                                   id="freemobile_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_ondownload)]}/>
                            <label for="freemobile_notify_ondownload">
                                <p>${_('send a SMS when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_onsubtitledownload"
                                   id="freemobile_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_onsubtitledownload)]}/>
                            <label for="freemobile_notify_onsubtitledownload">
                                <p>${_('send a SMS when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Free Mobile customer ID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-user"></span></span>
                                </div>
                                <input name="freemobile_id" id="freemobile_id"
                                       value="${sickrage.app.config.freemobile_id}"
                                       class="form-control"
                                       placeholder="${_('ex. 12345678')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Free Mobile API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="freemobile_apikey" id="freemobile_apikey"
                                       value="${sickrage.app.config.freemobile_apikey}"
                                       class="form-control"
                                       placeholder="${_('enter yourt API key')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testFreeMobile-result">
                                ${_('Click below to test your settings.')}
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test SMS')}" id="testFreeMobile"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_freemobile //-->
            </fieldset>
        </div><!-- /freemobile tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/telegram.png" alt=""
                     title="Telegram"/>
                <h3><a href="${anon_url('http://telegram.org/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Telegram</a></h3>
                <p>${_('Telegram is a cloud-based instant messaging service')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_telegram"
                               id="use_telegram" ${('', 'checked')[bool(sickrage.app.config.use_telegram)]}/>
                        <label for="use_telegram">
                            <p>${_('send Telegram notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_telegram">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="telegram_notify_onsnatch"
                                   id="telegram_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_onsnatch)]}/>
                            <label for="telegram_notify_onsnatch">
                                <p>${_('send a message when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="telegram_notify_ondownload"
                                   id="telegram_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_ondownload)]}/>
                            <label for="telegram_notify_ondownload">
                                <p>${_('send a message when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="telegram_notify_onsubtitledownload"
                                   id="telegram_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_onsubtitledownload)]}/>
                            <label for="telegram_notify_onsubtitledownload">
                                <p>${_('send a message when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('User/Group ID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-user"></span></span>
                                        </div>
                                        <input name="telegram_id" id="telegram_id"
                                               value="${sickrage.app.config.telegram_id}"
                                               class="form-control"
                                               placeholder="${_('ex. 12345678')}"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="telegram_id">
                                        ${_('contact @myidbot on Telegram to get an ID')}
                                    </label>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label>
                                        <b>${_('NOTE')}
                                            :</b> ${_('Don\'t forget to talk with your bot at least one time if you get a 403 error.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Bot API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                        </div>
                                        <input name="telegram_apikey" id="telegram_apikey"
                                               value="${sickrage.app.config.telegram_apikey}"
                                               class="form-control"
                                               placeholder="${_('enter yourt API key')}"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="telegram_apikey">
                                        ${_('contact @BotFather on Telegram to set up one')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTelegram-result">
                                ${_('Click below to test your settings.')}
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Telegram')}" id="testTelegram"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_telegram //-->
            </fieldset>
        </div><!-- /telegram tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/twilio.png" alt=""
                     title="Twilio"/>
                <h3><a href="${anon_url('http://www.twilio.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Twilio</a></h3>
                <p>
                    ${_('Twilio is a webservice API that allows you to communicate directly with a mobile number. This notifier will send a text directly to your mobile device.')}
                </p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_twilio"
                               id="use_twilio" ${('', 'checked')[bool(sickrage.app.config.use_twilio)]}/>
                        <label for="use_twilio">
                            <p>${_('text your mobile device?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_twilio">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twilio_notify_onsnatch"
                                   id="twilio_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_onsnatch)]}/>
                            <label for="twilio_notify_onsnatch">
                                <p>${_('send a message when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twilio_notify_ondownload"
                                   id="twilio_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_ondownload)]}/>
                            <label for="twilio_notify_ondownload">
                                <p>${_('send a message when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twilio_notify_onsubtitledownload"
                                   id="twilio_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_onsubtitledownload)]}/>
                            <label for="twilio_notify_onsubtitledownload">
                                <p>${_('send a message when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Twilio Account SID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-user"></span></span>
                                        </div>
                                        <input name="twilio_account_sid" id="twilio_account_sid"
                                               value="${sickrage.app.config.twilio_account_sid}"
                                               class="form-control"
                                               placeholder="${_('ex. 12345678')}"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="twilio_account_sid">
                                        ${_('account SID of your Twilio account.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Twilio Auth Token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="twilio_auth_token" id="twilio_auth_token"
                                       value="${sickrage.app.config.twilio_auth_token}"
                                       class="form-control"
                                       placeholder="${_('enter your auth token')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Twilio Phone SID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-hashtag"></span>
                                            </span>
                                        </div>
                                        <input name="twilio_phone_sid" id="twilio_phone_sid"
                                               value="${sickrage.app.config.twilio_phone_sid}"
                                               class="form-control"
                                               placeholder="${_('ex. 12345678')}"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="twilio_phone_sid">
                                        ${_('phone SID that you would like to send the sms from.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Your phone number')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text">
                                                <span class="fas fa-hashtag"></span>
                                            </span>
                                        </div>
                                        <input name="twilio_to_number" id="twilio_to_number"
                                               value="${sickrage.app.config.twilio_to_number}"
                                               class="form-control"
                                               placeholder="${_('ex. +1-###-###-####')}"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label for="twilio_to_number">
                                        ${_('phone number that will receive the sms.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTwilio-result">
                                ${_('Click below to test your settings.')}
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Twilio')}" id="testTwilio"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_twilio //-->
            </fieldset>
        </div><!-- /twilio tab-pane //-->
    </div>

    <div id="social" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/twitter.png" alt=""
                     title="Twitter"/>
                <h3><a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Twitter</a></h3>
                <p>${_('A social networking and microblogging service, enabling its users to send and read other users messages called tweets.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_twitter"
                               id="use_twitter" ${('', 'checked')[bool(sickrage.app.config.use_twitter)]}/>
                        <label for="use_twitter">
                            ${_('post tweets on Twitter?')}<br/>
                            <b>${_('NOTE:')}</b> ${_('you may want to use a secondary account.')}
                        </label>
                    </div>
                </div>

                <div id="content_use_twitter">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_onsnatch"
                                   id="twitter_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_onsnatch)]}/>
                            <label for="twitter_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_ondownload"
                                   id="twitter_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_ondownload)]}/>
                            <label for="twitter_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_onsubtitledownload"
                                   id="twitter_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_onsubtitledownload)]}/>
                            <label for="twitter_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Send direct message')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_usedm"
                                   id="twitter_usedm" ${('', 'checked')[bool(sickrage.app.config.twitter_usedm)]}/>
                            <label for="twitter_usedm">
                                <p>${_('send a notification via Direct Message, not via status update')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Send DM to')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-user"></span></span>
                                </div>
                                <input name="twitter_dmto" id="twitter_dmto"
                                       value="${sickrage.app.config.twitter_dmto}"
                                       class="form-control"
                                       placeholder="${_('Twitter account to send messages to')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Step One')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input class="btn btn-secondary" type="button" value="${_('Request Authorization')}" id="twitterStep1"/>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    ${_('Click the "Request Authorization" button.')}<br/>
                                    ${_('This will open a new page containing an auth key.')}<br/>
                                    <b>${_('NOTE:')}</b>${_('if nothing happens check your popup blocker.')}<br/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Step Two')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                </div>
                                <input id="twitter_key" value=""
                                       class="form-control"
                                       placeholder="${_('Enter the key Twitter gave you')}"
                                       autocapitalize="off"/>
                                <div class="input-group-append">
                                    <span class="input-group-text">
                                        <input class="button" type="button" value="Verify Key" id="twitterStep2"/>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTwitter-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Twitter')}" id="testTwitter"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_twitter //-->

            </fieldset>
        </div><!-- /twitter tab-pane //-->


        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/trakt.png" alt=""
                     title="Trakt"/>
                <h3><a href="${anon_url('http://trakt.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Trakt</a></h3>
                <p>${_('Trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, trakt recommends additional shows and movies you\'ll enjoy!')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_trakt"
                               id="use_trakt" ${('', 'checked')[bool(sickrage.app.config.use_trakt)]}/>
                        <label for="use_trakt">
                            <p>${_('send Trakt.tv notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_trakt">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Trakt username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-user"></span></span>
                                </div>
                                <input name="trakt_username" id="trakt_username"
                                       value="${sickrage.app.config.trakt_username}"
                                       class="form-control"
                                       placeholder="${_('username')}"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <input type="hidden" id="trakt_pin_url" value="${srTraktAPI()['oauth/pin'].url()}">
                    % if not sickrage.app.config.trakt_oauth_token:
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Trakt PIN')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input name="trakt_pin" id="trakt_pin" value=""
                                           placeholder="${_('authorization PIN code')}"
                                           class="form-control" autocapitalize="off"/>
                                    <div class="input-group-append">
                                        <span class="input-group-text">
                                            <a href="#" id="TraktGetPin">Get PIN</a>
                                            <a href="#" id="authTrakt" class="hide">${_('Authorize')}</a>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endif
                    <input type="button" class="btn btn-secondary hide" value="${_('Authorize SiCKRAGE')}" id="authTrakt"/>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('API Timeout')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-clock"></span>
                                    </span>
                                </div>
                                <input name="trakt_timeout" id="trakt_timeout"
                                       value="${sickrage.app.config.trakt_timeout}"
                                       class="form-control"/>
                                <div class="input-group-append">
                                    <span class="input-group-text">
                                        secs
                                    </span>
                                </div>
                            </div>
                            <label for="trakt_timeout">
                                ${_('Seconds to wait for Trakt API to respond. (Use 0 to wait forever)')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Default indexer')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-linode"></span>
                                    </span>
                                </div>
                                <select id="trakt_default_indexer" name="trakt_default_indexer"
                                        class="form-control " title="Default Indexer">
                                    % for indexer in IndexerApi().indexers:
                                        <option value="${indexer}" ${('', 'selected')[sickrage.app.config.trakt_default_indexer == indexer]}>${IndexerApi().indexers[indexer]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Sync libraries')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" class="enabler" name="trakt_sync"
                                   id="trakt_sync" ${('', 'checked')[bool(sickrage.app.config.trakt_sync)]}/>
                            <label for="trakt_sync">
                                <p>${_('sync your SickRage show library with your trakt show library.')}</p>
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Remove Episodes From Collection')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_sync_remove"
                                       id="trakt_sync_remove" ${('', 'checked')[bool(sickrage.app.config.trakt_sync_remove)]}/>
                                <label for="trakt_sync_remove">
                                    <p>${_('Remove an episode from your Trakt collection if it is not in your SickRage library.')}</p>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Sync watchlist')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" class="enabler" name="trakt_sync_watchlist"
                                   id="trakt_sync_watchlist" ${('', 'checked')[bool(sickrage.app.config.trakt_sync_watchlist)]}/>
                            <label for="trakt_sync_watchlist">
                                ${_('sync your SickRage show watchlist with your trakt show watchlist (either Show and Episode).')}
                                <br/>
                                ${_('Episode will be added on watch list when wanted or snatched and will be removed when downloaded')}
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync_watchlist">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Watchlist add method')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-binoculars"></span>
                                        </span>
                                    </div>
                                    <select id="trakt_method_add" name="trakt_method_add"
                                            class="form-control ">
                                        <option value="0" ${('', 'selected')[sickrage.app.config.trakt_method_add == 0]}>
                                            ${_('Skip All')}
                                        </option>
                                        <option value="1" ${('', 'selected')[sickrage.app.config.trakt_method_add == 1]}>
                                            ${_('Download Pilot Only')}
                                        </option>
                                        <option value="2" ${('', 'selected')[sickrage.app.config.trakt_method_add == 2]}>
                                            ${_('Get whole show')}
                                        </option>
                                    </select>
                                </div>
                                <label for="trakt_method_add">
                                    ${_('method in which to download episodes for new show\'s.')}
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Remove episode')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_watchlist"
                                       id="trakt_remove_watchlist" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_watchlist)]}/>
                                <label for="trakt_remove_watchlist">
                                    <p>${_('remove an episode from your watchlist after it is downloaded.')}</p>
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Remove series')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_serieslist"
                                       id="trakt_remove_serieslist" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_serieslist)]}/>
                                <label for="trakt_remove_serieslist">
                                    <p>${_('remove the whole series from your watchlist after any download.')}</p>
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Remove watched show')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_show_from_sickrage"
                                       id="trakt_remove_show_from_sickrage" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_show_from_sickrage)]}/>
                                <label for="trakt_remove_show_from_sickrage">
                                    <p>${_('remove the show from sickrage if it\'s ended and completely watched')}</p>
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Start paused')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_start_paused"
                                       id="trakt_start_paused" ${('', 'checked')[bool(sickrage.app.config.trakt_start_paused)]}/>
                                <label for="trakt_start_paused">
                                    <p>${_('show\'s grabbed from your trakt watchlist start paused.')}</p>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Trakt blackList name')}</label>
                        </div>
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list"></span></span>
                                </div>
                                <input name="trakt_blacklist_name" id="trakt_blacklist_name"
                                       value="${sickrage.app.config.trakt_blacklist_name}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="trakt_blacklist_name">
                                ${_('Name(slug) of list on Trakt for blacklisting show on \'Add from Trakt\' page')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTrakt-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn btn-secondary" value="${_('Test Trakt')}" id="testTrakt"/>
                            <input type="submit" class="btn btn-secondary config_submitter" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_trakt //-->
            </fieldset>
        </div><!-- /trakt tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/email.png" alt=""
                     title="Email"/>
                <h3><a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Email</a>
                </h3>
                <p>${_('Allows configuration of email notifications on a per show basis.')}</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_email"
                               id="use_email" ${('', 'checked')[bool(sickrage.app.config.use_email)]}/>
                        <label for="use_email">
                            <p>${_('send email notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_email">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_onsnatch"
                                   id="email_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.email_notify_onsnatch)]}/>
                            <label for="email_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_ondownload"
                                   id="email_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.email_notify_ondownload)]}/>
                            <label for="email_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_onsubtitledownload"
                                   id="email_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.email_notify_onsubtitledownload)]}/>
                            <label for="email_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('SMTP host')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="email_host" id="email_host"
                                       value="${sickrage.app.config.email_host}"
                                       placeholder="${_('SMTP server address')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('SMTP port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="email_port" id="email_port"
                                       value="${sickrage.app.config.email_port}"
                                       placeholder="${_('SMTP server port number')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('SMTP from')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-envelope"></span></span>
                                </div>
                                <input name="email_from" id="email_from"
                                       value="${sickrage.app.config.email_from}"
                                       placeholder="${_('sender email address')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Use TLS')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_tls"
                                   id="email_tls" ${('', 'checked')[bool(sickrage.app.config.email_tls)]}/>
                            <label for="email_tls">
                                <p>${_('check to use TLS encryption.')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('SMTP user')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-user"></span></span>
                                </div>
                                <input name="email_user" id="email_user"
                                       value="${sickrage.app.config.email_user}"
                                       placeholder="${_('optional')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('SMTP password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                </div>
                                <input type="password" name="email_password" id="email_password"
                                       value="${sickrage.app.config.email_password}"
                                       placeholder="${_('optional')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Global email list')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-envelope"></span></span>
                                </div>
                                <input name="email_list" id="email_list"
                                       value="${sickrage.app.config.email_list}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="email_list">
                                ${_('all emails here receive notifications for')} <b>${_('all')}</b> ${_('shows.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Show notification list')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-list"></span></span>
                                        </div>
                                        <select name="email_show" id="email_show" class="form-control ">
                                            <option value="-1">-- ${_('Select a Show')} --</option>
                                        </select>
                                    </div>
                                    <label for="email_show">
                                        ${_('configure per show notifications here.')}
                                    </label>
                                </div>
                            </div>
                            <br/>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-envelope"></span></span>
                                        </div>
                                        <input name="email_show_list" id="email_show_list" class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                    <label for="email_show_list">
                                        ${_('configure per-show notifications here by entering email addresses, separated by commas, after selecting a show in the drop-down box. Be sure to activate the Save for this show button below after each entry.')}
                                    </label>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input id="email_show_save" class="btn btn-secondary" type="button" value="${_('Save for this show')}"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testEmail-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Email')}" id="testEmail"/>
                            <input class="btn btn-secondary config_submitter" type="submit" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_email //-->
            </fieldset>
        </div><!-- /email tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/slack.png" alt=""
                     title="Slack"/>
                <h3><a href="${anon_url('http://www.slack.com')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Slack</a>
                </h3>
                <p>
                    ${_('Slack brings all your communication together in one place. It\'s real-time messaging, archiving and search for modern teams.')}
                </p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_slack"
                               id="use_slack" ${('', 'checked')[bool(sickrage.app.config.use_slack)]}/>
                        <label for="use_slack">
                            <p>${_('send slack notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_slack">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="slack_notify_onsnatch"
                                   id="slack_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.slack_notify_onsnatch)]}/>
                            <label for="slack_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="slack_notify_ondownload"
                                   id="slack_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.slack_notify_ondownload)]}/>
                            <label for="slack_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="slack_notify_onsubtitledownload"
                                   id="slack_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.slack_notify_onsubtitledownload)]}/>
                            <label for="slack_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Slack Incoming Webhook')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="slack_webhook" id="slack_webhook"
                                       value="${sickrage.app.config.slack_webhook}"
                                       placeholder="${_('Slack webhook')}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testSlack-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Slack')}" id="testSlack"/>
                            <input class="btn btn-secondary config_submitter" type="submit" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_slack //-->
            </fieldset>
        </div><!-- /slack tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 card-title">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/discord.png" alt=""
                     title="Discord"/>
                <h3><a href="${anon_url('http://www.discordapp.com')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Discord</a>
                </h3>
                <p>
                    ${_('All-in-one voice and text chat for gamers that\'s free, secure, and works on both your desktop and phone.')}
                </p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_discord"
                               id="use_discord" ${('', 'checked')[bool(sickrage.app.config.use_discord)]}/>
                        <label for="use_discord">
                            <p>${_('send discord notifications?')}</p>
                        </label>
                    </div>
                </div>

                <div id="content_use_discord">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="discord_notify_onsnatch"
                                   id="discord_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.discord_notify_onsnatch)]}/>
                            <label for="discord_notify_onsnatch">
                                <p>${_('send a notification when a download starts?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="discord_notify_ondownload"
                                   id="discord_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.discord_notify_ondownload)]}/>
                            <label for="discord_notify_ondownload">
                                <p>${_('send a notification when a download finishes?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="discord_notify_onsubtitledownload"
                                   id="discord_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.discord_notify_onsubtitledownload)]}/>
                            <label for="discord_notify_onsubtitledownload">
                                <p>${_('send a notification when subtitles are downloaded?')}</p>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Discord Incoming Webhook')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                        </div>
                                        <input name="discord_webhook" id="discord_webhook"
                                               value="${sickrage.app.config.discord_webhook}"
                                               placeholder="${_('Discord webhook')}"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-12">
                                <label for="discord_webhook">${_('Create webhook under channel settings.')}</label>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Discord Bot Name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                        </div>
                                        <input name="discord_name" id="discord_name"
                                               value="${sickrage.app.config.discord_name}"
                                               placeholder="${_('Discord Bot Name')}"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-12">
                                <label for="discord_name">${_('Blank will use webhook default name.')}</label>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Discord Avatar URL')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                        </div>
                                        <input name="discord_avatar_url" id="discord_avatar_url"
                                               value="${sickrage.app.config.discord_avatar_url}"
                                               placeholder="${_('Discord Avatar URL')}"
                                               class="form-control" autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-12">
                                <label for="discord_avatar_url">${_('Blank will use webhook default avatar.')}</label>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('Discord TTS')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="discord_tts"
                                   id="discord_tts" ${('', 'checked="checked"')[bool(sickrage.app.config.discord_tts)]}/>
                            <label for="discord_tts">${_('Send notifications using text-to-speech.')}</label>
                        </div>
                    </div>


                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testDiscord-result">${_('Click below to test.')}</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn btn-secondary" type="button" value="${_('Test Discord')}" id="testDiscord"/>
                            <input class="btn btn-secondary config_submitter" type="submit" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_discord //-->
            </fieldset>
        </div><!-- /discord tab-pane //-->
    </div>
</%block>
