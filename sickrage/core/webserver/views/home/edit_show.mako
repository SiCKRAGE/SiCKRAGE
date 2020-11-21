<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    import adba
    from sickrage.core.common import Quality, EpisodeStatus
    from sickrage.core.enums import SearchFormat
%>

<%block name="metas">
    <meta data-var="show.is_anime" data-content="${show.is_anime}">
</%block>

<%block name="content">
    <%namespace file="../includes/quality_chooser.mako" import="QualityChooser"/>
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <form action="editShow" method="post">
                <div class="card">
                    <div class="card-header">
                        <h3 class="title float-md-left">${title}</h3>
                        <ul class="nav nav-pills card-header-pills float-md-right">
                            <li class="nav-item px-1">
                                <a class="nav-link active" data-toggle="tab"
                                   href="#main">${_('Main')}</a>
                            </li>
                            <li class="nav-item px-1">
                                <a class="nav-link" data-toggle="tab"
                                   href="#format">${_('Format')}</a>
                            </li>
                            <li class="nav-item px-1">
                                <a class="nav-link" data-toggle="tab"
                                   href="#advanced">${_('Advanced')}</a>
                            </li>
                        </ul>
                    </div>

                    <div class="card-body tab-content">
                        <div id="main" class="tab-pane active">
                            <div class="form-row">
                                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                                    <h3>${_('Main Settings')}</h3>
                                </div>

                                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Show Location')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <input type="hidden" name="show" value="${show.series_id}"/>
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text"><span
                                                            class="fas fa-folder-open"></span></span>
                                                </div>
                                                <input type="text" name="location" id="location"
                                                       value="${show.location}"
                                                       class="form-control "
                                                       autocapitalize="off" title="Location" required=""/>
                                            </div>
                                            <label class="text-info" for="location">
                                                ${_('Location for where your show resides on your device')}
                                            </label>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Preferred Quality')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            ${QualityChooser(*Quality.split_quality(int(show.quality)))}
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Default Episode Status')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-list"></span>
                                                    </span>
                                                </div>
                                                <select name="defaultEpStatus" id="defaultEpStatusSelect"
                                                        title="This will set the status for future episodes."
                                                        class="form-control">
                                                    % for item in [EpisodeStatus.WANTED, EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED]:
                                                        <option value="${item.name}" ${('', 'selected')[item == show.default_ep_status]}>${item.display_name}</option>
                                                    % endfor
                                                </select>
                                            </div>
                                            <label class="text-info" for="defaultEpStatusSelect">
                                                ${_('Unaired episodes automatically set to this status when air date reached')}
                                            </label>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Info Language')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text"><span
                                                            class="fas fa-language"></span></span>
                                                </div>
                                                <select name="seriesProviderLanguage" id="seriesProviderLangSelect" class="form-control"
                                                        title="${_('Choose language')}">
                                                    % for language in show.series_provider.languages():
                                                        <option value="${language['abbreviation']}" ${('', 'selected')[sickrage.app.config.general.series_provider_default_language == language['abbreviation']]}>
                                                            ${language['englishname']}
                                                        </option>
                                                    % endfor
                                                </select>
                                            </div>
                                            <label class="text-info" for="seriesProviderLangSelect">
                                                ${_('Language to translate show information into')}
                                            </label>
                                        </div>
                                    </div>

                                    <br/>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Scene Numbering')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label for="scene">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="scene"
                                                       name="scene" ${('', 'checked')[bool(show.scene)]} />
                                                ${_('use scene numbering instead of series provider numbering')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Skip downloaded')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label for="skip_downloaded">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="skip_downloaded"
                                                       name="skip_downloaded" ${('', 'checked')[show.skip_downloaded == 1]} />
                                                ${_('skips updating quality of old/new downloaded episodes')}
                                            </label>
                                        </div>
                                    </div>

                                    % if sickrage.app.config.subtitles.enable:
                                        <div class="form-row form-group">
                                            <div class="col-lg-3 col-md-4 col-sm-5">
                                                <label class="component-title">${_('Subtitles')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                                <label for="subtitles">
                                                    <input type="checkbox" class="toggle color-primary is-material"
                                                           id="subtitles"
                                                           name="subtitles" ${('', 'checked')[all([show.subtitles,sickrage.app.config.subtitles.enable])]}${('disabled="disabled"', '')[bool(sickrage.app.config.subtitles.enable)]}/>
                                                    ${_('search for subtitles')}
                                                </label>
                                            </div>
                                        </div>

                                        <div class="form-row form-group">
                                            <div class="col-lg-3 col-md-4 col-sm-5">
                                                <label class="component-title">${_('Subtitle Metdata')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                                <label for="sub_use_sr_metadata">
                                                    <input type="checkbox" class="toggle color-primary is-material"
                                                           id="sub_use_sr_metadata"
                                                           name="sub_use_sr_metadata" ${('', 'checked')[show.sub_use_sr_metadata == 1]} />
                                                    ${_('use SiCKRAGE metadata when searching for subtitle, this will '
                                                    'override the auto-discovered metadata')}
                                                </label>
                                            </div>
                                        </div>
                                    % endif

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Paused')}</label><br/>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label for="paused">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="paused"
                                                       name="paused" ${('', 'checked')[show.paused == 1]} />
                                                ${_('pause this show (SiCKRAGE will not download episodes)')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Anime')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label for="anime">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="anime" name="anime" ${('', 'checked')[show.is_anime == 1]}>
                                                ${_('check if the show is Anime')}
                                            </label>
                                            <br/>
                                            % if show.is_anime:
                                                <%include file="../includes/blackwhitelist.mako"/>
                                            % endif
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>

                        <div id="format" class="tab-pane">
                            <div class="form-row">
                                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                                    <h3>${_('Format Settings')}</h3>
                                </div>

                                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Search Format')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-list"></span>
                                                    </span>
                                                </div>
                                                <select id="search_format" name="search_format"
                                                        class="form-control">
                                                    % for item in SearchFormat:
                                                        <option value="${item.name}" ${('', 'selected')[show.search_format == item]}>${item.display_name}</option>
                                                    % endfor
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('DVD Order')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label class="mb-0" for="dvd_order">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="dvd_order"
                                                       name="dvd_order" ${('', 'checked')[show.dvd_order == 1]} />
                                                ${_('use the DVD order instead of the air order')}
                                            </label>
                                            <div class="text-info">
                                                ${_('A "Force Full Update" is necessary, and if you have existing '
                                                'episodes you need to sort them manually.')}
                                            </div>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Season folders')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <label for="season_folders">
                                                <input type="checkbox" class="toggle color-primary is-material"
                                                       id="season_folders"
                                                       name="flatten_folders" ${('', 'checked')[bool(not show.flatten_folders or sickrage.app.naming_force_folders)]} ${('', 'disabled="disabled"')[bool(sickrage.app.naming_force_folders)]}/>
                                                ${_('group episodes by season folder (uncheck to store in a single folder)')}
                                            </label>
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>

                        <div id="advanced" class="tab-pane">
                            <div class="form-row">
                                <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                                    <h3>${_('Advanced Settings')}</h3>
                                </div>
                                <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Ignored Words')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-file-word-o"></span>
                                                    </span>
                                                </div>
                                                <input type="text" id="rls_ignore_words" name="rls_ignore_words"
                                                       value="${show.rls_ignore_words}"
                                                       placeholder="${_('ex. word1,word2,word3')}"
                                                       class="form-control "/>
                                            </div>
                                            <label class="text-info" for="rls_ignore_words">
                                                ${_('Search results with one or more words from this list will be ignored.')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Required Words')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-file-word-o"></span>
                                                    </span>
                                                </div>
                                                <input type="text" id="rls_require_words" name="rls_require_words"
                                                       placeholder="${_('ex. word1,word2,word3')}"
                                                       value="${show.rls_require_words}"
                                                       class="form-control "/>
                                            </div>
                                            <label class="text-info" for="rls_require_words">
                                                ${_('Search results with no words from this list will be ignored.')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Scene Exception')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <input type="text" id="SceneName"
                                                       title="Scene exception name for show"
                                                       class="form-control "/>
                                                <div class="input-group-append">
                                                    <span class="input-group-text">
                                                        <a href="#" class="fas fa-plus" id="addSceneName"></a>
                                                    </span>
                                                </div>
                                            </div>
                                            <br/>
                                            <div class="form-row">
                                                <div class="col-md-12">
                                                    <div class="input-group">
                                                        <select id="exceptions_list" name="exceptions_list"
                                                                class="form-control"
                                                                multiple="multiple"
                                                                style="min-width:200px;height:99px;">
                                                            % for cur_exception in scene_exceptions:
                                                                <option value="${cur_exception}">${cur_exception}</option>
                                                            % endfor
                                                        </select>
                                                        <div class="input-group-append">
                                                            <span class="input-group-text">
                                                                <a href="#" class="fas fa-minus"
                                                                   id="removeSceneName"></a>
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <label class="text-info" for="exceptions_list">
                                                ${_('This will affect episode search on NZB and torrent providers. '
                                                'This list overrides the original name it doesn\'t append to it.')}
                                            </label>
                                        </div>
                                    </div>

                                    <div class="form-row form-group">
                                        <div class="col-lg-3 col-md-4 col-sm-5">
                                            <label class="component-title">${_('Search Delay')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-clock"></span>
                                                    </span>
                                                </div>
                                                <input type="text" id="search_delay" name="search_delay"
                                                       placeholder="${_('ex. 1')}"
                                                       value="${show.search_delay}"
                                                       class="form-control "/>
                                            </div>
                                            <label class="text-info" for="search_delay">
                                                ${_('Delays searching for new episodes by X number of days.')}
                                            </label>
                                        </div>
                                    </div>
                                </fieldset>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <input id="submit" type="submit" value="${_('Save Changes')}"
                               class="btn config_submitter">
                        <input id="cancel" type="submit" value="${_('Cancel')}"
                               class="btn">
                    </div>
                </div>
            </form>
        </div>
    </div>
</%block>
