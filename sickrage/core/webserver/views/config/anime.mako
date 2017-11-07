<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveAnime' %></%def>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
%>

<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">${_('AnimeDB Settings')}</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">${_('User Interface')}</a></li>
</%block>

<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/anidb24.png" alt="AniDB" title="${_('AniDB')}"
                     width="24" height="24"/>
                <h3><a href="${anon_url('http://anidb.info')}"
                       onclick="window.open(this.href, '_blank'); return false;">AniDB</a></h3>
                <p>${_('AniDB is non-profit database of anime information that is freely open to the public')}</p>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_anidb"
                               id="use_anidb" ${('', 'checked')[bool(sickrage.app.config.USE_ANIDB)]} />
                        <label for="use_anidb">
                            ${_('Enable AniDB')}
                        </label>
                    </div>
                </div>

                <div id="content_use_anidb">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('AniDB Username')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-user"></span>
                                </div>
                                <input type="text" name="anidb_username" id="anidb_username"
                                       value="${sickrage.app.config.ANIDB_USERNAME}"
                                       title="${_('AniDB Username')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('AniDB Password')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-lock"></span>
                                </div>
                                <input type="password" name="anidb_password" id="anidb_password"
                                       value="${sickrage.app.config.ANIDB_PASSWORD}"
                                       title="${_('AniDB Password')}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${_('AniDB MyList')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="anidb_use_mylist"
                                   id="anidb_use_mylist" ${('', 'checked')[bool(sickrage.app.config.ANIDB_USE_MYLIST)]}/>
                            <label for="anidb_use_mylist">
                                ${_('Do you want to add the PostProcessed Episodes to the MyList ?')}
                            </label>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div>

    <div id="core-tab-pane2" class="tab-pane fade">
        <div class="row tab-pane">
            <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
                <h3>${_('User Interface')}</h3>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">${_('Split show lists')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="split_home"
                               id="split_home" ${('', 'checked')[bool(sickrage.app.config.ANIME_SPLIT_HOME)]}/>
                        <label for="split_home">
                            ${_('Separate anime and normal shows in groups')}
                        </label>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div>
</%block>