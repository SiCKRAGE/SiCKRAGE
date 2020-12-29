<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.subtitles import Subtitles
    from sickrage.core.helpers import anon_url
    from sickrage.core.enums import SeriesProviderID
%>

<%block name="metas">
    <meta data-var="sickrage.DEFAULT_LANGUAGE" data-content="${sickrage.app.config.general.series_provider_default_language}">
    <meta data-var="sickrage.LANGUAGES"
          data-content="${','.join([lang['abbreviation'] for lang in sickrage.app.series_providers[SeriesProviderID.THETVDB].languages()])}">
</%block>

<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="sickrage-stepper mb-3">
                <div class="stepwizard">
                    <div class="stepwizard-row setup-panel form-inline">
                        <div class="stepwizard-step col-auto">
                            <a href="#step-1" class="btn btn-success btn-circle">1</a>
                            <p>
                                <small class="text-white">${_('Find A Show')}</small>
                            </p>
                        </div>
                        <div class="stepwizard-step col-auto">
                            <a href="#step-2" class="btn btn-dark btn-circle disabled">2</a>
                            <p>
                                <small class="text-white">${_('Pick A Folder')}</small>
                            </p>
                        </div>
                        <div class="stepwizard-step col-auto">
                            <a href="#step-3" class="btn btn-dark btn-circle disabled">3</a>
                            <p>
                                <small class="text-white">${_('Custom Options')}</small>
                            </p>
                        </div>
                    </div>
                </div>

                <form class="needs-validation" id="addShowForm" method="post"
                      action="${srWebRoot}/home/addShows/addNewShow" novalidate>

                    % if use_provided_info:
                        <input type="hidden" id="seriesProviderLanguage" name="seriesProviderLanguage"
                               value="${sickrage.app.config.general.series_provider_default_language}"/>
                        <input type="hidden" id="whichSeries" name="whichSeries"
                               value="${provided_series_id}"/>
                        <input type="hidden" id="providedSeriesProviderID" name="providedSeriesProviderID"
                               value="${provided_series_provider_id.name}"/>
                        <input type="hidden" id="providedSeriesName" name="providedSeriesName"
                               value="${provided_series_name}"/>
                    % endif

                    % if provided_show_dir:
                        <input type="hidden" id="fullShowPath" name="fullShowPath"
                               value="${provided_show_dir}"/><br>
                    % endif

                    % for curNextDir in other_shows:
                        <input type="hidden" name="other_shows" value="${curNextDir}"/>
                    % endfor

                    <input type="hidden" name="skipShow" id="skipShow" value=""/>

                    % if not use_provided_info:
                        <div class="card setup-content active" id="step-1">
                            <div class="card-header">
                                <h3 class="card-title">${_('Find a show')}</h3>
                            </div>
                            <div class="card-body">
                                <div class="form-group">
                                    <input type="hidden" id="series_provider_timeout"
                                           value="${sickrage.app.config.general.series_provider_timeout}"/>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-tv"></span>
                                                    </span>
                                                </div>
                                                <input id="nameToSearch" value="${default_show_name}"
                                                       title="TV show name" class="form-control" required/>
                                                <select name="providedSeriesProviderID" id="providedSeriesProviderID"
                                                        class="form-control" title="Choose series provider">
                                                    % for item in SeriesProviderID:
                                                        <option value="${item.name}" ${('', 'selected')[provided_series_provider_id == item]}>${item.display_name}</option>
                                                    % endfor
                                                </select>
                                                <div class="invalid-feedback">
                                                    ${_('Please choose a show')}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <br/>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <div class="input-group">
                                                <div class="input-group-prepend">
                                                    <span class="input-group-text">
                                                        <span class="fas fa-flag"></span>
                                                    </span>
                                                </div>
                                                <select name="seriesProviderLanguage" id="seriesProviderLanguage" class="form-control"
                                                        title="${_('Choose language')}">
                                                    % for language in sickrage.app.series_providers[SeriesProviderID.THETVDB].languages():
                                                        <option value="${language['abbreviation']}" ${('', 'selected')[sickrage.app.config.general.series_provider_default_language == language['abbreviation']]}>
                                                            ${language['englishname']}
                                                        </option>
                                                    % endfor
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                    <p>
                                    <div id="step-1-messages"></div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <button class="btn btn-success btn-inline ${('', 'disabled')[use_provided_info]}"
                                        type="button" id="searchName">
                                    ${_('Search')}
                                </button>
                                <button class="btn btn-primary nextBtn ${('', 'disabled')[not use_provided_info]} pull-right"
                                        type="button">
                                    ${_('Next')}
                                </button>
                                % if provided_show_dir:
                                    <input class="btn float-right" type="button" id="skipShowButton"
                                           value="${_('Skip Show')}"/>
                                % endif
                            </div>
                        </div>
                    % endif

                    <div class="card setup-content" id="step-2">
                        <div class="card-header">
                            <h3 class="card-title">${_('Pick a folder')}</h3>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                % if not provided_show_dir:
                                    <%include file="../includes/root_dirs.mako"/>
                                % else:
                                ${_('Pre-chosen Destination Folder:')}
                                    <b>${provided_show_dir}</b><br/>
                                % endif
                                <p>
                                <div id="step-2-messages"></div>
                                </p>
                            </div>
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-primary nextBtn pull-right" type="button">
                                ${_('Next')}
                            </button>
                        </div>
                    </div>

                    <div class="card setup-content" id="step-3">
                        <div class="card-header">
                            <h3 class="card-title">${_('Custom options for show: ')} ${default_show_name}</h3>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                    <%include file="../includes/add_show_options.mako"/>
                            </div>
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-success pull-right" type="submit">
                                ${_('Finish!')}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>
