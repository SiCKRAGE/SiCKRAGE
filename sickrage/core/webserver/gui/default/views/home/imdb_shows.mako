<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
%>
<%block name="content">
    <div class="col-md-12">
        <div class="row">
            <div class="col-lg-8 col-md-7 col-sm-7 col-xs-12 pull-right">
                <div class="pull-right">
                    <label>
                        <span>Sort By:</span>
                        <select id="showsort" class="form-control form-control-inline input-sm" title="Show Sort">
                            <option value="name">Name</option>
                            <option value="original" selected="selected">Original</option>
                            <option value="votes">Votes</option>
                            <option value="rating">% Rating</option>
                            <option value="rating_votes">% Rating > Votes</option>
                        </select>
                        &nbsp;
                    </label>
                    <label>
                        <span>Sort Order:</span>
                        <select id="showsortdirection" class="form-control form-control-inline input-sm"
                                title="Show Sort Direction">
                            <option value="asc" selected="selected">Asc</option>
                            <option value="desc">Desc</option>
                        </select>
                    </label>
                </div>
            </div>
            <div class="col-lg-4 col-md-5 col-sm-5 col-xs-12">
                <h1 class="title">${title}</h1>
            </div>
        </div>
        <div class="row">
            <% imdb_tt = {show.imdbid for show in sickrage.srCore.SHOWLIST if show.imdbid} %>
            <div id="popularShows">
                <div id="container">
                    % if not popular_shows:
                        <div class="trakt_show" style="width:100%; margin-top:20px">
                            <p class="red-text">Fetching of IMDB Data failed. Are you online?
                                <strong>Exception:</strong>
                            <p>${imdb_exception}</p>
                        </div>
                    % else:
                        % for cur_result in popular_shows:
                            % if not cur_result['imdb_tt'] in imdb_tt:
                                % if 'rating' in cur_result and cur_result['rating']:
                                    <% cur_rating = cur_result['rating'] %>
                                    <% cur_votes = cur_result['votes'] %>
                                % else:
                                    <% cur_rating = '0' %>
                                    <% cur_votes = '0' %>
                                % endif

                                <div class="trakt_show" data-name="${cur_result['name']}" data-rating="${cur_rating}"
                                     data-votes="${cur_votes.replace(',', '')}">
                                    <div class="traktContainer">
                                        <div class="trakt-image">
                                            <a class="trakt-image" href="${anon_url(cur_result['imdb_url'])}"
                                               target="_blank">
                                                <img alt="" class="trakt-image"
                                                     src="${srWebRoot}/${cur_result['image_path']}"
                                                     height="273px" width="186px"/>
                                            </a>
                                        </div>

                                        <div class="show-title">
                                            ${(cur_result['name'], '<span>&nbsp;</span>')['' == cur_result['name']]}
                                        </div>

                                        <div class="clearfix">
                                            <p>
                                                ${int(float(cur_rating)*10)}%
                                                <span class="fa fa-heart red-text"></span>
                                            </p>
                                            <i>${cur_votes}</i>
                                            <div class="traktShowTitleIcons">
                                                <a href="${srWebRoot}/home/addShows/newShow/?search_string=${cur_result['name']}"
                                                   class="btn btn-xs" data-no-redirect>Add Show</a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            % endif
                        % endfor
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>
