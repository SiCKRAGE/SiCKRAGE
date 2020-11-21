<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'savePostProcessing' %></%def>
<%!
    import sys
    import os.path

    import sickrage
    from sickrage.core.common import Quality
    from sickrage.core.enums import MultiEpNaming, FileTimestampTimezone, ProcessMethod
    from sickrage.core.nameparser import validator
    from sickrage.metadata_providers import MetadataProvider, MetadataProviders
%>

<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#post-processing">${_('Post-Processing')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab"
                                 href="#episode-naming">${_('Episode Naming')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#metadata">${_('Metadata')}</a></li>
</%block>
<%block name="pages">
    <div id="post-processing" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Post-Processing')}</h3>
                <small class="form-text text-muted">
                    ${_('Settings that dictate how SickRage should process completed downloads.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Enabled')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label class="form-check-label">
                            <input type="checkbox" class="toggle color-primary is-material" name="process_automatically"
                                   id="process_automatically" ${('', 'checked')[bool(sickrage.app.config.general.process_automatically)]}/>
                            ${_('Enable the automatic post processor to scan and process any files in your')}
                            <i>${_('Post Processing Dir')}</i>?<br>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('Do not use if you use an external PostProcessing script')}
                            </div>
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Post Processing Dir')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-folder-open"></span></span>
                                    </div>
                                    <input name="tv_download_dir" id="tv_download_dir"
                                           value="${sickrage.app.config.general.tv_download_dir}"
                                           class="form-control"
                                           autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="tv_download_dir">
                                    ${_('The folder where your download client puts the completed TV downloads.')}<br/>
                                    <b>${_('NOTE')}
                                        :</b> ${_('Please use seperate downloading and completed folders in your download client if possible.')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Processing Method:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text"><span class="fas fa-sync"></span></span>
                                    </div>
                                    <select name="process_method" id="process_method" class="form-control"
                                            title="Processing method">
                                        % for item in ProcessMethod:
                                            <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.process_method == item]}>${item.display_name}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="col-md-12">
                                <label class="text-info" for="process_method">
                                    ${_('What method should be used to put files into the library?')}<br/>
                                    <b>${_('NOTE:')}</b> ${_('If you keep seeding torrents after they finish, please avoid the \'move\' processing method to prevent errors.')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Auto Post-Processing Frequency')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <input type="number" min="10" name="auto_postprocessor_frequency"
                                   id="auto_postprocessor_frequency"
                                   value="${sickrage.app.config.general.auto_postprocessor_freq}"
                                   title="Time in minutes to check for new files to auto post-process (min 10)"
                                   class="form-control"/>
                            <div class="input-group-append">
                                <span class="input-group-text">
                                    mins
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Postpone post processing')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="postpone_if_sync_files">
                            <input type="checkbox" class="toggle color-primary is-material"
                                   name="postpone_if_sync_files"
                                   id="postpone_if_sync_files" ${('', 'checked')[bool(sickrage.app.config.general.postpone_if_sync_files)]}/>
                            ${_('Wait to process a folder if sync files are present.')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Sync File Extensions to Ignore')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-file"></span>
                                </span>
                            </div>
                            <input name="sync_files" id="sync_files"
                                   value="${sickrage.app.config.general.sync_files}"
                                   placeholder="${_('ext1,ext2')}"
                                   title="comma separated list of extensions SiCKRAGE ignores when Post Processing"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Rename Episodes')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label>
                            <input type="checkbox" class="toggle color-primary is-material" name="rename_episodes"
                                   id="rename_episodes" ${('', 'checked')[bool(sickrage.app.config.general.rename_episodes)]}/>
                            ${_('Rename episode using the Episode Naming settings?')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Create missing show directories')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="create_missing_show_dirs">
                            <input type="checkbox" class="toggle color-primary is-material"
                                   name="create_missing_show_dirs"
                                   id="create_missing_show_dirs" ${('', 'checked')[bool(sickrage.app.config.general.create_missing_show_dirs)]}/>
                            ${_('Create missing show directories when they get deleted')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Add shows without directory')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="add_shows_wo_dir">
                            <input type="checkbox" class="toggle color-primary is-material" name="add_shows_wo_dir"
                                   id="add_shows_wo_dir" ${('', 'checked')[bool(sickrage.app.config.general.add_shows_wo_dir)]}/>
                            ${_('Add shows without creating a directory (not recommended)')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Move Associated Files')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="move_associated_files">
                            <input type="checkbox" class="toggle color-primary is-material" name="move_associated_files"
                                   id="move_associated_files" ${('', 'checked')[bool(sickrage.app.config.general.move_associated_files)]}/>
                            ${_('Move associated files with the episode when processed?')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Rename .nfo file')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="nfo_rename">
                            <input type="checkbox" class="toggle color-primary is-material" name="nfo_rename"
                                   id="nfo_rename" ${('', 'checked')[bool(sickrage.app.config.general.nfo_rename)]}/>
                            ${_('Rename the original .nfo file to .nfo-orig to avoid conflicts?')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Associated file extensions')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-file"></span>
                                        </span>
                                    </div>
                                    <input name="allowed_extensions" id="allowed_extensions"
                                           value="${sickrage.app.config.general.allowed_extensions}"
                                           class="form-control" autocapitalize="off"/>
                                </div>
                                <label class="text-info" for="allowed_extensions">
                                    ${_('comma separated list of associated file extensions SickRage should keep while post processing. Leaving it empty means no associated files will be post processed')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Delete non associated files')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="delete_non_associated_files">
                            <input type="checkbox" class="toggle color-primary is-material"
                                   name="delete_non_associated_files"
                                   id="delete_non_associated_files" ${('', 'checked')[bool(sickrage.app.config.general.delete_non_associated_files)]}/>
                            ${_('delete non associated files while post processing?')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Change File Date')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="airdate_episodes">
                            <input type="checkbox" class="toggle color-primary is-material" name="airdate_episodes"
                                   id="airdate_episodes" ${('', 'checked')[bool(sickrage.app.config.general.airdate_episodes)]}/>
                            ${_('Set last modified filedate to the date that the episode aired?')}<br/>
                            <div class="text-info"><b>${_('NOTE:')}</b> ${_('Some systems may ignore this feature.')}
                            </div>
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Timezone for File Date:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-clock"></span>
                                </span>
                            </div>
                            <select name="file_timestamp_timezone" id="file_timestamp_timezone"
                                    title="What timezone should be used to change File Date?"
                                    class="form-control">
                                % for item in FileTimestampTimezone:
                                    <option value="${item.name}" ${('', 'selected')[sickrage.app.config.general.file_timestamp_timezone == item]}>${item.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Unpack')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="unpack">
                            <input id="unpack" type="checkbox" class="enabler toggle color-primary is-material"
                                   name="unpack" ${('', 'checked')[bool(sickrage.app.config.general.unpack)]} />
                            ${_('Unpack any TV releases in your')} <i>${_('TV Download Dir')}</i>?<br/>
                            <div class="text-info"><b>${_('NOTE:')}</b> ${_('Only works with RAR archives')}</div>
                        </label>
                    </div>
                </div>
                <div id="content_unpack">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Unpack Directory')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-folder-open"></span></span>
                                </div>
                                <input name="unpack_dir" id="unpack_dir"
                                       value="${sickrage.app.config.general.unpack_dir}"
                                       class="form-control" autocapitalize="off"/>
                            </div>
                            <label class="text-info" for="unpack_dir">
                                ${_('Choose a path to unpack files, leave blank to unpack in download dir')}
                            </label>
                        </div>
                    </div>
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Delete RAR contents')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label for="del_rar_contents">
                                <input type="checkbox" class="toggle color-primary is-material" name="del_rar_contents"
                                       id="del_rar_contents" ${('', 'checked')[bool(sickrage.app.config.general.del_rar_contents)]}/>
                                ${_('Delete content of RAR files, even if Process Method not set to move?')}
                            </label>
                        </div>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Don\'t delete empty folders')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="no_delete">
                            <input type="checkbox" class="toggle color-primary is-material" name="no_delete"
                                   id="no_delete" ${('', 'checked')[bool(sickrage.app.config.general.no_delete)]}/>
                            ${_('Leave empty folders when Post Processing?')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('Can be overridden using manual Post Processing')}
                            </div>
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Follow symbolic-links')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="processor_follow_symlinks">
                            <input type="checkbox" class="toggle color-primary is-material"
                                   name="processor_follow_symlinks"
                                   id="processor_follow_symlinks" ${('', 'checked')[bool(sickrage.app.config.general.processor_follow_symlinks)]}/>
                            ${_('Enable only if you know what <b>circular symbolic links</b> are,<br/>'
                            'and can <b>verify that you have none</b>.')}
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Delete Failed')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <input id="delete_failed" type="checkbox" class="toggle color-primary is-material"
                               name="delete_failed" ${('', 'checked')[bool(sickrage.app.config.failed_downloads.enable)]}/>
                        <label for="delete_failed">
                            ${_('Delete files left over from a failed download?')}<br/>
                        </label>
                    </div>
                </div>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Extra Scripts')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-file"></span>
                                </span>
                            </div>
                            <input name="extra_scripts" id="extra_scripts"
                                   value="${sickrage.app.config.general.extra_scripts}"
                                   class="form-control" autocapitalize="off"/>
                        </div>
                        <label class="text-info" for="extra_scripts">${_('See')} <a
                                href="https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/Post-Processing#extra-scripts">
                            <span class="text-danger"><b>${_('Wiki')}</b></span></a> ${_('for script arguments description and usage.')}
                        </label>
                    </div>
                </div>
                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="episode-naming" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Episode Naming')}</h3>
                <small class="form-text text-muted">
                    ${_('How SickRage will name and sort your episodes.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Name Pattern:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-list"></span></span>
                            </div>
                            <select id="name_presets" class="form-control" title="Choose a naming pattern">
                                <% is_custom = True %>
                                % for cur_preset in validator.name_presets:
                                <% tmp = validator.test_name(cur_preset, anime_type=3) %>
                                % if cur_preset == sickrage.app.config.general.naming_pattern:
                                    <% is_custom = False %>
                                % endif
                                    <option id="${cur_preset}" ${('', 'selected')[sickrage.app.config.general.naming_pattern == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                % endfor
                                <option id="${sickrage.app.config.general.naming_pattern}" ${('', 'selected')[bool(is_custom)]}>
                                    Custom...
                                </option>
                            </select>
                        </div>
                    </div>
                </div>

                <div id="naming_custom">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5"></div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <i class="fas fa-eye" id="show_naming_key" title="Toggle Naming Legend"></i>
                                    </span>
                                </div>
                                <input name="naming_pattern" id="naming_pattern"
                                       value="${sickrage.app.config.general.naming_pattern}"
                                       class="form-control"/>
                            </div>
                            <label for="naming_pattern">
                                <b>${_('NOTE:')}</b> ${_('Don\'t forget to add quality pattern. Otherwise after post-processing the episode will have UNKNOWN quality')}
                            </label>
                        </div>
                    </div>

                    <div id="naming_key" class="nocheck d-none">
                        <table class="table">
                            <thead class="table-secondary text-black-50">
                            <tr>
                                <th class="align-right">${_('Meaning')}</th>
                                <th>${_('Pattern')}</th>
                                <th width="60%">${_('Result')}</th>
                            </tr>
                            </thead>
                            <tfoot class="table-secondary text-black-50">
                            <tr>
                                <th colspan="3">
                                    ${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}
                                </th>
                            </tr>
                            </tfoot>
                            <tbody>
                            <tr>
                                <td class="align-right"><b>${_('Show Name:')}</b></td>
                                <td>%SN</td>
                                <td>${_('Show Name')}</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%S.N</td>
                                <td>${_('Show.Name')}</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%S_N</td>
                                <td>${_('Show_Name')}</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>${_('Season Number:')}</b></td>
                                <td>%S</td>
                                <td>2</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0S</td>
                                <td>02</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>${_('XEM Season Number:')}</b></td>
                                <td>%XMS</td>
                                <td>2</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0XMS</td>
                                <td>02</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>${_('Episode Number:')}</b></td>
                                <td>%E</td>
                                <td>3</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0E</td>
                                <td>03</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>${_('XEM Episode Number:')}</b></td>
                                <td>%XME</td>
                                <td>3</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0XME</td>
                                <td>03</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>${_('Episode Name:')}</b></td>
                                <td>%EN</td>
                                <td>${_('Episode Name')}</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%E.N</td>
                                <td>${_('Episode.Name')}</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%E_N</td>
                                <td>${_('Episode_Name')}</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>${_('Quality:')}</b></td>
                                <td>%QN</td>
                                <td>720p BluRay</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%Q.N</td>
                                <td>720p.BluRay</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%Q_N</td>
                                <td>720p_BluRay</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>${_('Scene Quality:')}</b></td>
                                <td>%SQN</td>
                                <td>${_('720p HDTV x264')}</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%SQ.N</td>
                                <td>${_('720p.HDTV.x264')}</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%SQ_N</td>
                                <td>${_('720p_HDTV_x264')}</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">
                                    <i class="fas fa-info-circle" title="Multi-EP style is ignored"></i>
                                    <b>${_('Release Name:')}</b>
                                </td>
                                <td>%RN</td>
                                <td>${_('Show.Name.S02E03.HDTV.XviD-RLSGROUP')}</td>
                            </tr>
                            <tr>
                                <td class="align-right">
                                    <i class="fas fa-info-circle"
                                       title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                    <b>${_('Release Group:')}</b>
                                </td>
                                <td>%RG</td>
                                <td>RLSGROUP</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">
                                    <i class="fas fa-info-circle"
                                       title="If episode is proper/repack add 'proper' to name."></i>
                                    <b>${_('Release Type:')}</b>
                                </td>
                                <td>%RT</td>
                                <td>PROPER</td>
                            </tr>
                            </tbody>
                        </table>
                        <br>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Multi-Episode Style:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-glasses"></span></span>
                            </div>
                            <select id="naming_multi_ep" name="naming_multi_ep" class="form-control"
                                    title="Choose a Multi-Episode Style">
                                % for multi_ep in sorted(MultiEpNaming, key=lambda x: x.name):
                                    <option value="${multi_ep.name}" ${('', 'selected')[multi_ep == sickrage.app.config.general.naming_multi_ep]}>${multi_ep.display_name}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>

                <div class="card bg-secondary mb-3">
                    <div class="card-header">
                        <h3>${_('Single-EP Sample:')}</h3>
                    </div>
                    <div class="card-body">
                        <div class="card-text">
                            <div id="naming_example_div">
                                <div class="example">
                                    <span class="jumbo" id="naming_example">&nbsp;</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card bg-secondary mb-3">
                    <div class="card-header">
                        <h3>${_('Multi-EP sample:')}</h3>
                    </div>
                    <div class="card-body">
                        <div class="card-text">
                            <div id="naming_example_multi_div">
                                <div class="example">
                                    <span class="jumbo" id="naming_example_multi">&nbsp;</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Strip Show Year')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label>
                            <input type="checkbox" class="toggle color-primary is-material" id="naming_strip_year"
                                   name="naming_strip_year" ${('', 'checked')[bool(sickrage.app.config.general.naming_strip_year)]}/>
                            ${_('Remove the TV show\'s year when renaming the file?')}<br/>
                            <div class="text-info">
                                <b>${_('NOTE:')}</b> ${_('Only applies to shows that have year inside parentheses')}
                            </div>
                        </label>
                    </div>
                </div>

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Custom Air-By-Date')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="naming_custom_abd">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   id="naming_custom_abd"
                                   name="naming_custom_abd" ${('', 'checked')[bool(sickrage.app.config.general.naming_custom_abd)]}/>
                            ${_('Name Air-By-Date shows differently than regular shows?')}
                        </label>
                    </div>
                </div>

                <div id="content_naming_custom_abd">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Air-by-date Name Pattern:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list"></span></span>
                                </div>
                                <select id="name_abd_presets" class="form-control" title="Choose a naming pattern">
                                    <% is_abd_custom = True %>
                                    % for cur_preset in validator.name_abd_presets:
                                    <% tmp = validator.test_name(cur_preset) %>
                                    % if cur_preset == sickrage.app.config.general.naming_abd_pattern:
                                        <% is_abd_custom = False %>
                                    % endif
                                        <option id="${cur_preset}" ${('', 'selected')[sickrage.app.config.general.naming_abd_pattern == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                    % endfor
                                    <option id="${sickrage.app.config.general.naming_abd_pattern}" ${('', 'selected')[bool(is_abd_custom)]}>
                                        Custom...
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="naming_abd_custom">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5"></div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <i class="fas fa-eye" id="show_naming_abd_key"
                                               title="Toggle ABD Naming Legend"></i>
                                        </span>
                                    </div>
                                    <input name="naming_abd_pattern" id="naming_abd_pattern"
                                           value="${sickrage.app.config.general.naming_abd_pattern}"
                                           title="Air-by-date naming pattern"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div id="naming_abd_key" class="nocheck d-none">
                            <table class="table">
                                <thead class="table-secondary text-black-50">
                                <tr>
                                    <th class="align-right">${_('Meaning')}</th>
                                    <th>${_('Pattern')}</th>
                                    <th width="60%">${_('Result')}</th>
                                </tr>
                                </thead>
                                <tfoot class="table-secondary text-black-50">
                                <tr>
                                    <th colspan="3">
                                        ${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}
                                    </th>
                                </tr>
                                </tfoot>
                                <tbody>
                                <tr>
                                    <td class="align-right"><b>${_('Show Name:')}</b></td>
                                    <td>%SN</td>
                                    <td>${_('Show Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%S.N</td>
                                    <td>${_('Show.Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%S_N</td>
                                    <td>${_('Show_Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Regular Air Date:')}</b></td>
                                    <td>%AD</td>
                                    <td>2010 03 09</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%A.D</td>
                                    <td>2010.03.09</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%A_D</td>
                                    <td>2010_03_09</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%A-D</td>
                                    <td>2010-03-09</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Episode Name:')}</b></td>
                                    <td>%EN</td>
                                    <td>${_('Episode Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%E.N</td>
                                    <td>${_('Episode.Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%E_N</td>
                                    <td>${_('Episode_Name')}</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Quality:')}</b></td>
                                    <td>%QN</td>
                                    <td>720p BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%Q.N</td>
                                    <td>720p.BluRay</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%Q_N</td>
                                    <td>720p_BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Year:')}</b></td>
                                    <td>%Y</td>
                                    <td>2010</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Month:')}</b></td>
                                    <td>%M</td>
                                    <td>3</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">&nbsp;</td>
                                    <td>%0M</td>
                                    <td>03</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Day:')}</b></td>
                                    <td>%D</td>
                                    <td>9</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">&nbsp;</td>
                                    <td>%0D</td>
                                    <td>09</td>
                                </tr>
                                <tr>
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="Multi-EP style is ignored"></i>
                                        <b>${_('Release Name:')}</b>
                                    </td>
                                    <td>%RN</td>
                                    <td>${_('Show.Name.2010.03.09.HDTV.XviD-RLSGROUP')}</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                        <b>${_('Release Group:')}</b>
                                    </td>
                                    <td>%RG</td>
                                    <td>RLSGROUP</td>
                                </tr>
                                <tr>
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="If episode is proper/repack add 'proper' to name."></i>
                                        <b>${_('Release Type:')}</b>
                                    </td>
                                    <td>%RT</td>
                                    <td>PROPER</td>
                                </tr>
                                </tbody>
                            </table>
                            <br>
                        </div>
                    </div><!-- /naming_abd_custom -->

                    <div class="card bg-secondary mb-3">
                        <div class="card-header">
                            <h3>${_('Air-by-date Sample:')}</h3>
                        </div>
                        <div class="card-body">
                            <div class="card-text">
                                <div id="naming_example_abd_div">
                                    <div class="example">
                                        <span class="jumbo" id="naming_abd_example">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div><!-- /naming_abd_different -->

                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Custom Sports')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="naming_custom_sports">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   id="naming_custom_sports"
                                   name="naming_custom_sports" ${('', 'checked')[bool(sickrage.app.config.general.naming_custom_sports)]}/>
                            ${_('Name Sports shows differently than regular shows?')}
                        </label>
                    </div>
                </div>

                <div id="content_naming_custom_sports">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Sports Name Pattern:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list"></span></span>
                                </div>
                                <select id="name_sports_presets" class="form-control" title="Choose a naming pattern">
                                    <% is_sports_custom = True %>
                                    % for cur_preset in validator.name_sports_presets:
                                    <% tmp = validator.test_name(cur_preset) %>
                                    % if cur_preset == sickrage.app.config.general.naming_sports_pattern:
                                        <% is_sports_custom = False %>
                                    % endif
                                        <option id="${cur_preset}" ${('', 'selected')[sickrage.app.config.general.naming_sports_pattern == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                    % endfor
                                    <option id="${sickrage.app.config.general.naming_sports_pattern}" ${('', 'selected')[bool(is_sports_custom)]}>
                                        ${_('Custom...')}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="naming_sports_custom">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5"></div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <i class="fas fa-eye" id="show_naming_sports_key"
                                           title="Toggle Sports Naming Legend"></i>
                                    </div>
                                    <input name="naming_sports_pattern" id="naming_sports_pattern"
                                           value="${sickrage.app.config.general.naming_sports_pattern}"
                                           title="Sports naming pattern"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div id="naming_sports_key" class="nocheck d-none">
                            <table class="table">
                                <thead class="table-secondary text-black-50">
                                <tr>
                                    <th class="align-right">${_('Meaning')}</th>
                                    <th>${_('Pattern')}</th>
                                    <th width="60%">${_('Result')}</th>
                                </tr>
                                </thead>
                                <tfoot class="table-secondary text-black-50">
                                <tr>
                                    <th colspan="3">
                                        ${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}
                                    </th>
                                </tr>
                                </tfoot>
                                <tbody>
                                <tr>
                                    <td class="align-right"><b>${_('Show Name:')}</b></td>
                                    <td>%SN</td>
                                    <td>${_('Show Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%S.N</td>
                                    <td>${_('Show.Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%S_N</td>
                                    <td>${_('Show_Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Sports Air Date:')}</b></td>
                                    <td>%AD</td>
                                    <td>9 ${_('Mar')} 2011</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%A.D</td>
                                    <td>9.${_('Mar')}.2011</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%A_D</td>
                                    <td>9_${_('Mar')}_2011</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%A-D</td>
                                    <td>9-${_('Mar')}-2011</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Episode Name:')}</b></td>
                                    <td>%EN</td>
                                    <td>${_('Episode Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%E.N</td>
                                    <td>${_('Episode.Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%E_N</td>
                                    <td>${_('Episode_Name')}</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Quality:')}</b></td>
                                    <td>%QN</td>
                                    <td>720p BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%Q.N</td>
                                    <td>720p.BluRay</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%Q_N</td>
                                    <td>720p_BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Year:')}</b></td>
                                    <td>%Y</td>
                                    <td>2010</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Month:')}</b></td>
                                    <td>%M</td>
                                    <td>3</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">&nbsp;</td>
                                    <td>%0M</td>
                                    <td>03</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Day:')}</b></td>
                                    <td>%D</td>
                                    <td>9</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">&nbsp;</td>
                                    <td>%0D</td>
                                    <td>09</td>
                                </tr>
                                <tr>
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="Multi-EP style is ignored"></i>
                                        <b>${_('Release Name:')}</b>
                                    </td>
                                    <td>%RN</td>
                                    <td>${_('Show.Name.9th.Mar.2011.HDTV.XviD-RLSGROUP')}</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                        <b>${_('Release Group:')}</b>
                                    </td>
                                    <td>%RG</td>
                                    <td>RLSGROUP</td>
                                </tr>
                                <tr>
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="If episode is proper/repack add 'proper' to name.">
                                        </i>
                                        <b>${_('Release Type:')}</b></td>
                                    <td>%RT</td>
                                    <td>PROPER</td>
                                </tr>
                                </tbody>
                            </table>
                            <br>
                        </div>
                    </div><!-- /naming_sports_custom -->

                    <div class="card bg-secondary mb-3">
                        <div class="card-header">
                            <h3>${_('Sports Sample:')}</h3>
                        </div>
                        <div class="card-body">
                            <div class="card-text">
                                <div id="naming_sports_example_div">
                                    <div class="example">
                                        <span class="jumbo" id="naming_sports_example">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div><!-- /naming_sports_different -->

                <!-- naming_anime_custom -->
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Custom Anime')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <label for="naming_custom_anime">
                            <input type="checkbox" class="enabler toggle color-primary is-material"
                                   id="naming_custom_anime"
                                   name="naming_custom_anime" ${('', 'checked')[bool(sickrage.app.config.general.naming_custom_anime)]}/>
                            ${_('Name Anime shows differently than regular shows?')}
                        </label>
                    </div>
                </div>

                <div id="content_naming_custom_anime">
                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Anime Name Pattern:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-list"></span></span>
                                </div>
                                <select id="name_anime_presets" class="form-control" title="Choose a naming pattern">
                                    <% is_anime_custom = True %>
                                    % for cur_preset in validator.name_anime_presets:
                                    <% tmp = validator.test_name(cur_preset) %>
                                    % if cur_preset == sickrage.app.config.general.naming_anime_pattern:
                                        <% is_anime_custom = False %>
                                    % endif
                                        <option id="${cur_preset}" ${('', 'selected')[cur_preset == sickrage.app.config.general.naming_anime_pattern]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                    % endfor
                                    <option id="${sickrage.app.config.general.naming_anime_pattern}" ${('', 'selected')[bool(is_anime_custom)]}>
                                        ${_('Custom...')}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div id="naming_anime_custom">
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">
                                    &nbsp;
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <i class="fas fa-eye" id="show_naming_anime_key"
                                               title="Toggle Anime Naming Legend"></i>
                                        </span>
                                    </div>
                                    <input name="naming_anime_pattern" id="naming_anime_pattern"
                                           value="${sickrage.app.config.general.naming_anime_pattern}"
                                           title="Anime naming pattern"
                                           class="form-control"/>
                                </div>
                            </div>
                        </div>

                        <div id="naming_anime_key" class="nocheck d-none">
                            <table class="table">
                                <thead class="table-secondary text-black-50">
                                <tr>
                                    <th class="align-right">${_('Meaning')}</th>
                                    <th>${_('Pattern')}</th>
                                    <th width="60%">${_('Result')}</th>
                                </tr>
                                </thead>
                                <tfoot class="table-secondary text-black-50">
                                <tr>
                                    <th colspan="3">
                                        ${_('Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)')}
                                    </th>
                                </tr>
                                </tfoot>
                                <tbody>
                                <tr>
                                    <td class="align-right"><b>${_('Show Name:')}</b></td>
                                    <td>%SN</td>
                                    <td>${_('Show Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%S.N</td>
                                    <td>${_('Show.Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%S_N</td>
                                    <td>${_('Show_Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Season Number:')}</b></td>
                                    <td>%S</td>
                                    <td>2</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%0S</td>
                                    <td>02</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('XEM Season Number:')}</b></td>
                                    <td>%XMS</td>
                                    <td>2</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%0XMS</td>
                                    <td>02</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Episode Number:')}</b></td>
                                    <td>%E</td>
                                    <td>3</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%0E</td>
                                    <td>03</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('XEM Episode Number:')}</b></td>
                                    <td>%XME</td>
                                    <td>3</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%0XME</td>
                                    <td>03</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right"><b>${_('Episode Name:')}</b></td>
                                    <td>%EN</td>
                                    <td>${_('Episode Name')}</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%E.N</td>
                                    <td>${_('Episode.Name')}</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%E_N</td>
                                    <td>${_('Episode_Name')}</td>
                                </tr>
                                <tr>
                                    <td class="align-right"><b>${_('Quality:')}</b></td>
                                    <td>%QN</td>
                                    <td>720p BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td>&nbsp;</td>
                                    <td>%Q.N</td>
                                    <td>720p.BluRay</td>
                                </tr>
                                <tr>
                                    <td>&nbsp;</td>
                                    <td>%Q_N</td>
                                    <td>720p_BluRay</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="Multi-EP style is ignored"></i>
                                        <b>${_('Release Name:')}</b>
                                    </td>
                                    <td>%RN</td>
                                    <td>${_('Show.Name.S02E03.HDTV.XviD-RLSGROUP')}</td>
                                </tr>
                                <tr>
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                        <b>${_('Release Group:')}</b>
                                    </td>
                                    <td>%RG</td>
                                    <td>RLSGROUP</td>
                                </tr>
                                <tr class="even">
                                    <td class="align-right">
                                        <i class="fas fa-info-circle"
                                           title="If episode is proper/repack add 'proper' to name."></i>
                                        <b>${_('Release Type:')}</b>
                                    </td>
                                    <td>%RT</td>
                                    <td>PROPER</td>
                                </tr>
                                </tbody>
                            </table>
                            <br>
                        </div>
                    </div><!-- /naming_anime_custom -->

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Multi-Episode Style:')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-glasses"></span></span>
                                </div>
                                <select id="naming_anime_multi_ep" name="naming_anime_multi_ep"
                                        title="Multi-Episode Style"
                                        class="form-control">
                                    % for multi_ep in sorted(MultiEpNaming, key=lambda x: x.name):
                                        <option value="${multi_ep.name}" ${('', 'selected')[multi_ep == sickrage.app.config.general.naming_anime_multi_ep]}>${multi_ep.display_name}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="card bg-secondary mb-3">
                        <div class="card-header">
                            <h3>${_('Single-EP Anime Sample:')}</h3>
                        </div>
                        <div class="card-body">
                            <div class="card-text">
                                <div id="naming_example_anime_div">
                                    <div class="example">
                                        <span class="jumbo" id="naming_example_anime">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card bg-secondary mb-3">
                        <div class="card-header">
                            <h3>${_('Multi-EP Anime sample:')}</h3>
                        </div>
                        <div class="card-body">
                            <div class="card-text">
                                <div id="naming_example_multi_anime_div">
                                    <div class="example">
                                        <span class="jumbo" id="naming_example_multi_anime">&nbsp;</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Add Absolute Number')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label>
                                <input type="radio" name="naming_anime" id="naming_anime"
                                       value="1" ${('', 'checked')[sickrage.app.config.general.naming_anime == 1]}/>
                                ${_('Add the absolute number to the season/episode format?')}<br/>
                                <div class="text-info">
                                    <b>${_('NOTE:')}</b> ${_('Only applies to animes. (eg. S15E45 - 310 vs S15E45)')}
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('Only Absolute Number')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label>
                                <input type="radio" name="naming_anime" id="naming_anime_only"
                                       value="2" ${('', 'checked')[sickrage.app.config.general.naming_anime == 2]}/>
                                ${_('Replace season/episode format with absolute number')}<br/>
                                <div class="text-info"><b>${_('NOTE:')}</b> ${_('Only applies to animes.')}</div>
                            </label>
                        </div>
                    </div>

                    <div class="form-row form-group">
                        <div class="col-lg-3 col-md-4 col-sm-5">
                            <label class="component-title">${_('No Absolute Number')}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                            <label>
                                <input type="radio" name="naming_anime" id="naming_anime_none"
                                       value="3" ${('', 'checked')[sickrage.app.config.general.naming_anime == 3]}/>
                                ${_('Dont include the absolute number')}<br/>
                                <div class="text-info"><b>${_('NOTE:')}</b> ${_('Only applies to animes.')}</div>
                            </label>
                        </div>
                    </div>

                </div><!-- /naming_anime_different -->

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->

    <div id="metadata" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Metadata')}</h3>
                <small class="form-text text-muted">
                    ${_('The data associated to the data. These are files associated to a TV show in the form of images and text that, when supported, will enhance the viewing experience.')}
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <% m_dict = sickrage.app.metadata_providers %>
                <div class="form-row form-group">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Metadata Type:')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text">
                                    <span class="fas fa-tv"></span>
                                </span>
                            </div>
                            <select id="metadataType" class="form-control">
                                % for (cur_id, cur_generator) in sorted(m_dict.items()):
                                    <option value="${cur_id}">${cur_generator.name}</option>
                                % endfor
                            </select>
                        </div>
                        <label class="text-info" for="metadataType">
                            ${_('Toggle the metadata options that you wish to be created.')}<br/>
                            <b>${_('Multiple targets may be used.')}</b>
                        </label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5">
                        <label class="component-title">${_('Select Metadata')}</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                        % for (cur_id, cur_generator) in m_dict.items():
                            <div class="list-group metadataDiv" id="${cur_id}">
                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_show_metadata">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_show_metadata" ${('', 'checked')[bool(cur_generator.show_metadata)]}/>
                                        ${_('Show Metadata')}
                                        <span id="${cur_id}_eg_show_metadata">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_show_metadata}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_episode_metadata">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_episode_metadata" ${('', 'checked')[bool(cur_generator.episode_metadata)]}/>
                                        ${_('Episode Metadata')}
                                        <span id="${cur_id}_eg_episode_metadata">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_episode_metadata}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_fanart">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_fanart" ${('', 'checked')[bool(cur_generator.fanart)]}/>
                                        ${_('Show Fanart')}
                                        <span id="${cur_id}_eg_fanart">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_fanart}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_poster">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_poster" ${('', 'checked')[bool(cur_generator.poster)]}/>
                                        ${_('Show Poster')}
                                        <span id="${cur_id}_eg_poster">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_poster}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_banner">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_banner" ${('', 'checked')[bool(cur_generator.banner)]}/>
                                        ${_('Show Banner')}
                                        <span id="${cur_id}_eg_banner">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_banner}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_episode_thumbnails">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_episode_thumbnails" ${('', 'checked')[bool(cur_generator.episode_thumbnails)]}/>
                                        ${_('Episode Thumbnails')}
                                        <span id="${cur_id}_eg_episode_thumbnails">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_episode_thumbnails}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_season_posters">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_season_posters" ${('', 'checked')[bool(cur_generator.season_posters)]}/>
                                        ${_('Season Posters')}
                                        <span id="${cur_id}_eg_season_posters">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_season_posters}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_season_banners">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_season_banners" ${('', 'checked')[bool(cur_generator.season_banners)]}/>
                                        ${_('Season Banners')}
                                        <span id="${cur_id}_eg_season_banners">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_season_banners}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label for="${cur_id}_season_all_poster">
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_season_all_poster" ${('', 'checked')[bool(cur_generator.season_all_poster)]}/>
                                        ${_('Season All Poster')}
                                        <span id="${cur_id}_eg_season_all_poster">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_season_all_poster}</span>
                                        </span>
                                    </label>
                                </div>

                                <div class="list-group-item-dark rounded mb-1">
                                    <label>
                                        <input type="checkbox" class="metadata_checkbox ml-1"
                                               id="${cur_id}_season_all_banner" ${('', 'checked')[bool(cur_generator.season_all_banner)]}/>
                                        ${_('Season All Banner')}
                                        <span id="${cur_id}_eg_season_all_banner">
                                            <span class="blockquote-footer ml-1">${cur_generator.eg_season_all_banner}</span>
                                        </span>
                                    </label>
                                </div>
                            </div>
                            <input type="hidden" name="${cur_id}_data" id="${cur_id}_data"
                                   value="${cur_generator.config}"/>
                        % endfor
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane3 //-->
</%block>