<%
    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings, statusStrings, SearchFormats
%>
<%namespace file="../includes/quality_chooser.mako" import="QualityChooser"/>
% if sickrage.app.config.use_subtitles:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5">
            <label class="component-title">${_('Subtitles')}</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
            <label>
                <input type="checkbox" class="toggle color-primary is-material" name="subtitles"
                       id="subtitles" ${('', 'checked')[bool(sickrage.app.config.subtitles_default)]} />
                ${_('enables searching for episode subtitles')}
            </label>
        </div>
    </div>

    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5">
            <label class="component-title">${_('Subtitles Metadata')}</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
            <label>
                <input type="checkbox" class="toggle color-primary is-material" name="sub_use_sr_metadata"
                       id="sub_use_sr_metadata"/>
                ${_('use SiCKRAGE metadata when searching for subtitle, this will override the auto-discovered metadata')}
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Season folders')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>
            <input type="checkbox" class="toggle color-primary is-material" name="flatten_folders"
                   id="flatten_folders" ${('', 'checked')[bool(not sickrage.app.config.flatten_folders_default)]}/>
            ${_('group episodes by season folder (uncheck to store in a single folder)')}
        </label>
    </div>
</div>
% if enable_anime_options:
    <div class="row field-pair">
        <div class="col-lg-3 col-md-4 col-sm-5">
            <label class="component-title">${_('Anime')}</label>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
            <label>
                <input type="checkbox" class="toggle color-primary is-material" name="anime"
                       id="anime" ${('', 'checked')[bool(sickrage.app.config.anime_default)]} />
                ${_('search by absolute numbering and enables searching with anime providers')}
            </label>
        </div>
    </div>
% endif
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('DVD Order')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>
            <input type="checkbox" class="toggle color-primary is-material" id="dvdorder"
                   name="dvdorder"/>
            ${_('use the DVD order instead of the air order')}
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Scene Numbering')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>
            <input type="checkbox" class="toggle color-primary is-material" name="scene"
                   id="scene" ${('', 'checked')[bool(sickrage.app.config.scene_default)]} />
            ${_('use scene numbering instead of indexer numbering')}
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Skip Downloaded')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>
            <input type="checkbox" class="toggle color-primary is-material" name="skip_downloaded"
                   id="skip_downloaded" ${('', 'checked')[bool(sickrage.app.config.skip_downloaded_default)]} />
            ${_('skips updating quality of old/new downloaded episodes')}
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Append Show Year to Show Folder')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>
            <input type="checkbox" class="toggle color-primary is-material" name="add_show_year"
                   id="add_show_year" ${('', 'checked')[bool(sickrage.app.config.add_show_year_default)]} />
            ${_('include year of show in show folder name during initial show folder creation')}
        </label>
    </div>
</div>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Search Format')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <div class="input-group">
            <div class="input-group-prepend">
                <span class="input-group-text">
                    <span class="fas fa-list"></span>
                </span>
            </div>
            <select id="search_format" name="search_format" class="form-control">
                % for search_format, search_format_string in SearchFormats.search_format_strings.items():
                    <option value="${search_format}" ${('', 'selected')[sickrage.app.config.search_format_default == search_format]}>${search_format_string}</option>
                % endfor
            </select>
        </div>
    </div>
</div>
<br/>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Status for previously aired episodes')}</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <div class="input-group">
            <div class="input-group-prepend">
                <span class="input-group-text"><span class="fas fa-arrow-left"></span></span>
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
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Status for all future episodes')}</label>
    </div>

    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <div class="input-group">
            <div class="input-group-prepend">
                <span class="input-group-text"><span class="fas fa-arrow-right"></span></span>
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
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">${_('Preferred Quality')}</label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        ${QualityChooser()}
    </div>
</div>
<br/>
<div class="row field-pair">
    <div class="col-lg-3 col-md-4 col-sm-5">
        <label class="component-title">
            <input class="btn" type="button" id="saveDefaultsButton" value="${_('Save As Defaults')}"
                   disabled/>
        </label>
    </div>
    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
        <label>${_('Use current values as the defaults')}</label>
    </div>
</div>

% if enable_anime_options:
    <% import sickrage.core.blackandwhitelist %>
    <%include file="blackwhitelist.mako"/>
% else:
    <input type="hidden" name="anime" id="anime" value="0"/>
% endif
