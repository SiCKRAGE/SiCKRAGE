<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.indexers import adba, srIndexerApi
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import statusStrings, Quality
%>

<%block name="metas">
    <meta data-var="show.is_anime" data-content="${show.is_anime}">
</%block>

<%block name="content">
    <div id="show">
        <div class="row">
            <div class="col-md-12">
                <h1 class="title">${title}</h1>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">

                <form action="editShow" method="post">
                    <ul class="nav nav-tabs">
                        <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Main</a></li>
                        <li><a data-toggle="tab" href="#core-tab-pane2">Format</a></li>
                        <li><a data-toggle="tab" href="#core-tab-pane3">Advanced</a></li>
                    </ul>

                    <div class="tab-content">
                        <div id="core-tab-pane1" class="tab-pane fade in active">
                            <div class="tab-pane">
                                <div class="tab-pane-desc">
                                    <h3>Main Settings</h3>
                                </div>

                                <fieldset class="tab-pane-list">
                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Show Location</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="hidden" name="show" value="${show.indexerid}"/>
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="glyphicon glyphicon-folder-open"></span>
                                                </div>
                                                <input type="text" name="location" id="location"
                                                       value="${show.location}"
                                                       class="form-control "
                                                       autocapitalize="off" title="Location" required=""/>
                                            </div>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Preferred Quality</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <% qualities = Quality.splitQuality(int(show.quality)) %>
                                            <%include file="../includes/quality_chooser.mako"/>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Default Episode Status</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="glyphicon glyphicon-list"></span>
                                                </div>
                                                <select name="defaultEpStatus" id="defaultEpStatusSelect"
                                                        title="This will set the status for future episodes."
                                                        class="form-control">
                                                    % for curStatus in [WANTED, SKIPPED, IGNORED]:
                                                        <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
                                                    % endfor
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Info Language</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <% languages = srIndexerApi().indexer().languages.keys() %>
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="glyphicon glyphicon-flag"></span>
                                                </div>
                                                <select name="indexerLang" id="indexerLangSelect"
                                                        class="form-control bfh-languages"
                                                        title="Show language"
                                                        data-language="${show.lang}"
                                                        data-available="${','.join(languages)}"></select>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Archive on first match</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="archive_firstmatch"
                                                   name="archive_firstmatch" ${('', 'checked')[show.archive_firstmatch == 1]} />
                                            <label for="archive_firstmatch">
                                                archive episode after the first best match is found from your archive
                                                quality list
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Subtitles</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="subtitles"
                                                   name="subtitles" ${('', 'checked')[all([show.subtitles,sickrage.srCore.srConfig.USE_SUBTITLES])]}${('disabled="disabled"', '')[bool(sickrage.srCore.srConfig.USE_SUBTITLES)]}/>
                                            <label for="subtitles">
                                                search for subtitles
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Subtitle metdata</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="subtitles_sr_metadata"
                                                   name="subtitles_sr_metadata" ${('', 'checked')[show.subtitles_sr_metadata == 1]} />
                                            <label for="subtitles_sr_metadata">
                                                use SiCKRAGE metadata when searching for subtitle, this will override
                                                the auto-discovered metadata
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Paused</label><br/>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="paused"
                                                   name="paused" ${('', 'checked')[show.paused == 1]} />
                                            <label for="paused">
                                                pause this show (SiCKRAGE will not download episodes)
                                            </label>
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>
                        <div id="core-tab-pane2" class="tab-pane fade">
                            <div class="tab-pane">
                                <div class="tab-pane-desc">
                                    <h3>Format Settings</h3>
                                </div>

                                <fieldset class="tab-pane-list">
                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Air by date</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="airbydate"
                                                   name="air_by_date" ${('', 'checked')[show.air_by_date == 1]} />
                                            <label for="airbydate">
                                                check if the show is released as Show.03.02.2010 rather than Show.S02E03
                                                <pre>In case of an air date conflict between regular and special episodes, the later will be ignored.</pre>
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Sports</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="sports"
                                                   name="sports" ${('', 'checked')[show.sports == 1]}/>
                                            <label for="sports">
                                                check if the show is a sporting or MMA event released as Show.03.02.2010
                                                rather than Show.S02E03
                                                <pre>In case of an air date conflict between regular and special episodes, the later will be ignored.</pre>
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">DVD Order</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="dvdorder"
                                                   name="dvdorder" ${('', 'checked')[show.dvdorder == 1]} />
                                            <label for="dvdorder">
                                                use the DVD order instead of the air order<br>
                                                <pre> A "Force Full Update" is necessary, and if you have existing episodes you need to sort them manually.</pre>
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Anime</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="anime"
                                                   name="anime" ${('', 'checked')[show.is_anime == 1]}>
                                            <label for="anime">
                                                check if the show is Anime and episodes are released as Show.265 rather
                                                than Show.S02E03
                                            </label>
                                            <br/>
                                            % if show.is_anime:
                                                <%include file="../includes/blackwhitelist.mako"/>
                                            % endif
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Season folders</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="season_folders"
                                                   name="flatten_folders" ${('checked', '')[show.flatten_folders == 1 and not sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS)]}/>
                                            <label for="season_folders">
                                                group episodes by season folder (uncheck to store in a single folder)
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Scene Numbering</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="scene"
                                                   name="scene" ${('', 'checked')[show.scene == 1]} />
                                            <label for="scene">
                                                search by scene numbering (uncheck to search by indexer numbering)
                                            </label>
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>

                        <div id="core-tab-pane3" class="tab-pane fade">
                            <div class="tab-pane">
                                <div class="tab-pane-desc">
                                    <h3>Advanced Settings</h3>
                                </div>
                                <fieldset class="tab-pane-list">

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Ignored Words</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="fa fa-file-word-o"></span>
                                                </div>
                                                <input type="text" id="rls_ignore_words" name="rls_ignore_words"
                                                       value="${show.rls_ignore_words}"
                                                       placeholder="ex. word1,word2,word3"
                                                       class="form-control "/>
                                            </div>
                                            <label for="rls_ignore_words">
                                                <p>
                                                    Search results with one or more words from this list will be
                                                    ignored.
                                                </p>
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Required Words</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="fa fa-file-word-o"></span>
                                                </div>
                                                <input type="text" id="rls_require_words" name="rls_require_words"
                                                       placeholder="ex. word1,word2,word3"
                                                       value="${show.rls_require_words}"
                                                       class="form-control "/>
                                            </div>
                                            <label for="rls_require_words">
                                                <p>Search results with no words from this list will be ignored.</p>
                                            </label>
                                        </div>
                                    </div>

                                    <div class="row field-pair">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">Scene Exception</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="input-group input350">
                                                <div class="input-group-addon">
                                                    <span class="glyphicon"></span>
                                                </div>
                                                <input type="text" id="SceneName"
                                                       title="Scene exception name for show"
                                                       class="form-control "/>
                                                <div class="input-group-addon">
                                                    <a href="#" class="glyphicon glyphicon-plus-sign"
                                                       id="addSceneName"></a>
                                                </div>
                                            </div>
                                            <br/>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <div class="input-group input350">
                                                        <select id="exceptions_list" name="exceptions_list"
                                                                class="form-control"
                                                                multiple="multiple"
                                                                style="min-width:200px;height:99px;">
                                                            % for cur_exception in show.exceptions:
                                                                <option value="${cur_exception}">${cur_exception}</option>
                                                            % endfor
                                                        </select>
                                                        <div class="input-group-addon">
                                                            <a href="#" class="glyphicon glyphicon-minus-sign"
                                                               id="removeSceneName"></a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <label for="exceptions_list">
                                                This will affect episode search on NZB and torrent
                                                providers. This list overrides the original name; it doesn't append
                                                to it.
                                            </label>
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input id="submit" type="submit" value="Save Changes"
                                   class="btn pull-left config_submitter button">
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>
