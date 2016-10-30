<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
    from sickrage.indexers import srIndexerApi
%>

<%block name="metas">
    <meta data-var="sickrage.DEFAULT_LANGUAGE" data-content="${sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE}">
    <meta data-var="sickrage.LANGUAGES" data-content="${','.join(srIndexerApi().indexer().languages.keys())}">
</%block>

<%block name="content">

    <div id="newShowPortal">
        <form id="addShowForm" class="form-inline" method="post" action="/home/addShows/addNewShow">
            <h1>Find a show</h1>
            <section data-step="0">
                <div class="form-group">
                    <input type="hidden" id="indexer_timeout" value="${sickrage.srCore.srConfig.INDEXER_TIMEOUT}"/>

                    % if use_provided_info:
                        Show retrieved from existing metadata:
                        <a href="${anon_url(srIndexerApi(provided_indexer).config['show_url'], provided_indexer_id)}">
                            ${provided_indexer_name}
                        </a>
                        <input type="hidden" id="indexerLang" name="indexerLang"
                               value="${sickrage.srCore.srConfig.INDEXER_DEFAULT_LANGUAGE}"/>
                        <input type="hidden" id="whichSeries" name="whichSeries"
                               value="${provided_indexer_id}"/>
                        <input type="hidden" id="providedIndexer" name="providedIndexer"
                               value="${provided_indexer}"/>
                        <input type="hidden" id="providedName" value="${provided_indexer_name}"/>
                    % else:
                        <label for="nameToSearch">
                            <input type="text" id="nameToSearch" value="${default_show_name}"
                                   class="form-control form-control-inline input-sm input350 pull-left"/>
                        </label>
                        <label for="providedIndexer">
                            <select name="providedIndexer" id="providedIndexer"
                                    class="form-control form-control-inline input-sm pull-right">
                                % for indexer in indexers:
                                    <option value="${indexer}" ${('', 'selected="selected"')[provided_indexer == indexer]}>
                                        ${indexers[indexer]}
                                    </option>
                                % endfor
                            </select>
                        </label>
                        <br/>
                        <label for="indexerLang">
                            <select name="indexerLang" id="indexerLang"
                                    class="form-control form-control-inline input-sm">
                            </select>
                        </label>
                        <p>
                        <div id="messages"></div>
                        <br/>
                        <input class="btn btn-success btn-inline" type="button" id="searchName" value="Search"/>
                    % endif
                </div>
            </section>

            <h1>Pick a folder</h1>
            <section data-step="1">
                <div class="form-group">
                    % if provided_show_dir:
                        Pre-chosen Destination Folder: <b>${provided_show_dir}</b> <br>
                        <input type="hidden" id="fullShowPath" name="fullShowPath"
                               value="${provided_show_dir}"/><br>
                    % else:
                        <%include file="../includes/root_dirs.mako"/>
                    % endif
                </div>
            </section>

            <h1>Custom options</h1>
            <section data-step="2">
                <div class="form-group">
                        <%include file="../includes/add_show_options.mako"/>
                </div>
            </section>

            % for curNextDir in other_shows:
                <input type="hidden" name="other_shows" value="${curNextDir}"/>
            % endfor
            <input type="hidden" name="skipShow" id="skipShow" value=""/>
        </form>
        <br/>
        <div style="width: 100%; text-align: center;">
            % if provided_show_dir:
                <input class="btn" type="button" id="skipShowButton" value="Skip Show"/>
            % endif
        </div>
    </div>
</%block>
