<%
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
    from sickrage.core.searchers import subtitle_searcher
%>
% if sickrage.USE_SUBTITLES:
        <br><div class="field-pair">
            <label for="subtitles" class="clearfix">
                <span class="component-title">Subtitles</span>
                <span class="component-desc">
                     <input type="checkbox" name="subtitles"
                            id="subtitles" ${('', 'checked="checked"')[bool(sickrage.SUBTITLES_DEFAULT)]} />
                    <p>Download subtitles for this show?</p>
                </span>
            </label>
        </div>
        % endif

        <div class="field-pair">
            <label for="statusSelect">
                <span class="component-title">Status for previously aired episodes</span>
                <span class="component-desc">
                    <select name="defaultStatus" id="statusSelect" class="form-control form-control-inline input-sm">
                    % for curStatus in [SKIPPED, WANTED, IGNORED]:
                        <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.STATUS_DEFAULT == curStatus]}>${statusStrings[curStatus]}</option>
                    % endfor
                    </select>
                </span>
            </label>
        </div>
        <div class="field-pair">
            <label for="statusSelectAfter">
                <span class="component-title">Status for all future episodes</span>
                <span class="component-desc">
                    <select name="defaultStatusAfter" id="statusSelectAfter" class="form-control form-control-inline input-sm">
                    % for curStatus in [SKIPPED, WANTED, IGNORED]:
                        <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.STATUS_DEFAULT_AFTER == curStatus]}>${statusStrings[curStatus]}</option>
                    % endfor
                    </select>
                </span>
            </label>
        </div>
        <div class="field-pair alt">
            <label for="flatten_folders" class="clearfix">
                <span class="component-title">Flatten Folders</span>
                <span class="component-desc">
                    <input class="cb" type="checkbox" name="flatten_folders"
                           id="flatten_folders" ${('', 'checked="checked"')[bool(sickrage.FLATTEN_FOLDERS_DEFAULT)]}/>
                    <p>Disregard sub-folders?</p>
                </span>
            </label>
        </div>

% if enable_anime_options:
        <div class="field-pair alt">
            <label for="anime" class="clearfix">
                <span class="component-title">Anime</span>
                <span class="component-desc">
                    <input type="checkbox" name="anime"
                           id="anime" ${('', 'checked="checked"')[bool(sickrage.ANIME_DEFAULT)]} />
                    <p>Is this show an Anime?<p>
                </span>
            </label>
        </div>
% endif

        <div class="field-pair alt">
            <label for="scene" class="clearfix">
                <span class="component-title">Scene Numbering</span>
                <span class="component-desc">
                    <input type="checkbox" name="scene"
                           id="scene" ${('', 'checked="checked"')[bool(sickrage.SCENE_DEFAULT)]} />
                    <p>Is this show scene numbered?</p>
                </span>
            </label>
        </div>

        <div class="field-pair alt">
            <label for="archive" class="clearfix">
                <span class="component-title">Archive first match</span>
                <span class="component-desc">
                    <input type="checkbox" name="archive"
                           id="archive" ${('', 'checked="checked"')[bool(sickrage.ARCHIVE_DEFAULT)]} />
                    <p>Archive episodes after downloading first match?</p>
                </span>
            </label>
        </div>

<% qualities = Quality.splitQuality(sickrage.QUALITY_DEFAULT) %>
        <% anyQualities = qualities[0] %>
        <% bestQualities = qualities[1] %>
        <%include file="/inc_qualityChooser.mako"/>

        <br>
        <div class="field-pair alt">
            <label for="saveDefaultsButton" class="nocheck clearfix">
                <span class="component-title"><input class="btn btn-inline" type="button" id="saveDefaultsButton" value="Save Defaults" disabled="disabled" /></span>
                <span class="component-desc">
                    <p>Use current values as the defaults</p>
                </span>
            </label>
        </div><br>

% if enable_anime_options:
    <% import sickrage.core.blackandwhitelist %>
    <%include file="/inc_blackwhitelist.mako"/>
% else:
        <input type="hidden" name="anime" id="anime" value="0" />
% endif
