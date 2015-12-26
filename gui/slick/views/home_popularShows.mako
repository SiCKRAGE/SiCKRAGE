<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
    import sickbeard
%>
<%block name="content">
<h2>Popular Shows</h2>
<br>

<% imdb_tt = [show.imdbid for show in sickbeard.showList if show.imdbid] %>
% if not popular_shows:
    <h3>Fetching of IMDB Data failed. Are you online?</h3>

    <strong>Exception:</strong>
    <p>${imdb_exception}</p>

% else:
    % for cur_result in popular_shows:
        <div class="popularShow">
            <div class="left">
                <img class="coverImage" src="${srRoot}/cache/${cur_result[b'image_path']}" />
            </div>
            <div class="right">
                <h3>${cur_result[b'name']}</h3>

                % if 'rating' in cur_result and cur_result[b'rating']:
                    <span class="rating">${cur_result[b'rating']}/10 (${cur_result[b'votes']})</span>
                % endif

                <p>${cur_result[b'outline']}<span class="year"> - Released ${cur_result[b'year']}<span></p>
                <span class="imdb_url"><a href="${anon_url(cur_result[b'imdb_url'])}">View on IMDB</a></span>&nbsp;&nbsp;|&nbsp;&nbsp;
                % if cur_result[b'imdb_tt'] not in imdb_tt:
                <span class="imdb_sickrage_search"><a href="${srRoot}/home/addShows/newShow/?search_string=${cur_result[b'name']}">
                    Add Show</a></span>
                % else:
                <span> Already added </span>
                % endif

            </div>
            <br style="clear:both" />

        </div>
    % endfor
% endif
</%block>
