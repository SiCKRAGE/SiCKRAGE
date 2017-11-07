<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.indexers import srIndexerApi
%>

<%block name="metas">
    <meta data-var="sickrage.DEFAULT_LANGUAGE" data-content="${sickrage.app.srConfig.INDEXER_DEFAULT_LANGUAGE}">
    <meta data-var="sickrage.LANGUAGES" data-content="${','.join(srIndexerApi().indexer().languages.keys())}">
</%block>

<%block name="content">
    <div id="newShowPortal">
        <div class="row">
            <div class="col-md-12">
                <h1 class="title">${title}</h1>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <form id="addShowForm" class="form-inline" method="post" action="${srWebRoot}/home/addShows/addNewShow">
                    <h1>${_('Find a show')}</h1>
                    <section data-step="0">
                        <div class="form-group">
                            <input type="hidden" id="indexer_timeout"
                                   value="${sickrage.app.srConfig.INDEXER_TIMEOUT}"/>
                            % if use_provided_info:
                            ${_('Show retrieved from existing metadata:')}
                                <a href="${anon_url(srIndexerApi(provided_indexer).config['show_url'], provided_indexer_id)}">
                                    ${provided_indexer_name}
                                </a>
                                <input type="hidden" id="indexerLang" name="indexerLang"
                                       value="${sickrage.app.srConfig.INDEXER_DEFAULT_LANGUAGE}"/>
                                <input type="hidden" id="whichSeries" name="whichSeries"
                                       value="${provided_indexer_id}"/>
                                <input type="hidden" id="providedIndexer" name="providedIndexer"
                                       value="${provided_indexer}"/>
                                <input type="hidden" id="providedName" value="${provided_indexer_name}"/>
                            % else:
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="input-group input350">
                                            <div class="input-group-addon">
                                                <span class="fa fa-tv"></span>
                                            </div>
                                            <input id="nameToSearch" value="${default_show_name}"
                                                   title="TV show name" class="form-control"/>
                                            <span class="input-group-addon"
                                                  style="width:0; padding-left:0; padding-right:0; border:none;"></span>
                                            <select name="providedIndexer" id="providedIndexer"
                                                    class="form-control" title="Choose indexer">
                                                % for indexer in indexers:
                                                    <option value="${indexer}" ${('', 'selected')[provided_indexer == indexer]}>
                                                        ${indexers[indexer]}
                                                    </option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <br/>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="input-group input350">
                                            <div class="input-group-addon">
                                                <span class="glyphicon glyphicon-flag"></span>
                                            </div>
                                            <select name="indexerLang" id="indexerLang" class="form-control"
                                                    title="${_('Choose language')}">
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <p>
                                <div id="messages"></div>
                                <br/>
                                <input class="btn btn-success btn-inline" type="button" id="searchName"
                                       value="${_('Search')}"/>
                            % endif
                        </div>
                    </section>

                    <h1>${_('Pick a folder')}</h1>
                    <section data-step="1">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    % if provided_show_dir:
                                    ${_('Pre-chosen Destination Folder:')} <b>${provided_show_dir}</b><br/>
                                        <input type="hidden" id="fullShowPath" name="fullShowPath"
                                               value="${provided_show_dir}"/><br>
                                    % else:
                                        <%include file="../includes/root_dirs.mako"/>
                                    % endif
                                </div>
                            </div>
                        </div>
                    </section>

                    <h1>${_('Custom options')}</h1>
                    <section data-step="2">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                        <%include file="../includes/add_show_options.mako"/>
                                </div>
                            </div>
                        </div>
                    </section>

                    % for curNextDir in other_shows:
                        <input type="hidden" name="other_shows" value="${curNextDir}"/>
                    % endfor
                    <input type="hidden" name="skipShow" id="skipShow" value=""/>
                </form>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div style="width: 100%; text-align: center;">
                    % if provided_show_dir:
                        <input class="btn" type="button" id="skipShowButton" value="${_('Skip Show')}"/>
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>
