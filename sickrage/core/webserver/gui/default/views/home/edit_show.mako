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

                <form action="editShow" method="post">
                    <ul class="nav nav-tabs">
                        <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Main</a></li>
                        <li><a data-toggle="tab" href="#core-tab-pane2">Format</a></li>
                        <li><a data-toggle="tab" href="#core-tab-pane3">Advanced</a></li>
                    </ul>

                    <div class="tab-content">
                        <div id="core-tab-pane1" class="tab-pane fade in active">
                            <div class="row">
                                <div class="col-md-12"><h3>Main Settings</h3></div>
                            </div>

                            <fieldset class="tab-pane-list">

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Show Location</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="hidden" name="show" value="${show.indexerid}"/>
                                            <input type="text" name="location" id="location" value="${show.location}"
                                                   class="form-control input-sm input350"
                                                   autocapitalize="off" title="Location" required=""/></label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Preferred Quality</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <%
                                            qualities = Quality.splitQuality(int(show.quality))
                                        %>
                                            <%include file="../includes/quality_chooser.mako"/>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Archive on first match</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label>
                                            <input type="checkbox" id="archive_firstmatch"

                                                   name="archive_firstmatch" ${('', 'checked')[show.archive_firstmatch == 1]} />
                                            archive episode after the first best match is found from your archive
                                            quality list
                                        </label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Default Episode Status</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label>
                                            <select name="defaultEpStatus" id="defaultEpStatusSelect"
                                                    class="form-control input-sm">
                                                % for curStatus in [WANTED, SKIPPED, IGNORED]:
                                                    <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
                                                % endfor
                                            </select>
                                            This will set the status for future
                                            episodes.
                                        </label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Info Language</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <% languages = srIndexerApi().indexer().languages.keys() %>
                                        <label>
                                            <select name="indexerLang" id="indexerLangSelect"
                                                    class="form-control input-sm bfh-languages"
                                                    data-language="${show.lang}"
                                                    data-available="${','.join(languages)}"></select>
                                            This only applies to episode filenames and the contents of metadata
                                            files.
                                        </label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Subtitles</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label>
                                            <input type="checkbox" id="subtitles"

                                                   name="subtitles" ${('', 'checked')[all([show.subtitles,sickrage.srCore.srConfig.USE_SUBTITLES])]}${('disabled="disabled"', '')[bool(sickrage.srCore.srConfig.USE_SUBTITLES)]}/>
                                            search for subtitles
                                        </label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Subtitle metdata</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label>
                                            <input type="checkbox" id="subtitles_sr_metadata"

                                                   name="subtitles_sr_metadata" ${('', 'checked')[show.subtitles_sr_metadata == 1]} />
                                            use SiCKRAGE metadata when searching for subtitle, this will override the
                                            auto-discovered metadata
                                        </label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Paused</span><br/>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label>
                                            <input type="checkbox" id="paused"

                                                   name="paused" ${('', 'checked')[show.paused == 1]} />
                                            pause this show (SiCKRAGE will not download episodes)
                                        </label>
                                    </div>
                                </div>

                            </fieldset>
                        </div>

                        <div id="core-tab-pane2" class="tab-pane fade">
                            <div class="row">
                                <div class="col-md-12"><h3>Format Settings</h3>
                                </div>
                            </div>
                            <fieldset class="tab-pane-list">

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Air by date</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="airbydate"

                                                      name="air_by_date" ${('', 'checked')[show.air_by_date == 1]} />
                                            check if the show is released as Show.03.02.2010 rather than
                                            Show.S02E03.</label>
                                        <br/>
                                        <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Anime</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="anime"

                                                      name="anime" ${('', 'checked')[show.is_anime == 1]}> check if
                                            the show is Anime and episodes are released as Show.265 rather than
                                            Show.S02E03</label>
                                        <br/>
                                        % if show.is_anime:
                                            <%include file="../includes/blackwhitelist.mako"/>
                                        % endif
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Sports</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="sports"

                                                      name="sports" ${('', 'checked')[show.sports == 1]}/> check if
                                            the show is a sporting or MMA event released as Show.03.02.2010 rather than
                                            Show.S02E03</label>
                                        <br/>
                                        <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Season folders</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="season_folders"

                                                      name="flatten_folders" ${('checked', '')[show.flatten_folders == 1 and not sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickrage.srCore.srConfig.NAMING_FORCE_FOLDERS)]}/>
                                            group episodes by season folder (uncheck to store in a single
                                            folder)</label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Scene Numbering</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="scene"

                                                      name="scene" ${('', 'checked')[show.scene == 1]} /> search by
                                            scene numbering (uncheck to search by indexer numbering)</label>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">DVD Order</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <label><input type="checkbox" id="dvdorder"

                                                      name="dvdorder" ${('', 'checked')[show.dvdorder == 1]} /> use
                                            the DVD order instead of the air order<br></label>
                                        <br/>
                                        <span style="color:red">
                                            A "Force Full Update" is necessary, and if you
                                            have
                                            existing episodes you need to sort them manually.
                                        </span>
                                    </div>
                                </div>

                            </fieldset>
                        </div>

                        <div id="core-tab-pane3" class="tab-pane fade">
                            <div class="row">
                                <div class="col-md-12"><h3>Advanced Settings</h3></div>
                            </div>
                            <fieldset class="tab-pane-list">

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Ignored Words</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="rls_ignore_words" name="rls_ignore_words"
                                               id="rls_ignore_words" value="${show.rls_ignore_words}"
                                               class="form-control input-sm input350"/><br>
                                        <div class="clear-left">
                                            <p>comma-separated <i>e.g. "word1,word2,word3"</i>
                                            <p>Search results with one or more words from this list will be
                                                ignored.</p>
                                        </div>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Required Words</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="rls_require_words" name="rls_require_words"
                                               value="${show.rls_require_words}"
                                               class="form-control input-sm input350"/><br>
                                        <div class="clear-left">
                                            <p>comma-separated <i>e.g. "word1,word2,word3"</i></p>
                                            <p>Search results with no words from this list will be ignored.</p>
                                        </div>
                                    </div>
                                </div>

                                <div class="row field-pair">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">Scene Exception</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" id="SceneName"
                                               class="form-control input-sm input200"/><input
                                            class="btn" type="button" value="Add" id="addSceneName"/><br><br>
                                        <div class="pull-left">
                                            <select id="exceptions_list" name="exceptions_list" multiple="multiple"
                                                    style="min-width:200px;height:99px;">
                                                % for cur_exception in show.exceptions:
                                                    <option value="${cur_exception}">${cur_exception}</option>
                                                % endfor
                                            </select>
                                            <div>
                                                <input id="removeSceneName" value="Remove" class="btn float-left"
                                                       type="button"/>
                                            </div>
                                        </div>
                                        <label for="exceptions_list">
                                            This will affect episode search on NZB and
                                            torrent
                                            providers. This list overrides the original name; it doesn't append to
                                            it.
                                        </label>
                                    </div>
                                </div>

                            </fieldset>
                        </div>

                    </div>

                    <br>
                    <div class="row">
                        <div class="col-lg-2 col-md-2 col-sm-2 col-xs-12">
                            <input id="submit" type="submit" value="Save Changes"
                                   class="btn pull-left config_submitter button">
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>
