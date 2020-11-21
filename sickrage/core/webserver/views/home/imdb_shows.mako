<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.helpers import anon_url
%>
<%block name="sub_navbar">
    <div class="row submenu">
        <div class="col text-left">
            <div class="form-inline m-2">
                <select id="showsort" class="form-control form-control-inline m-1" title="${_('Show Sort')}">
                    <option value="name">${_('Name')}</option>
                    <option value="original" selected="selected">${_('Original')}</option>
                    <option value="votes">${_('Votes')}</option>
                    <option value="rating">${_('% Rating')}</option>
                    <option value="rating_votes">${_('% Rating > Votes')}</option>
                </select>
                &nbsp;
                <select id="showsortdirection" class="form-control form-control-inline m-1" title="${_('Show Sort Direction')}">
                    <option value="asc" selected="selected">${_('Asc')}</option>
                    <option value="desc">${_('Desc')}</option>
                </select>
            </div>
        </div>

        <div class="text-right pr-3">
            <div class="form-inline d-inline m-1">
                <div style="width: 100px" id="posterSizeSlider"></div>
            </div>
        </div>
    </div>
</%block>

<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <% imdb_tt = {show.imdb_id for show in get_show_list() if show.imdb_id} %>
                    <div class="show-grid mx-auto">
                        % if not popular_shows:
                            <div class="trakt_show" style="width:100%; margin-top:20px">
                                <p class="red-text">
                                    ${_('Fetching of IMDB Data failed. Are you online?')}
                                    <strong>${_('Exception:')}</strong>
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

                                    <div class="show-container" data-name="${cur_result['name']}"
                                         data-rating="${cur_rating}"
                                         data-votes="${cur_votes.replace(',', '')}">
                                        <div class="card card-block text-white bg-dark m-1 shadow">
                                            <div class="card-header p-0">
                                                <a class="trakt-image" href="${anon_url(cur_result['imdb_url'])}"
                                                   target="_blank">
                                                    <img class="card-img-top"
                                                         src="${srWebRoot}/${cur_result['image_path']}"/>
                                                </a>
                                            </div>
                                            <div class="card-body text-truncate py-1 px-1 small">
                                                <div class="show-title">
                                                    ${(cur_result['name'], '<span>&nbsp;</span>')['' == cur_result['name']]}
                                                </div>
                                                <div class="show-votes">
                                                    ${cur_votes} <i class="fas fa-thumbs-up text-success"></i>
                                                </div>
                                                <div class="show-ratings">
                                                    ${int(float(cur_rating)*10)}% <i class="fas fa-heart text-danger"></i>
                                                </div>
                                            </div>
                                            <div class="card-footer show-details p-1">
                                                <a href="${srWebRoot}/home/addShows/addShowByID/?series_id=${cur_result['imdb_tt']}&showName=${cur_result['name']}"
                                                   class="btn btn-sm" data-no-redirect>${_('Add Show')}</a>
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
    </div>
</%block>
