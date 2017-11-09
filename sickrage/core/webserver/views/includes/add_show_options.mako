<%
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
%>
% if sickrage.app.config.use_subtitles:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <label class="component-title">${_('Subtitles')}</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <label>
                <input type="checkbox" name="subtitles"
                       id="subtitles" ${('', 'checked')[bool(sickrage.app.config.subtitles_default)]} />
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Flatten Folders')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input class="cb" type="checkbox" name="flatten_folders"
                   id="flatten_folders" ${('', 'checked')[bool(sickrage.app.config.flatten_folders_default)]}/>
        </label>
    </div>
</div>
% if enable_anime_options:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <label class="component-title">${_('Anime')}</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <label>
                <input type="checkbox" name="anime"
                       id="anime" ${('', 'checked')[bool(sickrage.app.config.anime_default)]} />
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Scene Numbering')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input type="checkbox" name="scene"
                   id="scene" ${('', 'checked')[bool(sickrage.app.config.scene_default)]} />
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Archive on first match')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>
            <input type="checkbox" name="archive"
                   id="archive" ${('', 'checked')[bool(sickrage.app.config.archive_default)]} />
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Status for previously aired episodes')}</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <div class="input-group input350">
            <div class="input-group-addon">
                <span class="glyphicon glyphicon-arrow-left"></span>
            </div>
            <select name="defaultStatus" id="statusSelect" class="form-control"
                    title="Status for previously aired episodes">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected')[sickrage.app.config.status_default == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </div>
    </div>
</div>
<br/>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Status for all future episodes')}</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <div class="input-group input350">
            <div class="input-group-addon">
                <span class="glyphicon glyphicon-arrow-right"></span>
            </div>
            <select name="defaultStatusAfter" id="statusSelectAfter" title="Status for future episodes"
                    class="form-control">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected')[sickrage.app.config.status_default_after == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </div>
    </div>
</div>
<br/>
<div class="field-pair row">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">${_('Preferred Quality')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <%include file="quality_chooser.mako"/>
    </div>
</div>
<br/>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
        <label class="component-title">
            <input class="btn btn-inline" type="button" id="saveDefaultsButton" value="${_('Save As Defaults')}"
                   disabled/>
        </label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
        <label>${_('Use current values as the defaults')}</label>
    </div>
</div>

% if enable_anime_options:
    <% import sickrage.core.blackandwhitelist %>
    <%include file="blackwhitelist.mako"/>
% else:
    <input type="hidden" name="anime" id="anime" value="0"/>
% endif
