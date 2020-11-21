<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveAnime' %></%def>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
%>

<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#settings">${_('AnimeDB Settings')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#interface">${_('User Interface')}</a></li>
</%block>

<%block name="pages">
    <div id="settings" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>
                    <i class="sickrage-core sickrage-core-anidb" title="${_('AniDB')}"></i>
                    <a href="${anon_url('http://anidb.info')}"
                       onclick="window.open(this.href, '_blank'); return false;">AniDB</a>
                </h3>
                <small class="form-text text-muted">
                    ${_('AniDB is non-profit database of anime information that is freely open to the public')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="use_anidb">
                            <input type="checkbox" class="enabler toggle color-primary is-material" name="use_anidb"
                                   id="use_anidb" ${('', 'checked')[bool(sickrage.app.config.anidb.enable)]} />
                            ${_('Enable AniDB')}
                        </label>
                    </div>
                </div>

                <div id="content_use_anidb">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('AniDB Username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-user"></span>
                                    </span>
                                </div>
                                <input type="text" name="anidb_username" id="anidb_username"
                                       value="${sickrage.app.config.anidb.username}"
                                       title="${_('AniDB Username')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('AniDB Password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-lock"></span>
                                    </span>
                                </div>
                                <input type="password" name="anidb_password" id="anidb_password"
                                       value="${sickrage.app.config.anidb.password}"
                                       title="${_('AniDB Password')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('AniDB MyList')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="anidb_use_mylist">
                                <input type="checkbox" class="toggle color-primary is-material" name="anidb_use_mylist"
                                       id="anidb_use_mylist" ${('', 'checked')[bool(sickrage.app.config.anidb.use_my_list)]}/>
                                ${_('Do you want to add the PostProcessed Episodes to the MyList ?')}
                            </label>
                        </div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div>

    <div id="interface" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('User Interface')}</h3>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Split show lists')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <input type="checkbox" class="enabler toggle color-primary is-material" name="split_home"
                               id="split_home" ${('', 'checked')[bool(sickrage.app.config.anidb.split_home)]}/>
                        <label for="split_home">
                            ${_('Separate anime and normal shows in groups')}
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
    </div>
</%block>