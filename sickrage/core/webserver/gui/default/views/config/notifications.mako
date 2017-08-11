<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveNotifications' %></%def>
<%!
    import re

    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets, multiEpStrings
    from sickrage.indexers import srIndexerApi
%>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#tabs-1">Home Theater / NAS</a></li>
    <li><a data-toggle="tab" href="#tabs-2">Devices</a></li>
    <li><a data-toggle="tab" href="#tabs-3">Social</a></li>
</%block>
<%block name="pages">
    <div id="tabs-1" class="row tab-pane fade in active">
        <div class="tab-pane">

            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/kodi.png" alt=""
                     title="KODI"/>
                <h3><a href="${anon_url('http://kodi.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">KODI</a></h3>
                <p>A free and open source cross-platform media center and home entertainment system software
                    with a 10-foot user interface designed for the living-room TV.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_kodi"
                               id="use_kodi" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_KODI)]}/>
                        <label for="use_kodi">should SickRage send KODI commands ?</label>
                    </div>
                </div>

                <div id="content_use_kodi">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Always on</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_always_on"
                                   id="kodi_always_on" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_ALWAYS_ON)]}/>
                            <label for="kodi_always_on">
                                <p>log errors when unreachable ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_onsnatch"
                                   id="kodi_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_NOTIFY_ONSNATCH)]}/>
                            <label for="kodi_notify_onsnatch">
                                <p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_ondownload"
                                   id="kodi_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="kodi_notify_ondownload">
                                <p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_notify_onsubtitledownload"
                                   id="kodi_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="kodi_notify_onsubtitledownload">
                                <p>send a notification when subtitles are downloaded ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Update library</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_library"
                                   id="kodi_update_library" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_UPDATE_LIBRARY)]}/>
                            <label for="kodi_update_library">
                                <p>update KODI library when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Full library update</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_full"
                                   id="kodi_update_full" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_UPDATE_FULL)]}/>
                            <label for="kodi_update_full">
                                <p>perform a full library update if update per-show fails ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Only update first host</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="kodi_update_onlyfirst"
                                   id="kodi_update_onlyfirst" ${('', 'checked')[bool(sickrage.srCore.srConfig.KODI_UPDATE_ONLYFIRST)]}/>
                            <label for="kodi_update_onlyfirst">
                                <p>only send library updates to the first active host ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">KODI IP:Port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="kodi_host" id="kodi_host"
                                       value="${sickrage.srCore.srConfig.KODI_HOST}"
                                       placeholder="ex. 192.168.1.100:8080, 192.168.1.101:8080"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">KODI username</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="kodi_username" id="kodi_username"
                                       value="${sickrage.srCore.srConfig.KODI_USERNAME}"
                                       class="form-control"
                                       placeholder="blank = no authentication"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">KODI password</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input type="password" name="kodi_password" id="kodi_password"
                                       value="${sickrage.srCore.srConfig.KODI_PASSWORD}"
                                       class="form-control"
                                       placeholder="blank = no authentication"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testKODI-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test KODI" id="testKODI"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_kodi //-->

            </fieldset>

        </div><!-- /kodi tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/plex.png" alt=""
                     title="Plex Media Server"/>
                <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Plex Media Server</a></h3>
                <p>Experience your media on a visually stunning, easy to use interface on your Mac connected
                    to
                    your TV. Your media library has never looked this good!</p>
                <p class="plexinfo hide">For sending notifications to Plex Home Theater (PHT) clients, use
                    the
                    KODI notifier with port <b>3005</b>.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_plex"
                               id="use_plex" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PLEX)]}/>
                        <label for="use_plex"><p>should SickRage send Plex commands ?</p></label>
                    </div>
                </div>

                <div id="content_use_plex">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Plex Media Server Auth Token</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="input-group input350">
                                        <div class="input-group-addon">
                                            <span class="glyphicon glyphicon-cloud"></span>
                                        </div>
                                        <input name="plex_server_token" id="plex_server_token"
                                               value="${sickrage.srCore.srConfig.PLEX_SERVER_TOKEN}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="plex_server_token">
                                        Auth Token used by plex
                                        (<a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}"
                                            rel="noreferrer"
                                            onclick="window.open(this.href, '_blank'); return false;"><u>Finding
                                        your account token</u></a>)
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="tab-pane" style="padding: 0; min-height: 130px">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Server Username</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="plex_username" id="plex_username"
                                           value="${sickrage.srCore.srConfig.PLEX_USERNAME}"
                                           placeholder="blank = no authentication"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Server/client password</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="plex_password" id="plex_password"
                                           value="${sickrage.srCore.srConfig.PLEX_PASSWORD}"
                                           placeholder="blank = no authentication"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="tab-pane" style="padding: 0; min-height: 50px">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Update server library</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="plex_update_library"
                                       id="plex_update_library" ${('', 'checked')[bool(sickrage.srCore.srConfig.PLEX_UPDATE_LIBRARY)]}/>
                                <label for="plex_update_library">
                                    update Plex Media Server library after download finishes
                                </label>
                            </div>
                        </div>
                        <div id="content_plex_update_library">
                            <div class="row field-pair">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">Plex Media Server IP:Port</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="input-group input350">
                                        <div class="input-group-addon">
                                            <span class="glyphicon glyphicon-globe"></span>
                                        </div>
                                        <input name="plex_server_host"
                                               id="plex_server_host"
                                               placeholder="ex. 192.168.1.1:32400, 192.168.1.2:32400"
                                               value="${re.sub(r'\b,\b', ', ', sickrage.srCore.srConfig.PLEX_SERVER_HOST)}"
                                               class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPMS-result">
                                        Click below to test Plex server(s)
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="Test Plex Server" id="testPMS"/>
                                    <input type="submit" class="config_submitter btn" value="Save Changes"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </div><!-- /content_use_plex -->
            </fieldset>
        </div><!-- /plex media server tab-pane -->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/plex.png" alt=""
                     title="Plex Media Client"/>
                <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Plex Media Client</a></h3>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_plex"
                               id="use_plex_client" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PLEX_CLIENT)]}/>
                        <label for="use_plex_client"><p>should SickRage send Plex commands ?</p></label>
                    </div>
                </div>

                <div id="content_use_plex_client">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_onsnatch"
                                   id="plex_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.PLEX_NOTIFY_ONSNATCH)]}/>
                            <label for="plex_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_ondownload"
                                   id="plex_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PLEX_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="plex_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="plex_notify_onsubtitledownload"
                                   id="plex_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="plex_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Plex Client IP:Port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="plex_host" id="plex_host"
                                       value="${sickrage.srCore.srConfig.PLEX_HOST}"
                                       placeholder="ex. 192.168.1.100:3000, 192.168.1.101:3000"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="tab-pane" style="padding: 0; min-height: 130px">
                        <div class="row field-pair">

                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Server Username</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input name="plex_client_username" id="plex_client_username"
                                           value="${sickrage.srCore.srConfig.PLEX_CLIENT_USERNAME}"
                                           placeholder="blank = no authentication"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Client Password</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input type="password" name="plex_client_password" id="plex_client_password"
                                           value="${sickrage.srCore.srConfig.PLEX_CLIENT_PASSWORD}"
                                           placeholder="blank = no authentication"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="testNotification" id="testPMC-result">Click below to test Plex client(s)
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <input class="btn" type="button" value="Test Plex Client" id="testPMC"/>
                                <input type="submit" class="config_submitter btn" value="Save Changes"/>
                            </div>
                        </div>
                    </div>
                </div><!-- /content_use_plex_client -->
            </fieldset>
        </div><!-- /plex client tab-pane -->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/emby.png" alt=""
                     title="Emby"/>
                <h3><a href="${anon_url('http://emby.media/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Emby</a></h3>
                <p>A home media server built using other popular open source technologies.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_emby"
                               id="use_emby" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_EMBY)]} />
                        <label class="control-label" for="use_emby">
                            should SickRage send update commands to Emby?
                        </label>
                    </div>
                </div>
                <div id="content_use_emby">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Emby IP:Port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="emby_host" id="emby_host"
                                       value="${sickrage.srCore.srConfig.EMBY_HOST}"
                                       placeholder="ex. 192.168.1.100:8096"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Emby API Key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="emby_apikey" id="emby_apikey"
                                       value="${sickrage.srCore.srConfig.EMBY_APIKEY}"
                                       class="form-control"
                                       autocapitalize="off" title="Emby API key"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testEMBY-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Emby" id="testEMBY"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div>
                <!-- /content_use_emby //-->
            </fieldset>
        </div><!-- /emby tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nmj.png" alt=""
                     title="Networked Media Jukebox"/>
                <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">NMJ</a></h3>
                <p>The Networked Media Jukebox, or NMJ, is the official media jukebox interface made
                    available
                    for the Popcorn Hour 200-series.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">

                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nmj"
                               id="use_nmj" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_NMJ)]}/>
                        <label for="use_nmj"><p>should SickRage send update commands to NMJ ?</p></label>
                    </div>
                </div>

                <div id="content_use_nmj">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Popcorn IP address</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="nmj_host" id="nmj_host"
                                       value="${sickrage.srCore.srConfig.NMJ_HOST}"
                                       placeholder="ex. 192.168.1.100"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Get settings</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input class="btn btn-inline" type="button" value="Get Settings"
                                   id="settingsNMJ"/>
                            <label for="settingsNMJ">
                                the Popcorn Hour device must be powered on and NMJ running.
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NMJ database</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-database"></span>
                                </div>
                                <input name="nmj_database" id="nmj_database"
                                       value="${sickrage.srCore.srConfig.NMJ_DATABASE}"
                                       class="form-control"
                                       placeholder="automatically filled via the 'Get Settings'"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.srCore.srConfig.NMJ_DATABASE == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NMJ mount url</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-database"></span>
                                </div>
                                <input name="nmj_mount" id="nmj_mount"
                                       value="${sickrage.srCore.srConfig.NMJ_MOUNT}"
                                       class="form-control"
                                       placeholder="automatically filled via the 'Get Settings'"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.srCore.srConfig.NMJ_MOUNT == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMJ-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test NMJ" id="testNMJ"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_nmj //-->

            </fieldset>
        </div><!-- /nmj tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nmj.png" alt=""
                     title="Networked Media Jukebox v2"/>
                <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">NMJv2</a></h3>
                <p>The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made
                    available
                    for the Popcorn Hour 300 & 400-series.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nmjv2"
                               id="use_nmjv2" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_NMJv2)]}/>
                        <label for="use_nmjv2"><p>should SickRage send update commands to NMJv2 ?</p></label>
                    </div>
                </div>

                <div id="content_use_nmjv2">
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Popcorn IP address</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="nmjv2_host" id="nmjv2_host"
                                       value="${sickrage.srCore.srConfig.NMJv2_HOST}"
                                       placeholder="ex. 192.168.1.100"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Database location</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="radio" NAME="nmjv2_dbloc" VALUE="local"
                                           id="NMJV2_DBLOC_A" ${('', 'checked')[sickrage.srCore.srConfig.NMJv2_DBLOC == 'local']}/>PCH
                                    <label for="NMJV2_DBLOC_A" class="space-right">
                                        Local Media
                                    </label>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="radio" NAME="nmjv2_dbloc" VALUE="network"
                                           id="NMJV2_DBLOC_B" ${('', 'checked')[sickrage.srCore.srConfig.NMJv2_DBLOC == 'network']}/>
                                    <label for="NMJV2_DBLOC_B">
                                        PCH Network Media
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Database instance</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-database"></span>
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
                                adjust this value if the wrong database is selected.
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Find database</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="button" class="btn btn-inline" value="Find Database"
                                   id="settingsNMJv2"/>
                            <label for="settingsNMJv2">
                                the Popcorn Hour device must be powered on.
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NMJv2 database</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-database"></span>
                                </div>
                                <input name="nmjv2_database" id="nmjv2_database"
                                       value="${sickrage.srCore.srConfig.NMJv2_DATABASE}"
                                       class="form-control"
                                       placeholder="automatically filled via the 'Find Database'"
                                       autocapitalize="off" ${(' readonly="readonly"', '')[sickrage.srCore.srConfig.NMJv2_DATABASE == True]}/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMJv2-result">Click below to test.</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test NMJv2" id="testNMJv2"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_nmjv2 //-->
            </fieldset>
        </div><!-- /nmjv2 tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/synoindex.png" alt=""
                     title="Synology"/>
                <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Synology</a></h3>
                <p>The Synology DiskStation NAS.</p>
                <p>Synology Indexer is the daemon running on the Synology NAS to build its media
                    database.</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_synoindex"
                               id="use_synoindex" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_SYNOINDEX)]}/>
                        <label for="use_synoindex">
                            should SickRage send Synology notifications ?<br/>
                            <b>Note:</b> requires SickRage to be running on your Synology NAS.
                        </label>
                    </div>
                </div>

                <div id="content_use_synoindex">
                    <div class="row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_synoindex //-->
            </fieldset>
        </div><!-- /synoindex tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/synologynotifier.png" alt=""
                     title="Synology Indexer"/>
                <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Synology Notifier</a></h3>
                <p>Synology Notifier is the notification system of Synology DSM</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_synologynotifier"
                               id="use_synologynotifier" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_SYNOLOGYNOTIFIER)]}/>
                        <label for="use_synologynotifier">
                            should SickRage send notifications to the Synology Notifier ?<br/>
                            <b>Note:</b> requires SickRage to be running on your Synology DSM.
                        </label>
                    </div>
                </div>
                <div id="content_use_synologynotifier">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_onsnatch"
                                   id="synologynotifier_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)]}/>
                            <label for="synologynotifier_notify_onsnatch"><p>send a notification when a download starts
                                ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_ondownload"
                                   id="synologynotifier_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="synologynotifier_notify_ondownload"><p>send a notification when a download
                                finishes ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="synologynotifier_notify_onsubtitledownload"
                                   id="synologynotifier_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="synologynotifier_notify_onsubtitledownload"><p>send a notification when
                                subtitles are downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div><!-- /synology notifier tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pytivo.png" alt=""
                     title="pyTivo"/>
                <h3><a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">pyTivo</a>
                </h3>
                <p>pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads
                    to
                    your Tivo.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pytivo"
                               id="use_pytivo" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PYTIVO)]}/>
                        <label for="use_pytivo">
                            should SickRage send notifications to pyTivo ?<br/>
                            <b>Note:</b> requires the downloaded files to be accessible by pyTivo.
                        </label>
                    </div>
                </div>

                <div id="content_use_pytivo">
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">pyTivo IP:Port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="pytivo_host" id="pytivo_host"
                                       value="${sickrage.srCore.srConfig.PYTIVO_HOST}"
                                       class="form-control"
                                       placeholder="ex. 192.168.1.1:9032"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">pyTivo share name</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-book"></span>
                                </div>
                                <input name="pytivo_share_name" id="pytivo_share_name"
                                       value="${sickrage.srCore.srConfig.PYTIVO_SHARE_NAME}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pytivo_share_name">value used in pyTivo Web Configuration to name the
                                share.</label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Tivo name</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-book"></span>
                                </div>
                                <input name="pytivo_tivo_name" id="pytivo_tivo_name"
                                       value="${sickrage.srCore.srConfig.PYTIVO_TIVO_NAME}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pytivo_tivo_name">(Messages &amp; Settings > Account &amp; System
                                Information > System Information > DVR name)</label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_pytivo //-->
            </fieldset>
        </div><!-- /tab-pane //-->
    </div>

    <div id="tabs-2" class="row tab-pane fade">
        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/growl.png" alt=""
                     title="Growl"/>
                <h3><a href="${anon_url('http://growl.info/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Growl</a></h3>
                <p>A cross-platform unobtrusive global notification system.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_growl"
                               id="use_growl" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_GROWL)]}/>
                        <label for="use_growl"><p>should SickRage send Growl notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_growl">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_onsnatch"
                                   id="growl_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.GROWL_NOTIFY_ONSNATCH)]}/>
                            <label for="growl_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_ondownload"
                                   id="growl_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.GROWL_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="growl_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="growl_notify_onsubtitledownload"
                                   id="growl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="growl_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Growl IP:Port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="growl_host" id="growl_host"
                                       value="${sickrage.srCore.srConfig.GROWL_HOST}"
                                       placeholder="ex. 192.168.1.100:23053"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Growl password</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input type="password" name="growl_password" id="growl_password"
                                       value="${sickrage.srCore.srConfig.GROWL_PASSWORD}"
                                       class="form-control"
                                       placeholder="blank = no authentication"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testGrowl-result">Click below to rex.ster and test
                                Growl,
                                this is required for Growl notifications to work.
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Register Growl" id="testGrowl"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_growl //-->

            </fieldset>
        </div><!-- /growl tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/prowl.png" alt="Prowl"
                     title="Prowl"/>
                <h3><a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Prowl</a></h3>
                <p>A Growl client for iOS.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_prowl"
                               id="use_prowl" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PROWL)]}/>
                        <label for="use_prowl"><p>should SickRage send Prowl notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_prowl">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_onsnatch"
                                   id="prowl_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.PROWL_NOTIFY_ONSNATCH)]}/>
                            <label for="prowl_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_ondownload"
                                   id="prowl_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PROWL_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="prowl_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="prowl_notify_onsubtitledownload"
                                   id="prowl_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="prowl_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Prowl API key:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="prowl_api" id="prowl_api"
                                       value="${sickrage.srCore.srConfig.PROWL_API}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="prowl_api">get your key at: <a
                                    href="${anon_url('https://www.prowlapp.com/api_settings.php')}"
                                    rel="noreferrer"
                                    onclick="window.open(this.href, '_blank'); return false;">https://www.prowlapp.com/api_settings.php</a></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Prowl priority:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-exclamation"></span>
                                </div>
                                <select id="prowl_priority" name="prowl_priority" class="form-control ">
                                    <option value="-2" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROWL_PRIORITY == '-2']}>
                                        Very Low
                                    </option>
                                    <option value="-1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROWL_PRIORITY == '-1']}>
                                        Moderate
                                    </option>
                                    <option value="0" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROWL_PRIORITY == '0']}>
                                        Normal
                                    </option>
                                    <option value="1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROWL_PRIORITY == '1']}>
                                        High
                                    </option>
                                    <option value="2" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROWL_PRIORITY == '2']}>
                                        Emergency
                                    </option>
                                </select>
                            </div>
                            <label for="prowl_priority">priority of Prowl messages from SickRage.</label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testProwl-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Prowl" id="testProwl"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_prowl //-->

            </fieldset>
        </div><!-- /prowl tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/libnotify.png" alt=""
                     title="Libnotify"/>
                <h3><a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Libnotify</a></h3>
                <p>The standard desktop notification API for Linux/*nix systems. This notifier will only
                    function if the pynotify module is installed (Ubuntu/Debian package <a
                            href="apt:python-notify">python-notify</a>).</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_libnotify"
                               id="use_libnotify" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_LIBNOTIFY)]}/>
                        <label for="use_libnotify"><p>should SickRage send Libnotify notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_libnotify">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_onsnatch"
                                   id="libnotify_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSNATCH)]}/>
                            <label for="libnotify_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_ondownload"
                                   id="libnotify_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="libnotify_notify_ondownload"><p>send a notification when a download finishes
                                ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="libnotify_notify_onsubtitledownload"
                                   id="libnotify_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="libnotify_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testLibnotify-result">Click below to test.</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Libnotify" id="testLibnotify"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_libnotify //-->
            </fieldset>
        </div><!-- /libnotify tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushover.png" alt=""
                     title="Pushover"/>
                <h3><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushover</a></h3>
                <p>Pushover makes it easy to send real-time notifications to your Android and iOS
                    devices.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushover"
                               id="use_pushover" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PUSHOVER)]}/>
                        <label for="use_pushover"><p>should SickRage send Pushover notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_pushover">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_onsnatch"
                                   id="pushover_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSNATCH)]}/>
                            <label for="pushover_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_ondownload"
                                   id="pushover_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="pushover_notify_ondownload"><p>send a notification when a download finishes
                                ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushover_notify_onsubtitledownload"
                                   id="pushover_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="pushover_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">

                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushover key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input name="pushover_userkey" id="pushover_userkey"
                                       value="${sickrage.srCore.srConfig.PUSHOVER_USERKEY}"
                                       class="form-control"
                                       placeholder="user key of your Pushover account"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushover API key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="pushover_apikey" id="pushover_apikey"
                                       value="${sickrage.srCore.srConfig.PUSHOVER_APIKEY}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                            <label for="pushover_apikey">
                                <a href="${anon_url('https://pushover.net/apps/clone/sickrage')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;"><b>Click here</b></a> to
                                create a Pushover API key
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushover devices</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-list-alt"></span>
                                </div>
                                <input name="pushover_device" id="pushover_device"
                                       value="${sickrage.srCore.srConfig.PUSHOVER_DEVICE}"
                                       placeholder="ex. device1,device2"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushover notification sound</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-music"></span>
                                </div>
                                <select id="pushover_sound" name="pushover_sound" class="form-control ">
                                    <option value="pushover" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'pushover']}>
                                        Pushover
                                    </option>
                                    <option value="bike" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'bike']}>
                                        Bike
                                    </option>
                                    <option value="bugle" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'bugle']}>
                                        Bugle
                                    </option>
                                    <option value="cashregister" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'cashregister']}>
                                        Cash Rex.ster
                                    </option>
                                    <option value="classical" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'classical']}>
                                        Classical
                                    </option>
                                    <option value="cosmic" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'cosmic']}>
                                        Cosmic
                                    </option>
                                    <option value="falling" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'falling']}>
                                        Falling
                                    </option>
                                    <option value="gamelan" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'gamelan']}>
                                        Gamelan
                                    </option>
                                    <option value="incoming" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'incoming']}>
                                        Incoming
                                    </option>
                                    <option value="intermission" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'intermission']}>
                                        Intermission
                                    </option>
                                    <option value="magic" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'magic']}>
                                        Magic
                                    </option>
                                    <option value="mechanical" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'mechanical']}>
                                        Mechanical
                                    </option>
                                    <option value="pianobar" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'pianobar']}>
                                        Piano Bar
                                    </option>
                                    <option value="siren" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'siren']}>
                                        Siren
                                    </option>
                                    <option value="spacealarm" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'spacealarm']}>
                                        Space Alarm
                                    </option>
                                    <option value="tugboat" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'tugboat']}>
                                        Tug Boat
                                    </option>
                                    <option value="alien" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'alien']}>
                                        Alien Alarm (long)
                                    </option>
                                    <option value="climb" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'climb']}>
                                        Climb (long)
                                    </option>
                                    <option value="persistent" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'persistent']}>
                                        Persistent (long)
                                    </option>
                                    <option value="echo" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'echo']}>
                                        Pushover Echo (long)
                                    </option>
                                    <option value="updown" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'updown']}>
                                        Up Down (long)
                                    </option>
                                    <option value="none" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'none']}>
                                        None (silent)
                                    </option>
                                    <option value="default" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PUSHOVER_SOUND == 'default']}>
                                        Device specific
                                    </option>
                                </select>
                            </div>
                            <label for="pushover_sound">
                                Choose notification sound to use
                            </label>
                        </div>
                    </div>
                    <div class="testNotification" id="testPushover-result">Click below to test.</div>
                    <input class="btn" type="button" value="Test Pushover" id="testPushover"/>
                    <input type="submit" class="config_submitter btn" value="Save Changes"/>
                </div><!-- /content_use_pushover //-->

            </fieldset>
        </div><!-- /pushover tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/boxcar.png" alt=""
                     title="Boxcar"/>
                <h3><a href="${anon_url('http://boxcar.io/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Boxcar</a></h3>
                <p>Universal push notification for iOS. Read your messages where and when you want them! A
                    subscription will be sent if needed.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_boxcar"
                               id="use_boxcar" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_BOXCAR)]}/>
                        <label for="use_boxcar"><p>should SickRage send Boxcar notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_boxcar">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar_notify_onsnatch"
                                   id="boxcar_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONSNATCH)]}/>
                            <label for="boxcar_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar_notify_ondownload"
                                   id="boxcar_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="boxcar_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar_notify_onsubtitledownload"
                                   id="boxcar_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="boxcar_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Boxcar username</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="boxcar_username" id="boxcar_username"
                                       value="${sickrage.srCore.srConfig.BOXCAR_USERNAME}"
                                       class="form-control"
                                       placeholder="username of your Boxcar account"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testBoxcar-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Boxcar" id="testBoxcar"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_boxcar //-->

            </fieldset>
        </div><!-- /boxcar tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/boxcar2.png" alt=""
                     title="Boxcar2"/>
                <h3><a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Boxcar2</a></h3>
                <p>Read your messages where and when you want them!</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_boxcar2"
                               id="use_boxcar2" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_BOXCAR2)]}/>
                        <label for="use_boxcar2"><p>should SickRage send Boxcar2 notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_boxcar2">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_onsnatch"
                                   id="boxcar2_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONSNATCH)]}/>
                            <label for="boxcar2_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_ondownload"
                                   id="boxcar2_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="boxcar2_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="boxcar2_notify_onsubtitledownload"
                                   id="boxcar2_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="boxcar2_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Boxcar2 access token</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="boxcar2_accesstoken" id="boxcar2_accesstoken"
                                       value="${sickrage.srCore.srConfig.BOXCAR2_ACCESSTOKEN}"
                                       placeholder="access token for your Boxcar2 account"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testBoxcar2-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Boxcar2" id="testBoxcar2"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_boxcar2 //-->

            </fieldset>
        </div><!-- /boxcar2 tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/nma.png" alt="" title="NMA"/>
                <h3><a href="${anon_url('http://nma.usk.bz')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Notify My Android</a></h3>
                <p>Notify My Android is a Prowl-like Android App and API that offers an easy way to send
                    notifications from your application directly to your Android device.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_nma"
                               id="use_nma" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_NMA)]}/>
                        <label for="use_nma"><p>should SickRage send NMA notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_nma">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_onsnatch"
                                   id="nma_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.NMA_NOTIFY_ONSNATCH)]}/>
                            <label for="nma_notify_onsnatch"><p>send a notification when a download starts ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_ondownload"
                                   id="nma_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.NMA_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="nma_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="nma_notify_onsubtitledownload"
                                   id="nma_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="nma_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NMA API key:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="nma_api" id="nma_api"
                                       value="${sickrage.srCore.srConfig.NMA_API}"
                                       placeholder="ex. key1,key2 (max 5)"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">NMA priority:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-exclamation-sign"></span>
                                </div>
                                <select id="nma_priority" name="nma_priority" class="form-control ">
                                    <option value="-2" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NMA_PRIORITY == '-2']}>
                                        Very Low
                                    </option>
                                    <option value="-1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NMA_PRIORITY == '-1']}>
                                        Moderate
                                    </option>
                                    <option value="0" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NMA_PRIORITY == '0']}>
                                        Normal
                                    </option>
                                    <option value="1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NMA_PRIORITY == '1']}>
                                        High
                                    </option>
                                    <option value="2" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NMA_PRIORITY == '2']}>
                                        Emergency
                                    </option>
                                </select>
                            </div>
                            <label for="nma_priority">
                                priority of NMA messages from SickRage.
                            </label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testNMA-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test NMA" id="testNMA"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_nma //-->

            </fieldset>
        </div><!-- /nma tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushalot.png" alt=""
                     title="Pushalot"/>
                <h3><a href="${anon_url('https://pushalot.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushalot</a></h3>
                <p>Pushalot is a platform for receiving custom push notifications to connected devices
                    running
                    Windows Phone or Windows 8.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushalot"
                               id="use_pushalot" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PUSHALOT)]}/>
                        <label for="use_pushalot"><p>should SickRage send Pushalot notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_pushalot">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_onsnatch"
                                   id="pushalot_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSNATCH)]}/>
                            <label for="pushalot_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_ondownload"
                                   id="pushalot_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="pushalot_notify_ondownload"><p>send a notification when a download finishes
                                ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushalot_notify_onsubtitledownload"
                                   id="pushalot_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="pushalot_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushalot authorization token</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="pushalot_authorizationtoken"
                                       id="pushalot_authorizationtoken"
                                       value="${sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN}"
                                       placeholder="authorization token of your Pushalot account."
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testPushalot-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="Test Pushalot" id="testPushalot"/>
                            <input type="submit" class="btn config_submitter" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_pushalot //-->

            </fieldset>
        </div><!-- /pushalot tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/pushbullet.png" alt=""
                     title="Pushbullet"/>
                <h3><a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Pushbullet</a></h3>
                <p>Pushbullet is a platform for receiving custom push notifications to connected devices
                    running
                    Android and desktop Chrome browsers.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_pushbullet"
                               id="use_pushbullet" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_PUSHBULLET)]}/>
                        <label for="use_pushbullet"><p>should SickRage send Pushbullet notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_pushbullet">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_onsnatch"
                                   id="pushbullet_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSNATCH)]}/>
                            <label for="pushbullet_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_ondownload"
                                   id="pushbullet_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="pushbullet_notify_ondownload"><p>send a notification when a download finishes
                                ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="pushbullet_notify_onsubtitledownload"
                                   id="pushbullet_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="pushbullet_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushbullet API key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="pushbullet_api" id="pushbullet_api"
                                       value="${sickrage.srCore.srConfig.PUSHBULLET_API}"
                                       class="form-control"
                                       placeholder="API key of your Pushbullet account"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Pushbullet devices</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="input-group input350">
                                        <div class="input-group-addon">
                                            <span class="glyphicon glyphicon-list"></span>
                                        </div>
                                        <select name="pushbullet_device_list" id="pushbullet_device_list"
                                                class="form-control "></select>
                                    </div>
                                    <label for="pushbullet_device_list">select device you wish to push to.</label>
                                </div>
                            </div>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="hidden" id="pushbullet_device"
                                           value="${sickrage.srCore.srConfig.PUSHBULLET_DEVICE}">
                                    <input type="button" class="btn btn-inline" value="Update device list"
                                           id="getPushbulletDevices"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testPushbullet-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="Test Pushbullet" id="testPushbullet"/>
                            <input type="submit" class="btn config_submitter" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_pushbullet //-->

            </fieldset>
        </div><!-- /pushbullet tab-pane //-->
        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/freemobile.png" alt=""
                     title="Free Mobile"/>
                <h3><a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Free Mobile</a></h3>
                <p>Free Mobile is a famous French cellular network provider.<br> It provides to their
                    customer a
                    free SMS API.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_freemobile"
                               id="use_freemobile" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_FREEMOBILE)]}/>
                        <label for="use_freemobile"><p>should SickRage send SMS notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_freemobile">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_onsnatch"
                                   id="freemobile_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONSNATCH)]}/>
                            <label for="freemobile_notify_onsnatch"><p>send a SMS when a download starts ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_ondownload"
                                   id="freemobile_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="freemobile_notify_ondownload"><p>send a SMS when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="freemobile_notify_onsubtitledownload"
                                   id="freemobile_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="freemobile_notify_onsubtitledownload"><p>send a SMS when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Free Mobile customer ID</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="freemobile_id" id="freemobile_id"
                                       value="${sickrage.srCore.srConfig.FREEMOBILE_ID}"
                                       class="form-control"
                                       placeholder="ex. 12345678"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Free Mobile API Key</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-cloud"></span>
                                </div>
                                <input name="freemobile_apikey" id="freemobile_apikey"
                                       value="${sickrage.srCore.srConfig.FREEMOBILE_APIKEY}"
                                       class="form-control"
                                       placeholder="enter yourt API key"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testFreeMobile-result">Click below to test your
                                settings.
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test SMS" id="testFreeMobile"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_freemobile //-->
            </fieldset>
        </div><!-- /freemobile tab-pane //-->

    </div>

    <div id="tabs-3" class="row tab-pane fade">
        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/twitter.png" alt=""
                     title="Twitter"/>
                <h3><a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Twitter</a></h3>
                <p>A social networking and microblogging service, enabling its users to send and read other
                    users' messages called tweets.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_twitter"
                               id="use_twitter" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_TWITTER)]}/>
                        <label for="use_twitter">
                            should SickRage post tweets on Twitter ?<br/>
                            <b>Note:</b> you may want to use a secondary account.
                        </label>
                    </div>
                </div>

                <div id="content_use_twitter">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_onsnatch"
                                   id="twitter_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.TWITTER_NOTIFY_ONSNATCH)]}/>
                            <label for="twitter_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_ondownload"
                                   id="twitter_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.TWITTER_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="twitter_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_notify_onsubtitledownload"
                                   id="twitter_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="twitter_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Send direct message</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="twitter_usedm"
                                   id="twitter_usedm" ${('', 'checked')[bool(sickrage.srCore.srConfig.TWITTER_USEDM)]}/>
                            <label for="twitter_usedm"><p>send a notification via Direct Message, not via status
                                update</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Send DM to</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="twitter_dmto" id="twitter_dmto"
                                       value="${sickrage.srCore.srConfig.TWITTER_DMTO}"
                                       class="form-control"
                                       placeholder="Twitter account to send messages to"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Step One</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="Request Authorization" id="twitterStep1"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    Click the "Request Authorization" button.<br/>
                                    This will open a new page containing an auth key.<br/>
                                    <b>Note:</b>if nothing happens check your popup blocker.<br/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Step Two</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input id="twitter_key" value=""
                                       class="form-control"
                                       placeholder="Enter the key Twitter gave you"
                                       autocapitalize="off"/>
                                <div class="input-group-addon">
                                    <input class="button" type="button" value="Verify Key" id="twitterStep2"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTwitter-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Twitter" id="testTwitter"/>
                            <input type="submit" class="config_submitter btn" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_twitter //-->

            </fieldset>
        </div><!-- /twitter tab-pane //-->


        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/trakt.png" alt=""
                     title="Trakt"/>
                <h3><a href="${anon_url('http://trakt.tv/')}" rel="noreferrer"
                       onclick="window.open(this.href, '_blank'); return false;">Trakt</a></h3>
                <p>trakt helps keep a record of what TV shows and movies you are watching. Based on your
                    favorites, trakt recommends additional shows and movies you'll enjoy!</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_trakt"
                               id="use_trakt" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_TRAKT)]}/>
                        <label for="use_trakt"><p>should SickRage send Trakt.tv notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_trakt">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Trakt username</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="trakt_username" id="trakt_username"
                                       value="${sickrage.srCore.srConfig.TRAKT_USERNAME}"
                                       class="form-control"
                                       placeholder="username"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <input type="hidden" id="trakt_pin_url"
                           value="${sickrage.srCore.srConfig.TRAKT_PIN_URL}">
                    <input type="button"
                           class="btn ${('', 'hide')[bool(sickrage.srCore.srConfig.TRAKT_ACCESS_TOKEN)]}"
                           value="Get Trakt PIN" id="TraktGetPin"/>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Trakt PIN</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input name="trakt_pin" id="trakt_pin" value=""
                                       placeholder="authorization PIN code"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <input type="button" class="btn hide" value="Authorize SiCKRAGE" id="authTrakt"/>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">API Timeout</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-time"></span>
                                </div>
                                <input name="trakt_timeout" id="trakt_timeout"
                                       value="${sickrage.srCore.srConfig.TRAKT_TIMEOUT}"
                                       class="form-control"/>
                                <div class="input-group-addon">
                                    secs
                                </div>
                            </div>
                            <label for="trakt_timeout">
                                Seconds to wait for Trakt API to respond. (Use 0 to wait forever)
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Default indexer</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="fa fa-linode"></span>
                                </div>
                                <select id="trakt_default_indexer" name="trakt_default_indexer"
                                        class="form-control " title="Default Indexer">
                            </div>
                                % for indexer in srIndexerApi().indexers:
                                    <option value="${indexer}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TRAKT_DEFAULT_INDEXER == indexer]}>${srIndexerApi().indexers[indexer]}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Sync libraries</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" class="enabler" name="trakt_sync"
                                   id="trakt_sync" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_SYNC)]}/>
                            <label for="trakt_sync"><p>sync your SickRage show library with your trakt show library.</p>
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Remove Episodes From Collection</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_sync_remove"
                                       id="trakt_sync_remove" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_SYNC_REMOVE)]}/>
                                <label for="trakt_sync_remove"><p>Remove an Episode from your Trakt Collection if it is
                                    not in your SickRage
                                    Library.</p></label>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Sync watchlist</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" class="enabler" name="trakt_sync_watchlist"
                                   id="trakt_sync_watchlist" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_SYNC_WATCHLIST)]}/>
                            <label for="trakt_sync_watchlist">
                                sync your SickRage show watchlist with your trakt show watchlist (either Show and
                                Episode).<br/>
                                <p>Episode will be added on watch list when wanted or snatched and will be removed when
                                    downloaded </p>
                            </label>
                        </div>
                    </div>
                    <div id="content_trakt_sync_watchlist">
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Watchlist add method</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="input-group input350">
                                    <div class="input-group-addon">
                                        <span class="fa fa-binoculars"></span>
                                    </div>
                                    <select id="trakt_method_add" name="trakt_method_add"
                                            class="form-control ">
                                        <option value="0" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TRAKT_METHOD_ADD == 0]}>
                                            Skip All
                                        </option>
                                        <option value="1" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TRAKT_METHOD_ADD == 1]}>
                                            Download Pilot Only
                                        </option>
                                        <option value="2" ${('', 'selected="selected"')[sickrage.srCore.srConfig.TRAKT_METHOD_ADD == 2]}>
                                            Get whole show
                                        </option>
                                    </select>
                                </div>
                                <label for="trakt_method_add">
                                    method in which to download episodes for new show's.
                                </label>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Remove episode</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_watchlist"
                                       id="trakt_remove_watchlist" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_REMOVE_WATCHLIST)]}/>
                                <label for="trakt_remove_watchlist"><p>remove an episode from your watchlist after it is
                                    downloaded.</p></label>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Remove series</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_serieslist"
                                       id="trakt_remove_serieslist" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_REMOVE_SERIESLIST)]}/>
                                <label for="trakt_remove_serieslist"><p>remove the whole series from your watchlist
                                    after any download.</p></label>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Remove watched show:</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_remove_show_from_sickrage"
                                       id="trakt_remove_show_from_sickrage" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)]}/>
                                <label for="trakt_remove_show_from_sickrage"><p>remove the show from sickrage if it's
                                    ended and completely watched</p></label>
                            </div>
                        </div>
                        <div class="row field-pair">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">Start paused</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" name="trakt_start_paused"
                                       id="trakt_start_paused" ${('', 'checked')[bool(sickrage.srCore.srConfig.TRAKT_START_PAUSED)]}/>
                                <label for="trakt_start_paused"><p>show's grabbed from your trakt watchlist start
                                    paused.</p></label>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Trakt blackList name</label>
                        </div>
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-list"></span>
                                </div>
                                <input name="trakt_blacklist_name" id="trakt_blacklist_name"
                                       value="${sickrage.srCore.srConfig.TRAKT_BLACKLIST_NAME}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="trakt_blacklist_name">
                                Name(slug) of List on Trakt for blacklisting show on 'Add Trending Show' & 'Add
                                Recommended Shows' pages
                            </label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testTrakt-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input type="button" class="btn" value="Test Trakt" id="testTrakt"/>
                            <input type="submit" class="btn config_submitter" value="Save Changes"/>
                        </div>
                    </div>

                </div><!-- /content_use_trakt //-->
            </fieldset>
        </div><!-- /trakt tab-pane //-->

        <div class="tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/notifiers/email.png" alt=""
                     title="Email"/>
                <h3><a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}"
                       rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Email</a>
                </h3>
                <p>Allows configuration of email notifications on a per show basis.</p>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_email"
                               id="use_email" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_EMAIL)]}/>
                        <label for="use_email"><p>should SickRage send email notifications ?</p></label>
                    </div>
                </div>

                <div id="content_use_email">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on snatch</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_onsnatch"
                                   id="email_notify_onsnatch" ${('', 'checked')[bool(sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSNATCH)]}/>
                            <label for="email_notify_onsnatch"><p>send a notification when a download starts ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_ondownload"
                                   id="email_notify_ondownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.EMAIL_NOTIFY_ONDOWNLOAD)]}/>
                            <label for="email_notify_ondownload"><p>send a notification when a download finishes ?</p>
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Notify on subtitle download</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_notify_onsubtitledownload"
                                   id="email_notify_onsubtitledownload" ${('', 'checked')[bool(sickrage.srCore.srConfig.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                            <label for="email_notify_onsubtitledownload"><p>send a notification when subtitles are
                                downloaded ?</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">SMTP host</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="email_host" id="email_host"
                                       value="${sickrage.srCore.srConfig.EMAIL_HOST}"
                                       placeholder="SMTP server address"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">SMTP port</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-globe"></span>
                                </div>
                                <input name="email_port" id="email_port"
                                       value="${sickrage.srCore.srConfig.EMAIL_PORT}"
                                       placeholder="SMTP server port number"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">SMTP from</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-envelope"></span>
                                </div>
                                <input name="email_from" id="email_from"
                                       value="${sickrage.srCore.srConfig.EMAIL_FROM}"
                                       placeholder="sender email address"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Use TLS</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="email_tls"
                                   id="email_tls" ${('', 'checked')[bool(sickrage.srCore.srConfig.EMAIL_TLS)]}/>
                            <label for="email_tls"><p>check to use TLS encryption.</p></label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">SMTP user</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input name="email_user" id="email_user"
                                       value="${sickrage.srCore.srConfig.EMAIL_USER}"
                                       placeholder="optional"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">SMTP password</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input type="password" name="email_password" id="email_password"
                                       value="${sickrage.srCore.srConfig.EMAIL_PASSWORD}"
                                       placeholder="optional"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Global email list</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-envelope"></span>
                                </div>
                                <input name="email_list" id="email_list"
                                       value="${sickrage.srCore.srConfig.EMAIL_LIST}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label for="email_list">
                                all emails here receive notifications for <b>all</b> shows.
                            </label>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Show notification list</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="input-group input350">
                                        <div class="input-group-addon">
                                            <span class="glyphicon glyphicon-list"></span>
                                        </div>
                                        <select name="email_show" id="email_show" class="form-control ">
                                            <option value="-1">-- Select a Show --</option>
                                        </select>
                                    </div>
                                    <label for="email_show">configure per show notifications here.</label>
                                </div>
                            </div>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="input-group input350">
                                        <div class="input-group-addon">
                                            <span class="glyphicon glyphicon-envelope"></span>
                                        </div>
                                        <input name="email_show_list" id="email_show_list" class="form-control"
                                               autocapitalize="off"/>
                                    </div>
                                    <label for="email_show_list">
                                        configure per-show notifications here by entering email address(es), separated by commas,
                                        after selecting a show in the drop-down box.  Be sure to activate the Save for this show
                                        button below after each entry.
                                    </label>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input id="email_show_save" class="btn" type="button" value="Save for this show"/>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <div class="testNotification" id="testEmail-result">Click below to test.</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" type="button" value="Test Email" id="testEmail"/>
                            <input class="btn config_submitter" type="submit" value="Save Changes"/>
                        </div>
                    </div>
                </div><!-- /content_use_email //-->
            </fieldset>
        </div><!-- /email tab-pane //-->
    </div>
</%block>
