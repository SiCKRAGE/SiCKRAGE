<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.helpers import anon_url
%>
<%block name="content">
    <h2>Popular Shows</h2>
    <br>
    <% imdb_tt = [show.imdbid for show in sickrage.srCore.SHOWLIST if show.imdbid] %>
    % if not popular_shows:
        <h3>Fetching of IMDB Data failed. Are you online?</h3>
    % else:
        <table id="popularShows" class="tablesorter" cellspacing="1" border="0" cellpadding="1">
            <thead>
            <tr>
                <th>Show</th>
                <th>Rating</th>
                <th>Votes</th>
                <th>Released</th>
            </tr>
            </thead>
            <tbody>
                % for cur_result in popular_shows:
                    <tr>
                        <td class="popularShow">
                            <div class="left">
                                <img class="coverImage" src="/cache/${cur_result['image_path']}"/>
                            </div>
                            <div class="right">
                                <h3>${cur_result['name']}</h3>
                                <p>
                                    ${cur_result['outline']}
                                </p>
                                <span class="imdb_url">
                                    <a href="${anon_url(cur_result['imdb_url'])}">View on IMDB</a>
                                </span>&nbsp;&nbsp;|&nbsp;&nbsp;
                                % if cur_result['imdb_tt'] not in imdb_tt:
                                    <span class="imdb_sickrage_search">
                                        <a href="/home/addShows/newShow/?search_string=${cur_result['name']}">Add
                                            Show</a>
                                    </span>
                                % else:
                                    <span> Already added </span>
                                % endif
                            </div>
                            <br style="clear:both"/>
                        </td>
                        <td align="center">
                            % if cur_result.get('rating'):
                                <span class="rating">
                                    ${cur_result['rating']}/10
                                </span>
                            % endif
                        </td>
                        <td align="center">
                            % if cur_result.get('votes'):
                                ${cur_result['votes'].replace('votes', '')}
                            % endif
                        </td>
                        <td align="center">
                            ${cur_result['year']}
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
    % endif
</%block>
