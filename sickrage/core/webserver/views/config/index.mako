<%inherit file="../layouts/main.mako"/>
<%!
    import sys, os, tornado, locale

    import sickrage
    from sickrage.core.helpers import anon_url
%>

<%block name="content">
    <div class="form-row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-body">
                    <div class="card-text">
                        % if sickrage.app.config.user.sub_id:
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-keys"></i> ${_('SR Sub ID:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${sickrage.app.config.user.sub_id}
                                </div>
                            </div>
                            <br/>
                        % endif
                        % if sickrage.app.config.general.server_id:
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-keys"></i> ${_('SR App ID:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${sickrage.app.config.general.server_id}
                                </div>
                            </div>
                            <br/>
                        % endif
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-version"></i> ${_('SR Version:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sickrage.version()}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-type"></i> ${_('SR Install Type:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sickrage.app.version_updater.updater.type.upper()}
                            </div>
                        </div>
                        <br/>
                        % if sickrage.app.version_updater.updater.type == 'git':
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-commit"></i> ${_('SR GIT Commit:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${sickrage.app.version_updater.version}
                                </div>
                            </div>
                            <br/>
                        % elif os.environ.get('SOURCE_COMMIT'):
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-commit"></i> ${_('SR Source Commit:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${os.environ.get('SOURCE_COMMIT')}
                                </div>
                            </div>
                            <br/>
                        % endif
                        % if isinstance(current_user, dict):
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-user"></i> ${_('SR Username:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${current_user['preferred_username']}
                                </div>
                            </div>
                            <br/>
                        % endif
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-cfg"></i> ${_('SR Config File:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sickrage.app.config_file}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-cache"></i> ${_('SR Cache Dir:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sickrage.app.cache_dir}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-log"></i> ${_('SR Log File:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sickrage.app.log.logFile}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-console"></i> ${_('SR Arguments:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sys.argv[1:]}
                            </div>
                        </div>
                        <br/>
                        % if sickrage.app.config.general.web_root:
                            <div class="form-row">
                                <div class="col-lg-3 col-md-3 col-sm-3">
                                    <i class="sickrage-core sickrage-core-version"></i> ${_('SR Web Root:')}
                                </div>
                                <div class="col-lg-9 col-md-9 col-sm-9">
                                    ${sickrage.app.config.general.web_root}
                                </div>
                            </div>
                            <br/>
                        % endif
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-version"></i> ${_('Locale:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${locale.getdefaultlocale()}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-tornado"></i> ${_('Tornado Version:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${tornado.version}
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-python"></i> ${_('Python Version:')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                ${sys.version}
                            </div>
                        </div>
                        <hr/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-logo"></i> ${_('Homepage')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                <a href="${anon_url('https://www.sickrage.ca/')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;">https://www.sickrage.ca/</a>
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-wiki"></i> ${_('WiKi')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                <a href="${anon_url('https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/home')}"
                                   rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/home</a>
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-forums"></i> ${_('Forums')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                <a href="${anon_url('https://forums.sickrage.ca/')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;">https://forums.sickrage.ca/</a>
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-git"></i> ${_('Source')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                <a href="${anon_url('https://git.sickrage.ca/SiCKRAGE/sickrage/')}"
                                   rel="noreferrer"
                                   onclick="window.open(this.href, '_blank'); return false;">https://git.sickrage.ca/SiCKRAGE/sickrage/</a>
                            </div>
                        </div>
                        <br/>
                        <div class="form-row">
                            <div class="col-lg-3 col-md-3 col-sm-3">
                                <i class="sickrage-core sickrage-core-irc"></i> ${_('IRChat')}
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9">
                                <a href="irc://irc.freenode.net/#sickrage" rel="noreferrer"><i>#sickrage</i>
                                    ${_('on')} <i>irc.freenode.net</i></a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
