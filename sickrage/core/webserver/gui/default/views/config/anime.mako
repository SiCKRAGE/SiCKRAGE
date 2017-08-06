<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveAnime' %></%def>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
%>

<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">AnimeDB Settings</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Look &amp; Feel</a></li>
</%block>

<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="tab-pane">
            <div class="tab-pane-desc">
                <img class="notifier-icon" src="${srWebRoot}/images/anidb24.png" alt="AniDB" title="AniDB"
                     width="24" height="24"/>
                <h3><a href="${anon_url('http://anidb.info')}"
                       onclick="window.open(this.href, '_blank'); return false;">AniDB</a></h3>
                <p>AniDB is non-profit database of anime information that is freely open to the public</p>
            </div>

            <fieldset class="tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Enable AniDB</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="use_anidb"
                               id="use_anidb" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_ANIDB)]} />
                        <label for="use_anidb">
                            Should SickRage use data from AniDB?
                        </label>
                    </div>
                </div>

                <div id="content_use_anidb">
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">AniDB Username</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="text" name="anidb_username" id="anidb_username"
                                           value="${sickrage.srCore.srConfig.ANIDB_USERNAME}"
                                           class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="anidb_username">
                                        Username of your AniDB account
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">AniDB Password</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="password" name="anidb_password" id="anidb_password"
                                           value="${sickrage.srCore.srConfig.ANIDB_PASSWORD}"
                                           class="form-control input-sm input350"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="anidb_password">Password of your AniDB account</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">AniDB MyList</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input type="checkbox" name="anidb_use_mylist"
                                   id="anidb_use_mylist" ${('', 'checked')[bool(sickrage.srCore.srConfig.ANIDB_USE_MYLIST)]}/>
                            <label for="anidb_use_mylist">
                                Do you want to add the PostProcessed Episodes to the MyList ?
                            </label>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>

            </fieldset>
        </div>
    </div>

    <div id="core-tab-pane2" class="tab-pane fade">
        <div class="tab-pane">
            <div class="tab-pane-desc">
                <h3>Look and Feel</h3>
            </div>
            <fieldset class="tab-pane-list">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Split show lists</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input type="checkbox" class="enabler" name="split_home"
                               id="split_home" ${('', 'checked')[bool(sickrage.srCore.srConfig.ANIME_SPLIT_HOME)]}/>
                        <label for="split_home">
                            Separate anime and normal shows in groups
                        </label>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="Save Changes"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div>
</%block>