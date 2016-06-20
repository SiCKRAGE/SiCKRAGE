<%inherit file="../layouts/main.mako"/>
<%!
    import datetime

    import sickrage
    from sickrage.core.searchers import subtitle_searcher
%>
<%block name="content">
<div id="content960">


% if whichSubs:
    <% subsLanguage = subtitle_searcher.fromietf(whichSubs).name if not whichSubs == 'all' else 'All' %>
% endif
% if not whichSubs or (whichSubs and not ep_counts):

% if whichSubs:
<h2>All of your episodes have ${subsLanguage} subtitles.</h2>
<br>
% endif

<form action="/manage/subtitleMissed" method="get">
Manage episodes without <select name="whichSubs" class="form-control form-control-inline input-sm">
<option value="all">All</option>
    <% sub_langs = [subtitle_searcher.fromietf(x) for x in subtitle_searcher.wantedLanguages()] %>
% for sub_lang in sub_langs:
<option value="${sub_lang.opensubtitles}">${sub_lang.name}</option>
% endfor
</select>
subtitles
<input class="btn" type="submit" value="Manage" />
</form>

% else:
<input type="hidden" id="selectSubLang" name="selectSubLang" value="${whichSubs}" />

<form action="/manage/downloadSubtitleMissed" method="post">
<h2>Episodes without ${subsLanguage} subtitles.</h2>
<br>
Download missed subtitles for selected episodes <input class="btn btn-inline" type="submit" value="Go" />
<div>
    <button type="button" class="btn btn-xs selectAllShows"><a>Select all</a></button>
    <button type="button" class="btn btn-xs unselectAllShows"><a>Clear all</a></button>
</div>
<br>
    <table class="sickrageTable manageTable" cellspacing="1" border="0" cellpadding="0">
% for cur_indexer_id in sorted_show_ids:
 <tr id="${cur_indexer_id}">
  <th><input type="checkbox" class="allCheck" id="allCheck-${cur_indexer_id}" name="${cur_indexer_id}-all"checked="checked" /></th>
  <th colspan="3" style="width: 100%; text-align: left;"><a class="whitelink" href="/home/displayShow?show=${cur_indexer_id}">${show_names[cur_indexer_id]}</a> (${ep_counts[cur_indexer_id]}) <input type="button" class="pull-right get_more_eps btn" id="${cur_indexer_id}" value="Expand" /></th>
 </tr>
% endfor
</table>
</form>

% endif
</div>
</%block>
