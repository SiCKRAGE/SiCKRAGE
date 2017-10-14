<%inherit file="../layouts/main.mako"/>
<%!
    import sys, os, tornado

    import sickrage
    from sickrage.core.helpers import anon_url

    sr_user = None
    try:
        import pwd
        sr_user = pwd.getpwuid(os.getuid()).pw_name
    except ImportError:
        import getpass
        sr_user = getpass.getuser()
%>

<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <div class="panel panel-default">
                <div class="panel-body">
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-version"></i> ${_('SR Version')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sickrage.srCore.VERSIONUPDATER.updater.version}
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-type"></i> ${_('SR Type')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sickrage.srCore.VERSIONUPDATER.updater.type}
                        </div>
                    </div>
                    <br/>
                    % if sr_user:
                        <div class="row">
                            <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                                <i class="icons-sickrage icons-sickrage-user"></i> ${_('SR User')}:
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                                ${sr_user}
                            </div>
                        </div>
                        <br/>
                    % endif
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12"><i
                                class="icons-sickrage icons-sickrage-locale"></i> ${_('SR Locale')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">${sickrage.srCore.SYS_ENCODING}</div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-cfg"></i> ${_('SR Config')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sickrage.CONFIG_FILE}
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-cache"></i> ${_('SR Cache Dir')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sickrage.CACHE_DIR}
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-log"></i> ${_('SR Log Dir')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sickrage.srCore.srConfig.LOG_DIR}
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-console"></i> ${_('SR Arguments')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sys.argv[1:]}
                        </div>
                    </div>
                    <br/>
                    % if sickrage.srCore.srConfig.WEB_ROOT:
                        <div class="row">
                            <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                                ${_('SR Web Root')}:
                            </div>
                            <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                                ${sickrage.srCore.srConfig.WEB_ROOT}
                            </div>
                        </div>
                        <br/>
                    % endif
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-tornado"></i> ${_('Tornado Version')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${tornado.version}
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-python"></i> ${_('Python Version')}:
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            ${sys.version}
                        </div>
                    </div>
                    <hr/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-logo"></i> ${_('Homepage')}
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            <a href="${anon_url('https://www.sickrage.ca/')}"
                               rel="noreferrer"
                               onclick="window.open(this.href, '_blank'); return false;">https://www.sickrage.ca/</a>
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-wiki"></i> ${_('WiKi')}
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            <a href="${anon_url('https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/home')}"
                               rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/home</a>
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-forums"></i> ${_('Forums')}
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            <a href="${anon_url('https://sickrage.ca/forums/')}"
                               rel="noreferrer"
                               onclick="window.open(this.href, '_blank'); return false;">https://www.sickrage.ca/forums/</a>
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-git"></i> ${_('Source')}
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            <a href="${anon_url('https://git.sickrage.ca/SiCKRAGE/sickrage/')}"
                               rel="noreferrer"
                               onclick="window.open(this.href, '_blank'); return false;">https://git.sickrage.ca/SiCKRAGE/sickrage/</a>
                        </div>
                    </div>
                    <br/>
                    <div class="row">
                        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                            <i class="icons-sickrage icons-sickrage-irc"></i> ${_('IRChat')}
                        </div>
                        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                            <a href="irc://irc.freenode.net/#sickrage" rel="noreferrer"><i>#sickrage</i>
                                ${_('on')} <i>irc.freenode.net</i></a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
