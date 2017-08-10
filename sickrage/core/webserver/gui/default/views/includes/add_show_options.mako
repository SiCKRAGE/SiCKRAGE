<%
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
%>
% if sickrage.srCore.srConfig.USE_SUBTITLES:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <label class="component-title">Subtitles</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <label>
                <input type="checkbox" name="subtitles"
                          id="subtitles" ${('', 'checked')[bool(sickrage.srCore.srConfig.SUBTITLES_DEFAULT)]} />
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Flatten Folders</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input class="cb" type="checkbox" name="flatten_folders"
                      id="flatten_folders" ${('', 'checked')[bool(sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT)]}/>
        </label>
    </div>
</div>
% if enable_anime_options:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <label class="component-title">Anime</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <label>
                <input type="checkbox" name="anime"
                          id="anime" ${('', 'checked')[bool(sickrage.srCore.srConfig.ANIME_DEFAULT)]} />
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Scene Numbering</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input type="checkbox" name="scene"
                      id="scene" ${('', 'checked')[bool(sickrage.srCore.srConfig.SCENE_DEFAULT)]} />
        </label>
    </div>


</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Archive on first match</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input type="checkbox" name="archive"
                      id="archive" ${('', 'checked')[bool(sickrage.srCore.srConfig.ARCHIVE_DEFAULT)]} />
        </label>
    </div>


</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Status for previously aired episodes</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <select name="defaultStatus" id="statusSelect" class="form-control form-control-inline input-sm">
            % for curStatus in [SKIPPED, WANTED, IGNORED]:
                <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.STATUS_DEFAULT == curStatus]}>${statusStrings[curStatus]}</option>
            % endfor
        </select>
        </label>
    </div>

</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Status for all future episodes</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <select name="defaultStatusAfter" id="statusSelectAfter"
                       class="form-control form-control-inline input-sm">
            % for curStatus in [SKIPPED, WANTED, IGNORED]:
                <option value="${curStatus}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.STATUS_DEFAULT_AFTER == curStatus]}>${statusStrings[curStatus]}</option>
            % endfor
        </select>
        </label>
    </div>
</div>

<div class="field-pair row">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">Preferred Quality</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <%include file="quality_chooser.mako"/>
    </div>
</div>
<br/>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">
            <input class="btn btn-inline" type="button" id="saveDefaultsButton" value="Save As Defaults"
                   disabled="disabled"/>
        </label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>Use current values as the defaults</label>
    </div>
</div>

% if enable_anime_options:
    <% import sickrage.core.blackandwhitelist %>
    <%include file="blackwhitelist.mako"/>
% else:
    <input type="hidden" name="anime" id="anime" value="0"/>
% endif
