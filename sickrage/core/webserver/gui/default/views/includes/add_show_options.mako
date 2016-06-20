    <%
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
    from sickrage.core.searchers import subtitle_searcher
%>
% if sickrage.srCore.srConfig.USE_SUBTITLES:
    <br>
    <div class="field-pair">
        <label for="subtitles" class="clearfix">
            <span class="component-desc">
                 <input type="checkbox" name="subtitles"
                        id="subtitles" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SUBTITLES_DEFAULT)]} />
            </span>
            <span class="component-title">Subtitles</span>
        </label>
    </div>
% endif
<div class="field-pair alt">
    <label for="flatten_folders" class="clearfix">
        <span class="component-desc">
            <input class="cb" type="checkbox" name="flatten_folders"
                   id="flatten_folders" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT)]}/>
        </span>
        <span class="component-title">Flatten Folders</span>
    </label>
</div>
% if enable_anime_options:
    <div class="field-pair alt">
        <label for="anime" class="clearfix">
            <span class="component-desc">
                <input type="checkbox" name="anime"
                       id="anime" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.ANIME_DEFAULT)]} />
            </span>
            <span class="component-title">Anime</span>
        </label>
    </div>
% endif
<div class="field-pair alt">
    <label for="scene" class="clearfix">
        <span class="component-desc">
            <input type="checkbox" name="scene"
                   id="scene" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.SCENE_DEFAULT)]} />
        </span>
        <span class="component-title">Scene Numbering</span>
    </label>
</div>
<div class="field-pair alt">
    <label for="archive" class="clearfix">
        <span class="component-desc">
            <input type="checkbox" name="archive"
                   id="archive" ${('', 'checked="checked"')[bool(sickrage.srCore.srConfig.ARCHIVE_DEFAULT)]} />
        </span>
        <span class="component-title">Archive on first match</span>
    </label>
</div>
<div class="field-pair">
    <label for="statusSelect">
        <span class="component-desc">
            <select name="defaultStatus" id="statusSelect" class="form-control form-control-inline input-sm">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.STATUS_DEFAULT == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </span>
        <span class="component-title">Status for previously aired episodes</span>
    </label>
</div>
<div class="field-pair">
    <label for="statusSelectAfter">
        <span class="component-desc">
            <select name="defaultStatusAfter" id="statusSelectAfter"
                    class="form-control form-control-inline input-sm">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.STATUS_DEFAULT_AFTER == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </span>
        <span class="component-title">Status for all future episodes</span>
    </label>
</div>

<% qualities = Quality.splitQuality(sickrage.srCore.srConfig.QUALITY_DEFAULT) %>
<% anyQualities = qualities[0] %>
<% bestQualities = qualities[1] %>

<%include file="quality_chooser.mako"/>

<br/>
<div class="field-pair alt">
    <label for="saveDefaultsButton" class="nocheck clearfix">
        <span class="component-title">
            <input class="btn btn-inline" type="button" id="saveDefaultsButton" value="Save As Defaults"
                   disabled="disabled"/>
        </span>
    </label>
</div><br>

% if enable_anime_options:
    <% import sickrage.core.blackandwhitelist %>
    <%include file="blackwhitelist.mako"/>
% else:
    <input type="hidden" name="anime" id="anime" value="0"/>
% endif
