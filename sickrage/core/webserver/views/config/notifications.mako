<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveNotifications' %></%def>
<%!
    import re

    import sickrage
    from sickrage.core.traktapi import TraktAPI
    from sickrage.core.helpers import anon_url
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickrage.indexers import IndexerApi
%>
<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#home-theater-nas">${_('Home Theater')}
        / ${_('NAS')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#devices">${_('Devices')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#social">${_('Social')}</a></li>
</%block>
<%block name="pages">
    <div id="home-theater-nas" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://kodi.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="text-right sickrage-notifiers sickrage-notifiers-kodi" title="KODI"></i>
                        ${_('KODI')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_kodi">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_kodi"
                                   id="use_kodi" ${('', 'checked')[bool(sickrage.app.config.use_kodi)]}/>
                            ${_('send KODI commands?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_kodi">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Always on')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_always_on">
                                <input type="checkbox" class="toggle color-primary is-material" name="kodi_always_on"
                                       id="kodi_always_on" ${('', 'checked')[bool(sickrage.app.config.kodi_always_on)]}/>
                                ${_('log errors when unreachable?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="kodi_notify_onsnatch"
                                       id="kodi_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="kodi_notify_ondownload"
                                       id="kodi_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="kodi_notify_onsubtitledownload"
                                       id="kodi_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.kodi_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Update library')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_update_library">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="kodi_update_library"
                                       id="kodi_update_library" ${('', 'checked')[bool(sickrage.app.config.kodi_update_library)]}/>
                                ${_('update KODI library when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Full library update')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_update_full">
                                <input type="checkbox" class="toggle color-primary is-material" name="kodi_update_full"
                                       id="kodi_update_full" ${('', 'checked')[bool(sickrage.app.config.kodi_update_full)]}/>
                                ${_('perform a full library update if update per-show fails?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Only update first host')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="kodi_update_onlyfirst">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="kodi_update_onlyfirst"
                                       id="kodi_update_onlyfirst" ${('', 'checked')[bool(sickrage.app.config.kodi_update_onlyfirst)]}/>
                                ${_('only send library updates to the first active host?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('KODI IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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

                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('KODI username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('KODI password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testKODI-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test KODI')}" id="testKODI"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_kodi //-->
            </fieldset>
        </div><!-- /kodi tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-plex" title="${_('Plex Media Server')}"></i>
                        ${_('Plex Media Server')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Experience your media on a visually stunning, easy to use interface on your computer connected to your TV')}
                    <p class="plexinfo hide">${_('For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port')}
                        <b>3005</b>.
                    </p>
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_plex">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_plex"
                                   id="use_plex" ${('', 'checked')[bool(sickrage.app.config.use_plex)]}/>
                            ${_('send Plex commands?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_plex">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Plex Media Server Auth Token')}</label>
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
                                        <input name="plex_server_token" id="plex_server_token"
                                               value="${sickrage.app.config.plex_server_token}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <label class="text-info" for="plex_server_token">
                                        ${_('Auth Token used by Plex')} -
                                        <a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}"
                                           rel="noreferrer"
                                           onclick="window.open(this.href, '_blank'); return false;">
                                            <u>${_('Finding your account token')}</u></a>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Server Username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Server/client password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Update server library')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="plex_update_library">
                                <input type="checkbox" class="enabler toggle color-primary is-material"
                                       name="plex_update_library"
                                       id="plex_update_library" ${('', 'checked')[bool(sickrage.app.config.plex_update_library)]}/>
                                ${_('update Plex Media Server library after download finishes')}
                            </label>
                        </div>
                    </div>
                    <div id="content_plex_update_library">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Plex Media Server IP:Port')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                <div class="card mb-3">
                                    <div class="card-text m-1">
                                        <div id="testPMS-result">${_('Click below to test')}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <input class="btn" type="button" value="${_('Test Plex Server')}"
                                       id="testPMS"/>
                                <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                            </div>
                        </div>
                    </div>
                </div><!-- /content_use_plex -->
            </fieldset>
        </div><!-- /plex media server tab-pane -->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="text-right sickrage-notifiers sickrage-notifiers-plex" title="Plex Media Client"></i>
                        ${_('Plex Media Client')}
                    </a>
                </h3>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_plex_client">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_plex"
                                   id="use_plex_client" ${('', 'checked')[bool(sickrage.app.config.use_plex_client)]}/>
                            ${_('send Plex commands?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_plex_client">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="plex_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="plex_notify_onsnatch"
                                       id="plex_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.plex_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="plex_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="plex_notify_ondownload"
                                       id="plex_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.plex_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="plex_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="plex_notify_onsubtitledownload"
                                       id="plex_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.plex_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Plex Client IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Server Username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Client Password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testPMC-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Plex Client')}"
                                   id="testPMC"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_plex_client -->
            </fieldset>
        </div><!-- /plex client tab-pane -->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://emby.media/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="text-right sickrage-notifiers sickrage-notifiers-emby" title="Emby"></i>
                        ${_('Emby')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('A home media server built using other popular open source technologies.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label class="control-label" for="use_emby">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_emby"
                                   id="use_emby" ${('', 'checked')[bool(sickrage.app.config.use_emby)]} />
                            ${_('send update commands to Emby?')}
                        </label>
                    </div>
                </div>
                <div id="content_use_emby">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Emby IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Emby API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="emby_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="emby_notify_onsnatch"
                                       id="emby_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.emby_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="emby_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="emby_notify_ondownload"
                                       id="emby_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.emby_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="emby_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="emby_notify_onsubtitledownload"
                                       id="emby_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.emby_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testEMBY-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Emby')}" id="testEMBY"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_emby //-->
            </fieldset>
        </div><!-- /emby tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-nmj" title="Networked Media Jukebox"></i>
                        ${_('NMJ')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_nmj">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_nmj"
                                   id="use_nmj" ${('', 'checked')[bool(sickrage.app.config.use_nmj)]}/>
                            ${_('send update commands to NMJ?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_nmj">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Popcorn IP address')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-globe"></span></span>
                                </div>
                                <input name="nmj_host" id="nmj_host"
                                       value="${sickrage.app.config.nmj_host}"
                                       placeholder="${_('ex. 192.168.1.100')}"
                                       class="form-control" autocapitalize="off"/>
                                <div class="input-group-append">
                                    <input class="btn btn-inline" type="button" value="${_('Get Settings')}"
                                           id="settingsNMJ"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('NMJ database')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <input name="nmj_database" id="nmj_database"
                                       value="${sickrage.app.config.nmj_database}"
                                       class="form-control"
                                       placeholder="${_('automatically filled via Get Settings')}"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.app.config.nmj_database == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('NMJ mount url')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-database"></span>
                                    </span>
                                </div>
                                <input name="nmj_mount" id="nmj_mount"
                                       value="${sickrage.app.config.nmj_mount}"
                                       class="form-control"
                                       placeholder="${_('automatically filled via Get Settings')}"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.app.config.nmj_mount == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testNMJ-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test NMJ')}" id="testNMJ"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_nmj //-->
            </fieldset>
        </div><!-- /nmj tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-nmj" title="Networked Media Jukebox v2"></i>
                        ${_('NMJv2')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_nmjv2">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_nmjv2"
                                   id="use_nmjv2" ${('', 'checked')[bool(sickrage.app.config.use_nmjv2)]}/>
                            ${_('send update commands to NMJv2?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_nmjv2">
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Popcorn IP address')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Database location')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input type="radio" NAME="nmjv2_dbloc" VALUE="local"
                                           id="NMJV2_DBLOC_A" ${('', 'checked')[sickrage.app.config.nmjv2_dbloc == 'local']}/>
                                    <label for="NMJV2_DBLOC_A" class="space-right">
                                        ${_('PCH Local Media')}
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Database instance')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <label class="text-info" for="NMJv2db_instance">
                                ${_('adjust this value if the wrong database is selected.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('NMJv2 database')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                <div class="input-group-append">
                                    <input type="button" class="btn btn-inline"
                                           value="${_('Find Database')}"
                                           id="settingsNMJv2"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testNMJv2-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test NMJv2')}" id="testNMJv2"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_nmjv2 //-->
            </fieldset>
        </div><!-- /nmjv2 tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-synoindex" title="Synology"></i>
                        ${_('Synology')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('The Synology DiskStation NAS.')}<br/>
                    ${_('Synology Indexer is the daemon running on the Synology NAS to build its media database.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_synoindex">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_synoindex"
                                   id="use_synoindex" ${('', 'checked')[bool(sickrage.app.config.use_synoindex)]}/>
                            ${_('send Synology notifications?')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('requires SickRage to be running on your Synology NAS.')}</div>
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

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-synologynotifier" title="Synology Notifier"></i>
                        ${_('Synology Notifier')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Synology Notifier is the notification system of Synology DSM')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_synologynotifier">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="use_synologynotifier"
                                   id="use_synologynotifier" ${('', 'checked')[bool(sickrage.app.config.use_synologynotifier)]}/>
                            ${_('send notifications to the Synology Notifier?')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('requires SickRage to be running on your Synology DSM.')}</div>
                        </label>
                    </div>
                </div>
                <div id="content_use_synologynotifier">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="synologynotifier_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="synologynotifier_notify_onsnatch"
                                       id="synologynotifier_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="synologynotifier_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="synologynotifier_notify_ondownload"
                                       id="synologynotifier_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="synologynotifier_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="synologynotifier_notify_onsubtitledownload"
                                       id="synologynotifier_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.synologynotifier_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
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

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-pytivo" title="pyTivo"></i>
                        ${_('pyTivo')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_pytivo">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_pytivo"
                                   id="use_pytivo" ${('', 'checked')[bool(sickrage.app.config.use_pytivo)]}/>
                            ${_('send notifications to pyTivo?')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('requires the downloaded files to be accessible by pyTivo.')}
                            </div>
                        </label>
                    </div>
                </div>

                <div id="content_use_pytivo">
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('pyTivo IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('pyTivo share name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-book"></span></span>
                                </div>
                                <input name="pytivo_share_name" id="pytivo_share_name"
                                       value="${sickrage.app.config.pytivo_share_name}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="pytivo_share_name">
                                ${_('value used in pyTivo Web Configuration to name the share.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Tivo name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-book"></span></span>
                                </div>
                                <input name="pytivo_tivo_name" id="pytivo_tivo_name"
                                       value="${sickrage.app.config.pytivo_tivo_name}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="pytivo_tivo_name">
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
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://growl.info/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-growl" title="Growl"></i>
                        ${_('Growl')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('A cross-platform unobtrusive global notification system.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_growl">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_growl"
                                   id="use_growl" ${('', 'checked')[bool(sickrage.app.config.use_growl)]}/>
                            ${_('send Growl notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_growl">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="growl_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="growl_notify_onsnatch"
                                       id="growl_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.growl_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="growl_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="growl_notify_ondownload"
                                       id="growl_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.growl_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="growl_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="growl_notify_onsubtitledownload"
                                       id="growl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.growl_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Growl IP:Port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Growl password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testGrowl-result">${_('Click below to register and test Growl, this is required for Growl notifications to work.')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Register Growl')}"
                                   id="testGrowl"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_growl //-->

            </fieldset>
        </div><!-- /growl tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-prowl" title="Prowl"></i>
                        ${_('Prowl')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('A Growl client for iOS.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_prowl">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_prowl"
                                   id="use_prowl" ${('', 'checked')[bool(sickrage.app.config.use_prowl)]}/>
                            ${_('send Prowl notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_prowl">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="prowl_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="prowl_notify_onsnatch"
                                       id="prowl_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="prowl_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="prowl_notify_ondownload"
                                       id="prowl_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="prowl_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="prowl_notify_onsubtitledownload"
                                       id="prowl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.prowl_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Prowl API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="prowl_api" id="prowl_api"
                                       value="${sickrage.app.config.prowl_api}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="prowl_api">
                                ${_('get your key at:')}
                                <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;">https://www.prowlapp.com/api_settings.php</a>
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Prowl priority')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <label class="text-info" for="prowl_priority">
                                ${_('priority of Prowl messages from SiCKRAGE.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testProwl-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Prowl')}" id="testProwl"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_prowl //-->

            </fieldset>
        </div><!-- /prowl tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-libnotify" title="Libnotify"></i>
                        ${_('Libnotify')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('The standard desktop notification API for Linux/*nix systems. This notifier will only function if the pynotify module is installed')}
                    (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_libnotify">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_libnotify"
                                   id="use_libnotify" ${('', 'checked')[bool(sickrage.app.config.use_libnotify)]}/>
                            ${_('send Libnotify notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_libnotify">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="libnotify_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="libnotify_notify_onsnatch"
                                       id="libnotify_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="libnotify_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="libnotify_notify_ondownload"
                                       id="libnotify_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="libnotify_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="libnotify_notify_onsubtitledownload"
                                       id="libnotify_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.libnotify_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testLibnotify-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Libnotify')}"
                                   id="testLibnotify"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_libnotify //-->
            </fieldset>
        </div><!-- /libnotify tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-pushover" title="Pushover"></i>
                        ${_('Pushover')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Pushover makes it easy to send real-time notifications to your Android and iOS devices.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_pushover">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_pushover"
                                   id="use_pushover" ${('', 'checked')[bool(sickrage.app.config.use_pushover)]}/>
                            ${_('send Pushover notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_pushover">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushover_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushover_notify_onsnatch"
                                       id="pushover_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushover_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushover_notify_ondownload"
                                       id="pushover_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushover_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushover_notify_onsubtitledownload"
                                       id="pushover_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushover_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">

                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushover key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushover API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                </div>
                                <input name="pushover_apikey" id="pushover_apikey"
                                       value="${sickrage.app.config.pushover_apikey}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="pushover_apikey">
                                <a href="${anon_url('https://pushover.net/apps/clone/sickrage')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;"><b>${_('Click here')}</b></a> ${_('to create a Pushover API key')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushover devices')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushover notification sound')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <label class="text-info" for="pushover_sound">
                                ${_('Choose notification sound to use')}
                            </label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testPushover-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Pushover')}"
                                   id="testPushover"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_pushover //-->

            </fieldset>
        </div><!-- /pushover tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-boxcar2" title="Boxcar2"></i>
                        ${_('Boxcar2')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Read your messages where and when you want them!')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_boxcar2">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_boxcar2"
                                   id="use_boxcar2" ${('', 'checked')[bool(sickrage.app.config.use_boxcar2)]}/>
                            ${_('send Boxcar2 notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_boxcar2">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="boxcar2_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="boxcar2_notify_onsnatch"
                                       id="boxcar2_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="boxcar2_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="boxcar2_notify_ondownload"
                                       id="boxcar2_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="boxcar2_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="boxcar2_notify_onsubtitledownload"
                                       id="boxcar2_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.boxcar2_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Boxcar2 access token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testBoxcar2-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Boxcar2')}"
                                   id="testBoxcar2"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_boxcar2 //-->

            </fieldset>
        </div><!-- /boxcar2 tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://nma.usk.bz')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-nma" title="Notify My Android"></i>
                        ${_('Notify My Android')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Notify My Android is a Prowl-like Android App and API that offers an easy way to send notifications from your application directly to your Android device.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_nma">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_nma"
                                   id="use_nma" ${('', 'checked')[bool(sickrage.app.config.use_nma)]}/>
                            ${_('send NMA notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_nma">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="nma_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="nma_notify_onsnatch"
                                       id="nma_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.nma_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="nma_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="nma_notify_ondownload"
                                       id="nma_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.nma_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="nma_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="nma_notify_onsubtitledownload"
                                       id="nma_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.nma_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('NMA API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('NMA priority')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <label class="text-info" for="nma_priority">
                                ${_('priority of NMA messages from SiCKRAGE.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testNMA-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test NMA')}" id="testNMA"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_nma //-->

            </fieldset>
        </div><!-- /nma tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('https://pushalot.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-pushalot" title="Pushalot"></i>
                        ${_('Pushalot')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Pushalot is a platform for receiving custom push notifications to connected devices running Windows Phone or Windows 8.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_pushalot">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_pushalot"
                                   id="use_pushalot" ${('', 'checked')[bool(sickrage.app.config.use_pushalot)]}/>
                            ${_('send Pushalot notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_pushalot">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushalot_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushalot_notify_onsnatch"
                                       id="pushalot_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushalot_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushalot_notify_ondownload"
                                       id="pushalot_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushalot_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushalot_notify_onsubtitledownload"
                                       id="pushalot_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushalot_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushalot authorization token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testPushalot-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="${_('Test Pushalot')}"
                                   id="testPushalot"/>
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_pushalot //-->

            </fieldset>
        </div><!-- /pushalot tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-pushbullet" title="Pushbullet"></i>
                        ${_('Pushbullet')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Pushbullet is a platform for receiving custom push notifications to connected devices running Android and desktop Chrome browsers.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_pushbullet">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="use_pushbullet"
                                   id="use_pushbullet" ${('', 'checked')[bool(sickrage.app.config.use_pushbullet)]}/>
                            ${_('send Pushbullet notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_pushbullet">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushbullet_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushbullet_notify_onsnatch"
                                       id="pushbullet_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushbullet_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushbullet_notify_ondownload"
                                       id="pushbullet_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="pushbullet_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="pushbullet_notify_onsubtitledownload"
                                       id="pushbullet_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.pushbullet_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushbullet API key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Pushbullet devices')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-list"></span></span>
                                        </div>
                                        <select name="pushbullet_device_list" id="pushbullet_device_list"
                                                class="form-control "></select>
                                        <div class="input-group-append">
                                            <input type="hidden" id="pushbullet_device"
                                                   value="${sickrage.app.config.pushbullet_device}">
                                            <input type="button" class="btn btn-inline"
                                                   value="${_('Update device list')}"
                                                   id="getPushbulletDevices"/>
                                        </div>
                                    </div>
                                    <label class="text-info"
                                           for="pushbullet_device_list">${_('select device you wish to push to.')}</label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testPushbullet-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="${_('Test Pushbullet')}"
                                   id="testPushbullet"/>
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_pushbullet //-->
            </fieldset>
        </div><!-- /pushbullet tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-freemobile" title="FreeMobile"></i>
                        ${_('Free Mobile')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_freemobile">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   name="use_freemobile"
                                   id="use_freemobile" ${('', 'checked')[bool(sickrage.app.config.use_freemobile)]}/>
                            ${_('send SMS notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_freemobile">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="freemobile_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="freemobile_notify_onsnatch"
                                       id="freemobile_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_onsnatch)]}/>
                                ${_('send a SMS when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="freemobile_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="freemobile_notify_ondownload"
                                       id="freemobile_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_ondownload)]}/>
                                ${_('send a SMS when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="freemobile_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="freemobile_notify_onsubtitledownload"
                                       id="freemobile_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.freemobile_notify_onsubtitledownload)]}/>
                                ${_('send a SMS when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Free Mobile customer ID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Free Mobile API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testFreeMobile-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test SMS')}"
                                   id="testFreeMobile"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_freemobile //-->
            </fieldset>
        </div><!-- /freemobile tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://telegram.org/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-telegram" title="Telegram"></i>
                        ${_('Telegram')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Telegram is a cloud-based instant messaging service')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_telegram">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_telegram"
                                   id="use_telegram" ${('', 'checked')[bool(sickrage.app.config.use_telegram)]}/>
                            ${_('send Telegram notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_telegram">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="telegram_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="telegram_notify_onsnatch"
                                       id="telegram_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_onsnatch)]}/>
                                ${_('send a message when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="telegram_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="telegram_notify_ondownload"
                                       id="telegram_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_ondownload)]}/>
                                ${_('send a message when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="telegram_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="telegram_notify_onsubtitledownload"
                                       id="telegram_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.telegram_notify_onsubtitledownload)]}/>
                                ${_('send a message when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('User/Group ID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="telegram_id">
                                        ${_('contact @myidbot on Telegram to get an ID')}
                                        <p><b>${_('NOTE')}
                                            :</b> ${_('Don\'t forget to talk with your bot at least one time if you get a 403 error.')}
                                        </p>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Bot API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="telegram_apikey">
                                        ${_('contact @BotFather on Telegram to set up one')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testTelegram-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Telegram')}"
                                   id="testTelegram"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_telegram //-->
            </fieldset>
        </div><!-- /telegram tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('https://joaoapps.com/join/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-join" title="Join"></i>
                        ${_('Join')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Join all of your devices together')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_join">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_join"
                                   id="use_join" ${('', 'checked')[bool(sickrage.app.config.use_join)]}/>
                            ${_('send Join notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_join">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="join_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="join_notify_onsnatch"
                                       id="join_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.join_notify_onsnatch)]}/>
                                ${_('send a message when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="join_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="join_notify_ondownload"
                                       id="join_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.join_notify_ondownload)]}/>
                                ${_('send a message when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="join_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="join_notify_onsubtitledownload"
                                       id="join_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.join_notify_onsubtitledownload)]}/>
                                ${_('send a message when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Device ID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-user"></span></span>
                                        </div>
                                        <input name="join_id" id="join_id"
                                               value="${sickrage.app.config.join_id}"
                                               class="form-control"
                                               placeholder="${_('ex. 12345678')}"
                                               autocapitalize="off"/>
                                    </div>
                                    <label class="text-info" for="join_id">
                                        ${_('per device specific id')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('API Key')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="input-group">
                                        <div class="input-group-prepend">
                                            <span class="input-group-text"><span class="fas fa-cloud"></span></span>
                                        </div>
                                        <input name="join_apikey" id="join_apikey"
                                               value="${sickrage.app.config.join_apikey}"
                                               class="form-control"
                                               placeholder="${_('enter your API key')}"
                                               autocapitalize="off"/>
                                    </div>
                                    <label class="text-info" for="join_apikey">
                                        <a href="${anon_url('https://joaoapps.com/join/web')}" rel="noreferrer"
                                           onclick="window.open(this.href, '_blank'); return false;"><b>${_('click here')}</b></a>${_(' to create a Join API key')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testJoin-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Join')}"
                                   id="testJoin"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_join //-->
            </fieldset>
        </div><!-- /join tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.twilio.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-twilio" title="Twilio"></i>
                        ${_('Twilio')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Twilio is a webservice API that allows you to communicate directly with a mobile number. This notifier will send a text directly to your mobile device.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_twilio">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_twilio"
                                   id="use_twilio" ${('', 'checked')[bool(sickrage.app.config.use_twilio)]}/>
                            ${_('text your mobile device?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_twilio">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twilio_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twilio_notify_onsnatch"
                                       id="twilio_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_onsnatch)]}/>
                                ${_('send a message when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twilio_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twilio_notify_ondownload"
                                       id="twilio_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_ondownload)]}/>
                                ${_('send a message when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twilio_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twilio_notify_onsubtitledownload"
                                       id="twilio_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.twilio_notify_onsubtitledownload)]}/>
                                ${_('send a message when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Twilio Account SID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="twilio_account_sid">
                                        ${_('account SID of your Twilio account.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Twilio Auth Token')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Twilio Phone SID')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="twilio_phone_sid">
                                        ${_('phone SID that you would like to send the sms from.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Your phone number')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="twilio_to_number">
                                        ${_('phone number that will receive the sms.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testTwilio-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Twilio')}" id="testTwilio"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_twilio //-->
            </fieldset>
        </div><!-- /twilio tab-pane //-->

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://alexa.amazon.ca/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-alexa" title="Alexa"></i>
                        ${_('Alexa')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Alexa is smart home device. This notifier will send messages directly to your Alexa devices.')}
                    <p class="alexa-info hide">
                        ${_('For sending notifications to Alexa devices, install Alexa skill SiCKRAGE.')}
                    </p>
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_alexa">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_alexa"
                                   id="use_alexa" ${('', 'checked')[bool(sickrage.app.config.use_alexa)]}/>
                            ${_('send messages to your devices?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_alexa">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="alexa_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="alexa_notify_onsnatch"
                                       id="alexa_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.alexa_notify_onsnatch)]}/>
                                ${_('send a message when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="alexa_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="alexa_notify_ondownload"
                                       id="alexa_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.alexa_notify_ondownload)]}/>
                                ${_('send a message when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="alexa_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="alexa_notify_onsubtitledownload"
                                       id="alexa_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.alexa_notify_onsubtitledownload)]}/>
                                ${_('send a message when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testAlexa-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Alexa')}" id="testAlexa"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_alexa //-->
            </fieldset>
        </div><!-- /alexa tab-pane //-->
    </div>

    <div id="social" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-twitter" title="Twitter"></i>
                        ${_('Twitter')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('A social networking and microblogging service, enabling its users to send and read other users messages called tweets.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_twitter">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_twitter"
                                   id="use_twitter" ${('', 'checked')[bool(sickrage.app.config.use_twitter)]}/>
                            ${_('post tweets on Twitter?')}<br/>
                            <div class="text-info"><b>${_('NOTE:')}</b> ${_('you may want to use a secondary account.')}
                            </div>
                        </label>
                    </div>
                </div>

                <div id="content_use_twitter">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twitter_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twitter_notify_onsnatch"
                                       id="twitter_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twitter_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twitter_notify_ondownload"
                                       id="twitter_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twitter_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="twitter_notify_onsubtitledownload"
                                       id="twitter_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.twitter_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Send direct message')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="twitter_usedm">
                                <input type="checkbox" class="toggle color-primary is-material" name="twitter_usedm"
                                       id="twitter_usedm" ${('', 'checked')[bool(sickrage.app.config.twitter_usedm)]}/>
                                ${_('send a notification via Direct Message, not via status update')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Send DM to')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Step One')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="${_('Request Authorization')}"
                                           id="twitterStep1"/>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <div class="text-info">
                                        ${_('Click the "Request Authorization" button.')}<br/>
                                        ${_('This will open a new page containing an auth key.')}<br/>
                                        <b>${_('NOTE:')}</b>${_('if nothing happens check your popup blocker.')}<br/>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Step Two')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                </div>
                                <input id="twitter_key" value=""
                                       class="form-control"
                                       placeholder="${_('Enter the key Twitter gave you')}"
                                       autocapitalize="off"/>
                                <div class="input-group-append">
                                    <input class="btn" type="button" value="Verify Key" id="twitterStep2"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testTwitter-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Twitter')}"
                                   id="testTwitter"/>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </div><!-- /content_use_twitter //-->

            </fieldset>
        </div><!-- /twitter tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://trakt.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-trakt" title="Trakt"></i>
                        ${_('Trakt')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, trakt recommends additional shows and movies you\'ll enjoy!')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_trakt">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_trakt"
                                   id="use_trakt" ${('', 'checked')[bool(sickrage.app.config.use_trakt)]}/>
                            ${_('send Trakt.tv notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_trakt">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Trakt username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                    <input type="hidden" id="trakt_pin_url" value="${TraktAPI()['oauth/pin'].url()}">
                    % if not sickrage.app.config.trakt_oauth_token:
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Trakt PIN')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-lock"></span></span>
                                    </div>
                                    <input name="trakt_pin" id="trakt_pin" value=""
                                           placeholder="${_('authorization PIN code')}"
                                           class="form-control" autocapitalize="off"/>
                                    <div class="input-group-append">
                                        <a class="btn" href="#" id="TraktGetPin">Get PIN</a>
                                        <a class="btn d-none" href="#" id="authTrakt">${_('Authorize')}</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endif
                    <input type="button" class="btn hide" value="${_('Authorize SiCKRAGE')}"
                           id="authTrakt"/>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('API Timeout')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Default indexer')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fab fa-linode"></span>
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Sync libraries')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="trakt_sync">
                                <input type="checkbox" class="enabler toggle color-primary is-material"
                                       name="trakt_sync"
                                       id="trakt_sync" ${('', 'checked')[bool(sickrage.app.config.trakt_sync)]}/>
                                ${_('sync your SickRage show library with your trakt show library.')}
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Remove Episodes From Collection')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="trakt_sync_remove">
                                    <input type="checkbox" class="toggle color-primary is-material"
                                           name="trakt_sync_remove"
                                           id="trakt_sync_remove" ${('', 'checked')[bool(sickrage.app.config.trakt_sync_remove)]}/>
                                    ${_('Remove an episode from your Trakt collection if it is not in your SickRage library.')}
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Sync watchlist')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="trakt_sync_watchlist">
                                <input type="checkbox" class="enabler toggle color-primary is-material"
                                       name="trakt_sync_watchlist"
                                       id="trakt_sync_watchlist" ${('', 'checked')[bool(sickrage.app.config.trakt_sync_watchlist)]}/>
                                ${_('sync your SickRage show watchlist with your trakt show watchlist (either Show and Episode).')}
                                <div class="text-info">
                                    <p>${_('Episode will be added on watch list when wanted or snatched and will be removed when downloaded')}</p>
                                </div>
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync_watchlist">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Watchlist add method')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                <label class="text-info" for="trakt_method_add">
                                    ${_('method in which to download episodes for new show\'s.')}
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Remove episode')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="trakt_remove_watchlist">
                                    <input type="checkbox" class="toggle color-primary is-material"
                                           name="trakt_remove_watchlist"
                                           id="trakt_remove_watchlist" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_watchlist)]}/>
                                    ${_('remove an episode from your watchlist after it is downloaded.')}
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Remove series')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="trakt_remove_serieslist">
                                    <input type="checkbox" class="toggle color-primary is-material"
                                           name="trakt_remove_serieslist"
                                           id="trakt_remove_serieslist" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_serieslist)]}/>
                                    ${_('remove the whole series from your watchlist after any download.')}
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Remove watched show')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="trakt_remove_show_from_sickrage">
                                    <input type="checkbox" class="toggle color-primary is-material"
                                           name="trakt_remove_show_from_sickrage"
                                           id="trakt_remove_show_from_sickrage" ${('', 'checked')[bool(sickrage.app.config.trakt_remove_show_from_sickrage)]}/>
                                    ${_('remove the show from sickrage if it\'s ended and completely watched')}
                                </label>
                            </div>
                        </div>
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${_('Start paused')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <label for="trakt_start_paused">
                                    <input type="checkbox" class="toggle color-primary is-material"
                                           name="trakt_start_paused"
                                           id="trakt_start_paused" ${('', 'checked')[bool(sickrage.app.config.trakt_start_paused)]}/>
                                    ${_('show\'s grabbed from your trakt watchlist start paused.')}
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Trakt blackList name')}</label>
                        </div>
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list"></span></span>
                                </div>
                                <input name="trakt_blacklist_name" id="trakt_blacklist_name"
                                       value="${sickrage.app.config.trakt_blacklist_name}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="trakt_blacklist_name">
                                ${_('Name(slug) of list on Trakt for blacklisting show on \'Add from Trakt\' page')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testTrakt-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="${_('Test Trakt')}" id="testTrakt"/>
                            <input type="submit" class="btn config_submitter"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_trakt //-->
            </fieldset>
        </div><!-- /trakt tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-email" title="Email"></i>
                        ${_('Email')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Allows configuration of email notifications on a per show basis.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_email">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_email"
                                   id="use_email" ${('', 'checked')[bool(sickrage.app.config.use_email)]}/>
                            ${_('send email notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_email">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="email_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="email_notify_onsnatch"
                                       id="email_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.email_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="email_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="email_notify_ondownload"
                                       id="email_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.email_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="email_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="email_notify_onsubtitledownload"
                                       id="email_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.email_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('SMTP host')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('SMTP port')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('SMTP from')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Use TLS')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="email_tls">
                                <input type="checkbox" class="toggle color-primary is-material" name="email_tls"
                                       id="email_tls" ${('', 'checked')[bool(sickrage.app.config.email_tls)]}/>
                                ${_('check to use TLS encryption.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('SMTP user')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('SMTP password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Global email list')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-envelope"></span></span>
                                </div>
                                <input name="email_list" id="email_list"
                                       value="${sickrage.app.config.email_list}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="email_list">
                                ${_('all emails here receive notifications for')} <b>${_('all')}</b> ${_('shows.')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Show notification list')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="email_show">
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
                                    <label class="text-info" for="email_show_list">
                                        ${_('configure per-show notifications here by entering email addresses, separated by commas, after selecting a show in the drop-down box. Be sure to activate the Save for this show button below after each entry.')}
                                    </label>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="col-md-12">
                                    <input id="email_show_save" class="btn" type="button"
                                           value="${_('Save for this show')}"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testEmail-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Email')}" id="testEmail"/>
                            <input class="btn config_submitter" type="submit"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_email //-->
            </fieldset>
        </div><!-- /email tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.slack.com')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-slack" title="Slack"></i>
                        ${_('Slack')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('Slack brings all your communication together in one place. It\'s real-time messaging, archiving and search for modern teams.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_slack">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_slack"
                                   id="use_slack" ${('', 'checked')[bool(sickrage.app.config.use_slack)]}/>
                            ${_('send slack notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_slack">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="slack_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="slack_notify_onsnatch"
                                       id="slack_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.slack_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="slack_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="slack_notify_ondownload"
                                       id="slack_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.slack_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="slack_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="slack_notify_onsubtitledownload"
                                       id="slack_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.slack_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Slack Incoming Webhook')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testSlack-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Slack')}" id="testSlack"/>
                            <input class="btn config_submitter" type="submit"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_slack //-->
            </fieldset>
        </div><!-- /slack tab-pane //-->

        <hr/>

        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <a href="${anon_url('http://www.discordapp.com')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        <i class="sickrage-notifiers sickrage-notifiers-discord" title="Discord"></i>
                        ${_('Discord')}
                    </a>
                </h3>
                <small class="form-text text-muted">
                    ${_('All-in-one voice and text chat for gamers that\'s free, secure, and works on both your desktop and phone.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enable')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_discord">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_discord"
                                   id="use_discord" ${('', 'checked')[bool(sickrage.app.config.use_discord)]}/>
                            ${_('send discord notifications?')}
                        </label>
                    </div>
                </div>

                <div id="content_use_discord">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on snatch')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="discord_notify_onsnatch">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="discord_notify_onsnatch"
                                       id="discord_notify_onsnatch" ${('', 'checked')[bool(sickrage.app.config.discord_notify_onsnatch)]}/>
                                ${_('send a notification when a download starts?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="discord_notify_ondownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="discord_notify_ondownload"
                                       id="discord_notify_ondownload" ${('', 'checked')[bool(sickrage.app.config.discord_notify_ondownload)]}/>
                                ${_('send a notification when a download finishes?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Notify on subtitle download')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="discord_notify_onsubtitledownload">
                                <input type="checkbox" class="toggle color-primary is-material"
                                       name="discord_notify_onsubtitledownload"
                                       id="discord_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.app.config.discord_notify_onsubtitledownload)]}/>
                                ${_('send a notification when subtitles are downloaded?')}
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Discord Incoming Webhook')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info" for="discord_webhook">
                                        ${_('Create webhook under channel settings.')}
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Discord Bot Name')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info"
                                           for="discord_name">${_('Blank will use webhook default name.')}</label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Discord Avatar URL')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
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
                                    <label class="text-info"
                                           for="discord_avatar_url">${_('Blank will use webhook default avatar.')}</label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Discord TTS')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="discord_tts">
                                <input type="checkbox" class="toggle color-primary is-material" name="discord_tts"
                                       id="discord_tts" ${('', 'checked="checked"')[bool(sickrage.app.config.discord_tts)]}/>
                                ${_('Send notifications using text-to-speech.')}
                            </label>
                        </div>
                    </div>


                    <div class="form-row">
                        <div class="col-md-12">
                            <div class="card mb-3">
                                <div class="card-text m-1">
                                    <div id="testDiscord-result">${_('Click below to test')}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="${_('Test Discord')}"
                                   id="testDiscord"/>
                            <input class="btn config_submitter" type="submit"
                                   value="${_('Save Changes')}"/>
                        </div>
                    </div>
                </div><!-- /content_use_discord //-->
            </fieldset>
        </div><!-- /discord tab-pane //-->
    </div>
</%block>
