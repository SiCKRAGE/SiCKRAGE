<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'savePostProcessing' %></%def>
<%!
    import os.path

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets, multiEpStrings
    from sickrage.core.nameparser import validator
    from sickrage.metadata import GenericMetadata, metadataProvidersDict
%>

<%block name="tabs">
    <ul class="nav nav-tabs">
        <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Post-Processing</a></li>
        <li><a data-toggle="tab" href="#core-tab-pane2">Episode Naming</a></li>
        <li><a data-toggle="tab" href="#core-tab-pane3">Metadata</a></li>
    </ul>
</%block>
<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="tab-pane-desc">
            <h3>Post-Processing</h3>
            <p>Settings that dictate how SickRage should process completed downloads.</p>
        </div>
        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Enabled</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="process_automatically"
                           id="process_automatically" ${('', 'checked')[bool(sickrage.srCore.srConfig.PROCESS_AUTOMATICALLY)]}/>
                    <label for="process_automatically">
                        Enable the automatic post processor to scan and process any files in your <i>Post Processing
                        Dir</i>?<br>
                        <b>NOTE:</b> Do not use if you use an external PostProcessing script
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Post Processing Dir</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="input-group">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-folder-open"></span>
                                </div>
                                <input name="tv_download_dir" id="tv_download_dir"
                                       value="${sickrage.srCore.srConfig.TV_DOWNLOAD_DIR}"
                                       class="form-control"
                                       autocapitalize="off"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <label for="tv_download_dir">
                                The folder where your download client puts the completed TV downloads.<br/>
                                <b>NOTE:</b> Please use seperate downloading and completed folders in your download
                                client if
                                possible.
                            </label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Processing Method:</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-refresh"></span>
                                </div>
                                <select name="process_method" id="process_method" class="form-control"
                                        title="Processing method">
                                    <% process_method_text = {'copy': "Copy", 'move': "Move", 'hardlink': "Hard Link", 'symlink' : "Symbolic Link"} %>
                                    % for curAction in ('copy', 'move', 'hardlink', 'symlink'):
                                        <option value="${curAction}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <label for="process_method">
                                What method should be used to put files into the library?<br/>
                                <b>NOTE:</b> If you keep seeding torrents after they finish, please avoid the 'move'
                                processing method to prevent errors.
                            </label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Auto Post-Processing Frequency</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-time"></span>
                        </div>
                        <input type="number" min="10" name="autopostprocessor_frequency"
                               id="autopostprocessor_frequency"
                               value="${sickrage.srCore.srConfig.AUTOPOSTPROCESSOR_FREQ}"
                               title="Time in minutes to check for new files to auto post-process (min 10)"
                               class="form-control"/>
                        <div class="input-group-addon">
                            mins
                        </div>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Postpone post processing</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="postpone_if_sync_files"
                           id="postpone_if_sync_files" ${('', 'checked')[bool(sickrage.srCore.srConfig.POSTPONE_IF_SYNC_FILES)]}/>
                    <label for="postpone_if_sync_files">
                        Wait to process a folder if sync files are present.
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Sync File Extensions to Ignore</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-file"></span>
                        </div>
                        <input name="sync_files" id="sync_files"
                               value="${sickrage.srCore.srConfig.SYNC_FILES}"
                               placeholder="ext1,ext2"
                               title="comma separated list of extensions SiCKRAGE ignores when Post Processing"
                               class="form-control" autocapitalize="off"/>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Rename Episodes</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Rename episode using the Episode
                    <input type="checkbox" name="rename_episodes"
                           id="rename_episodes" ${('', 'checked')[bool(sickrage.srCore.srConfig.RENAME_EPISODES)]}/>
                    <label for="rename_episodes">
                        Naming settings?
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Create missing show directories</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Create missing show directories
                    <input type="checkbox" name="create_missing_show_dirs"
                           id="create_missing_show_dirs" ${('', 'checked')[bool(sickrage.srCore.srConfig.CREATE_MISSING_SHOW_DIRS)]}/>
                    <label for="create_missing_show_dirs">
                        when they get deleted
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Add shows without directory</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Add shows without creating a
                    <input type="checkbox" name="add_shows_wo_dir"
                           id="add_shows_wo_dir" ${('', 'checked')[bool(sickrage.srCore.srConfig.ADD_SHOWS_WO_DIR)]}/>
                    <label for="add_shows_wo_dir">
                        directory (not recommended)
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Move Associated Files</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Move srr/srt/sfv/etc files with the
                    <input type="checkbox" name="move_associated_files"
                           id="move_associated_files" ${('', 'checked')[bool(sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES)]}/>
                    <label for="move_associated_files">
                        episode when processed?
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Rename .nfo file</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Rename the original .nfo file to
                    <input type="checkbox" name="nfo_rename"
                           id="nfo_rename" ${('', 'checked')[bool(sickrage.srCore.srConfig.NFO_RENAME)]}/>
                    <label for="nfo_rename">
                        .nfo-orig to avoid conflicts?
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Change File Date</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="airdate_episodes"
                           id="airdate_episodes" ${('', 'checked')[bool(sickrage.srCore.srConfig.AIRDATE_EPISODES)]}/>
                    <label for="airdate_episodes">
                        Set last modified filedate to the date that the episode aired?<br/>
                        <b>NOTE:</b> Some systems may ignore this feature.
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Timezone for File Date:</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-time"></span>
                        </div>
                        <select name="file_timestamp_timezone" id="file_timestamp_timezone"
                                title="What timezone should be used to change File Date?"
                                class="form-control">
                            % for curTimezone in ('local','network'):
                                <option value="${curTimezone}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.FILE_TIMESTAMP_TIMEZONE == curTimezone]}>${curTimezone}</option>
                            % endfor
                        </select>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Unpack</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input id="unpack" type="checkbox"
                           name="unpack" ${('', 'checked')[bool(sickrage.srCore.srConfig.UNPACK)]} />
                    <label for="unpack">
                        Unpack any TV releases in your <i>TV Download Dir</i>?<br/>
                        <b>NOTE:</b> Only working with RAR archive
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Delete RAR contents</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="del_rar_contents"
                           id="del_rar_contents" ${('', 'checked')[bool(sickrage.srCore.srConfig.DELRARCONTENTS)]}/>
                    <label for="del_rar_contents">
                        Delete content of RAR files, even if Process Method not set to move?
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Don't delete empty folders</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input type="checkbox" name="no_delete"
                           id="no_delete" ${('', 'checked')[bool(sickrage.srCore.srConfig.NO_DELETE)]}/>
                    <label for="no_delete">
                        Leave empty folders when Post Processing?<br/>
                        <b>NOTE:</b> Can be overridden using manual Post Processing
                    </label>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Use Failed Downloads</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <input id="use_failed_downloads" type="checkbox" class="enabler"
                           name="use_failed_downloads" ${('', 'checked')[bool(sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS)]}/>
                    <label for="use_failed_downloads">Use Failed Download Handling?</label>
                </div>
            </div>
            <div id="content_use_failed_downloads">
                <div class="row field-pair">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Delete Failed</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <input id="delete_failed" type="checkbox"
                               name="delete_failed" ${('', 'checked')[bool(sickrage.srCore.srConfig.DELETE_FAILED)]}/>
                        <label for="delete_failed">
                            Delete files left over from a failed download?<br/>
                            <b>NOTE:</b> This only works if Use Failed Downloads is enabled.
                        </label>
                    </div>
                </div>
            </div>
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Extra Scripts</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-file"></span>
                        </div>
                        <input name="extra_scripts" id="extra_scripts"
                               value="${'|'.join(sickrage.srCore.srConfig.EXTRA_SCRIPTS)}"
                               class="form-control" autocapitalize="off"/>
                    </div>
                    <label for="extra_scripts">See <a href="https://git.sickrage.ca/SiCKRAGE/sickrage/wikis/Post-Processing#extra-scripts">
                    <span style="color: red; "><b>Wiki</b></span> </a> for script arguments description and usage.</label>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <input type="submit" class="btn config_submitter" value="Save Changes"/>
                </div>
            </div>
        </fieldset>
    </div><!-- /tab-pane1 //-->
    <div id="core-tab-pane2" class="tab-pane fade">

        <div class="tab-pane-desc">
            <h3>Episode Naming</h3>
            <p>How SickRage will name and sort your episodes.</p>
        </div>

        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <label class="nocheck" for="name_presets">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Name Pattern:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="input-group input350">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-list"></span>
                            </div>
                            <select id="name_presets" class="form-control">
                                <% is_custom = True %>
                                % for cur_preset in validator.name_presets:
                                <% tmp = validator.test_name(cur_preset, anime_type=3) %>
                                % if cur_preset == sickrage.srCore.srConfig.NAMING_PATTERN:
                                    <% is_custom = False %>
                                % endif
                                    <option id="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NAMING_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                % endfor
                                <option id="${sickrage.srCore.srConfig.NAMING_PATTERN}" ${('', 'selected="selected"')[bool(is_custom)]}>
                                    Custom...
                                </option>
                            </select>
                        </div>
                    </div>
                </label>
            </div>

            <div id="naming_custom">
                <div class="row field-pair" style="padding-top: 0;">
                    <label class="nocheck">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">
                                &nbsp;
                            </label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <input name="naming_pattern" id="naming_pattern"
                                   value="${sickrage.srCore.srConfig.NAMING_PATTERN}"
                                   class="form-control"/>
                            <img src="${srWebRoot}/images/legend16.png" width="16" height="16"
                                 alt="[Toggle Key]" id="show_naming_key" title="Toggle Naming Legend"
                                 class="legend" class="legend"/>
                        </div>
                    </label>
                    <label class="nocheck">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">&nbsp;</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc"><b>NOTE:</b> Don't forget to
                            add quality pattern. Otherwise after post-processing the episode will have UNKNOWN quality
                        </div>
                    </label>
                </div>

                <div id="naming_key" class="nocheck" style="display: none;">
                    <table class="Key">
                        <thead>
                        <tr>
                            <th class="align-right">Meaning</th>
                            <th>Pattern</th>
                            <th width="60%">Result</th>
                        </tr>
                        </thead>
                        <tfoot>
                        <tr>
                            <th colspan="3">
                                Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)
                            </th>
                        </tr>
                        </tfoot>
                        <tbody>
                        <tr>
                            <td class="align-right"><b>Show Name:</b></td>
                            <td>%SN</td>
                            <td>Show Name</td>
                        </tr>
                        <tr class="even">
                            <td>&nbsp;</td>
                            <td>%S.N</td>
                            <td>Show.Name</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%S_N</td>
                            <td>Show_Name</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><b>Season Number:</b></td>
                            <td>%S</td>
                            <td>2</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%0S</td>
                            <td>02</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><b>XEM Season Number:</b></td>
                            <td>%XMS</td>
                            <td>2</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%0XMS</td>
                            <td>02</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><b>Episode Number:</b></td>
                            <td>%E</td>
                            <td>3</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%0E</td>
                            <td>03</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><b>XEM Episode Number:</b></td>
                            <td>%XME</td>
                            <td>3</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%0XME</td>
                            <td>03</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><b>Episode Name:</b></td>
                            <td>%EN</td>
                            <td>Episode Name</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%E.N</td>
                            <td>Episode.Name</td>
                        </tr>
                        <tr class="even">
                            <td>&nbsp;</td>
                            <td>%E_N</td>
                            <td>Episode_Name</td>
                        </tr>
                        <tr>
                            <td class="align-right"><b>Quality:</b></td>
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
                            <td class="align-right"><b>Scene Quality:</b></td>
                            <td>%SQN</td>
                            <td>720p HDTV x264</td>
                        </tr>
                        <tr class="even">
                            <td>&nbsp;</td>
                            <td>%SQ.N</td>
                            <td>720p.HDTV.x264</td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                            <td>%SQ_N</td>
                            <td>720p_HDTV_x264</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                       title="Multi-EP style is ignored"></i> <b>Release
                                Name:</b></td>
                            <td>%RN</td>
                            <td>Show.Name.S02E03.HDTV.XviD-RLSGROUP</td>
                        </tr>
                        <tr>
                            <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                       title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                <b>Release Group:</b></td>
                            <td>%RG</td>
                            <td>RLSGROUP</td>
                        </tr>
                        <tr class="even">
                            <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                       title="If episode is proper/repack add 'proper' to name."></i>
                                <b>Release Type:</b></td>
                            <td>%RT</td>
                            <td>PROPER</td>
                        </tr>
                        </tbody>
                    </table>
                    <br>
                </div>
            </div>

            <div class="row field-pair">
                <label class="nocheck" for="naming_multi_ep">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Multi-Episode Style:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="naming_multi_ep" name="naming_multi_ep" class="form-control">
                            % for cur_multi_ep in sorted(multiEpStrings.items(), key=lambda x: x[1]):
                                <option value="${cur_multi_ep[0]}" ${('', 'selected="selected"')[cur_multi_ep[0] == sickrage.srCore.srConfig.NAMING_MULTI_EP]}>${cur_multi_ep[1]}</option>
                            % endfor
                        </select>
                    </div>
                </label>
            </div>

            <div id="naming_example_div">
                <h3>Single-EP Sample:</h3>
                <div class="example">
                    <span class="jumbo" id="naming_example">&nbsp;</span>
                </div>
                <br>
            </div>

            <div id="naming_example_multi_div">
                <h3>Multi-EP sample:</h3>
                <div class="example">
                    <span class="jumbo" id="naming_example_multi">&nbsp;</span>
                </div>
                <br>
            </div>

            <div class="row field-pair">
                <input type="checkbox" id="naming_strip_year"
                       name="naming_strip_year" ${('', 'checked')[bool(sickrage.srCore.srConfig.NAMING_STRIP_YEAR)]}/>
                <label for="naming_strip_year">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Strip Show Year</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Remove the TV show's year when
                        renaming the file?
                    </div>
                </label>
                <label class="nocheck">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">&nbsp;</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Only applies to shows that have
                        year inside parentheses
                    </div>
                </label>
            </div>

            <div class="row field-pair">
                <input type="checkbox" class="enabler" id="naming_custom_abd"
                       name="naming_custom_abd" ${('', 'checked')[bool(sickrage.srCore.srConfig.NAMING_CUSTOM_ABD)]}/>
                <label for="naming_custom_abd">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Custom Air-By-Date</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Name Air-By-Date shows differently
                        than regular shows?
                    </div>
                </label>
            </div>

            <div id="content_naming_custom_abd">
                <div class="row field-pair">
                    <label class="nocheck" for="name_abd_presets">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Name Pattern:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select id="name_abd_presets" class="form-control">
                                <% is_abd_custom = True %>
                                % for cur_preset in validator.name_abd_presets:
                                <% tmp = validator.test_name(cur_preset) %>
                                % if cur_preset == sickrage.srCore.srConfig.NAMING_ABD_PATTERN:
                                    <% is_abd_custom = False %>
                                % endif
                                    <option id="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NAMING_ABD_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                % endfor
                                <option id="${sickrage.srCore.srConfig.NAMING_ABD_PATTERN}" ${('', 'selected="selected"')[bool(is_abd_custom)]}>
                                    Custom...
                                </option>
                            </select>
                        </div>
                    </label>
                </div>

                <div id="naming_abd_custom">
                    <div class="row field-pair">
                        <label class="nocheck">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">
                                    &nbsp;
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="naming_abd_pattern" id="naming_abd_pattern"
                                       value="${sickrage.srCore.srConfig.NAMING_ABD_PATTERN}"
                                       class="form-control"/>
                                <img src="${srWebRoot}/images/legend16.png" width="16" height="16"
                                     alt="[Toggle Key]" id="show_naming_abd_key"
                                     title="Toggle ABD Naming Legend" class="legend"/>
                            </div>
                        </label>
                    </div>

                    <div id="naming_abd_key" class="nocheck" style="display: none;">
                        <table class="Key">
                            <thead>
                            <tr>
                                <th class="align-right">Meaning</th>
                                <th>Pattern</th>
                                <th width="60%">Result</th>
                            </tr>
                            </thead>
                            <tfoot>
                            <tr>
                                <th colspan="3">
                                    Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)
                                </th>
                            </tr>
                            </tfoot>
                            <tbody>
                            <tr>
                                <td class="align-right"><b>Show Name:</b></td>
                                <td>%SN</td>
                                <td>Show Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%S.N</td>
                                <td>Show.Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%S_N</td>
                                <td>Show_Name</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Regular Air Date:</b></td>
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
                                <td class="align-right"><b>Episode Name:</b></td>
                                <td>%EN</td>
                                <td>Episode Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%E.N</td>
                                <td>Episode.Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%E_N</td>
                                <td>Episode_Name</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Quality:</b></td>
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
                                <td class="align-right"><b>Year:</b></td>
                                <td>%Y</td>
                                <td>2010</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Month:</b></td>
                                <td>%M</td>
                                <td>3</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">&nbsp;</td>
                                <td>%0M</td>
                                <td>03</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Day:</b></td>
                                <td>%D</td>
                                <td>9</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">&nbsp;</td>
                                <td>%0D</td>
                                <td>09</td>
                            </tr>
                            <tr>
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="Multi-EP style is ignored"></i> <b>Release
                                    Name:</b></td>
                                <td>%RN</td>
                                <td>Show.Name.2010.03.09.HDTV.XviD-RLSGROUP</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                    <b>Release Group:</b></td>
                                <td>%RG</td>
                                <td>RLSGROUP</td>
                            </tr>
                            <tr>
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="If episode is proper/repack add 'proper' to name."></i>
                                    <b>Release Type:</b></td>
                                <td>%RT</td>
                                <td>PROPER</td>
                            </tr>
                            </tbody>
                        </table>
                        <br>
                    </div>
                </div><!-- /naming_abd_custom -->

                <div id="naming_abd_example_div">
                    <h3>Air-by-date Sample:</h3>
                    <div class="example">
                        <span class="jumbo" id="naming_abd_example">&nbsp;</span>
                    </div>
                    <br>
                </div>

            </div><!-- /naming_abd_different -->

            <div class="row field-pair">
                <input type="checkbox" class="enabler" id="naming_custom_sports"
                       name="naming_custom_sports" ${('', 'checked')[bool(sickrage.srCore.srConfig.NAMING_CUSTOM_SPORTS)]}/>
                <label for="naming_custom_sports">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Custom Sports</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Name Sports shows differently than
                        regular shows?
                    </div>
                </label>
            </div>

            <div id="content_naming_custom_sports">
                <div class="row field-pair">
                    <label class="nocheck" for="name_sports_presets">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Name Pattern:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select id="name_sports_presets" class="form-control">
                                <% is_sports_custom = True %>
                                % for cur_preset in validator.name_sports_presets:
                                <% tmp = validator.test_name(cur_preset) %>
                                % if cur_preset == sickrage.srCore.srConfig.NAMING_SPORTS_PATTERN:
                                    <% is_sports_custom = False %>
                                % endif
                                    <option id="${cur_preset}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.NAMING_SPORTS_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                % endfor
                                <option id="${sickrage.srCore.srConfig.NAMING_SPORTS_PATTERN}" ${('', 'selected="selected"')[bool(is_sports_custom)]}>
                                    Custom...
                                </option>
                            </select>
                        </div>
                    </label>
                </div>

                <div id="naming_sports_custom">
                    <div class="row field-pair" style="padding-top: 0;">
                        <label class="nocheck">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">
                                    &nbsp;
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="naming_sports_pattern" id="naming_sports_pattern"
                                       value="${sickrage.srCore.srConfig.NAMING_SPORTS_PATTERN}"
                                       class="form-control"/>
                                <img src="${srWebRoot}/images/legend16.png" width="16" height="16"
                                     alt="[Toggle Key]" id="show_naming_sports_key"
                                     title="Toggle Sports Naming Legend" class="legend"/>
                            </div>
                        </label>
                    </div>

                    <div id="naming_sports_key" class="nocheck" style="display: none;">
                        <table class="Key">
                            <thead>
                            <tr>
                                <th class="align-right">Meaning</th>
                                <th>Pattern</th>
                                <th width="60%">Result</th>
                            </tr>
                            </thead>
                            <tfoot>
                            <tr>
                                <th colspan="3">
                                    Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)
                                </th>
                            </tr>
                            </tfoot>
                            <tbody>
                            <tr>
                                <td class="align-right"><b>Show Name:</b></td>
                                <td>%SN</td>
                                <td>Show Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%S.N</td>
                                <td>Show.Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%S_N</td>
                                <td>Show_Name</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Sports Air Date:</b></td>
                                <td>%AD</td>
                                <td>9 Mar 2011</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%A.D</td>
                                <td>9.Mar.2011</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%A_D</td>
                                <td>9_Mar_2011</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%A-D</td>
                                <td>9-Mar-2011</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Episode Name:</b></td>
                                <td>%EN</td>
                                <td>Episode Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%E.N</td>
                                <td>Episode.Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%E_N</td>
                                <td>Episode_Name</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Quality:</b></td>
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
                                <td class="align-right"><b>Year:</b></td>
                                <td>%Y</td>
                                <td>2010</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Month:</b></td>
                                <td>%M</td>
                                <td>3</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">&nbsp;</td>
                                <td>%0M</td>
                                <td>03</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Day:</b></td>
                                <td>%D</td>
                                <td>9</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right">&nbsp;</td>
                                <td>%0D</td>
                                <td>09</td>
                            </tr>
                            <tr>
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="Multi-EP style is ignored"></i> <b>Release
                                    Name:</b></td>
                                <td>%RN</td>
                                <td>Show.Name.9th.Mar.2011.HDTV.XviD-RLSGROUP</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                    <b>Release Group:</b></td>
                                <td>%RG</td>
                                <td>RLSGROUP</td>
                            </tr>
                            <tr>
                                <td class="align-right">
                                    <i class="glyphicon glyphicon-info-sign"
                                       title="If episode is proper/repack add 'proper' to name.">

                                    </i>
                                    <b>Release Type:</b></td>
                                <td>%RT</td>
                                <td>PROPER</td>
                            </tr>
                            </tbody>
                        </table>
                        <br>
                    </div>
                </div><!-- /naming_sports_custom -->

                <div id="naming_sports_example_div">
                    <h3>Sports Sample:</h3>
                    <div class="example">
                        <span class="jumbo" id="naming_sports_example">&nbsp;</span>
                    </div>
                    <br>
                </div>

            </div><!-- /naming_sports_different -->

            <!-- naming_anime_custom -->
            <div class="row field-pair">
                <input type="checkbox" class="enabler" id="naming_custom_anime"
                       name="naming_custom_anime" ${('', 'checked')[bool(sickrage.srCore.srConfig.NAMING_CUSTOM_ANIME)]}/>
                <label for="naming_custom_anime">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Custom Anime</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Name Anime shows differently than
                        regular shows?
                    </div>
                </label>
            </div>

            <div id="content_naming_custom_anime">
                <div class="row field-pair">
                    <label class="nocheck" for="name_anime_presets">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Name Pattern:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select id="name_anime_presets" class="form-control">
                                <% is_anime_custom = True %>
                                % for cur_preset in validator.name_anime_presets:
                                <% tmp = validator.test_name(cur_preset) %>
                                % if cur_preset == sickrage.srCore.srConfig.NAMING_ANIME_PATTERN:
                                    <% is_anime_custom = False %>
                                % endif
                                    <option id="${cur_preset}" ${('', 'selected="selected"')[cur_preset == sickrage.srCore.srConfig.NAMING_ANIME_PATTERN]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                % endfor
                                <option id="${sickrage.srCore.srConfig.NAMING_ANIME_PATTERN}" ${('', 'selected="selected"')[bool(is_anime_custom)]}>
                                    Custom...
                                </option>
                            </select>
                        </div>
                    </label>
                </div>

                <div id="naming_anime_custom">
                    <div class="row field-pair" style="padding-top: 0;">
                        <label class="nocheck">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">
                                    &nbsp;
                                </label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input name="naming_anime_pattern" id="naming_anime_pattern"
                                       value="${sickrage.srCore.srConfig.NAMING_ANIME_PATTERN}"
                                       class="form-control"/>
                                <img src="${srWebRoot}/images/legend16.png" width="16" height="16"
                                     alt="[Toggle Key]" id="show_naming_anime_key"
                                     title="Toggle Anime Naming Legend" class="legend"/>
                            </div>
                        </label>
                    </div>

                    <div id="naming_anime_key" class="nocheck" style="display: none;">
                        <table class="Key">
                            <thead>
                            <tr>
                                <th class="align-right">Meaning</th>
                                <th>Pattern</th>
                                <th width="60%">Result</th>
                            </tr>
                            </thead>
                            <tfoot>
                            <tr>
                                <th colspan="3">
                                    Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)
                                </th>
                            </tr>
                            </tfoot>
                            <tbody>
                            <tr>
                                <td class="align-right"><b>Show Name:</b></td>
                                <td>%SN</td>
                                <td>Show Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%S.N</td>
                                <td>Show.Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%S_N</td>
                                <td>Show_Name</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Season Number:</b></td>
                                <td>%S</td>
                                <td>2</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0S</td>
                                <td>02</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>XEM Season Number:</b></td>
                                <td>%XMS</td>
                                <td>2</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0XMS</td>
                                <td>02</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Episode Number:</b></td>
                                <td>%E</td>
                                <td>3</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0E</td>
                                <td>03</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>XEM Episode Number:</b></td>
                                <td>%XME</td>
                                <td>3</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%0XME</td>
                                <td>03</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><b>Episode Name:</b></td>
                                <td>%EN</td>
                                <td>Episode Name</td>
                            </tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td>%E.N</td>
                                <td>Episode.Name</td>
                            </tr>
                            <tr class="even">
                                <td>&nbsp;</td>
                                <td>%E_N</td>
                                <td>Episode_Name</td>
                            </tr>
                            <tr>
                                <td class="align-right"><b>Quality:</b></td>
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
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="Multi-EP style is ignored"></i> <b>Release
                                    Name:</b></td>
                                <td>%RN</td>
                                <td>Show.Name.S02E03.HDTV.XviD-RLSGROUP</td>
                            </tr>
                            <tr>
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i>
                                    <b>Release Group:</b></td>
                                <td>%RG</td>
                                <td>RLSGROUP</td>
                            </tr>
                            <tr class="even">
                                <td class="align-right"><i class="glyphicon glyphicon-info-sign"
                                                           title="If episode is proper/repack add 'proper' to name."></i>
                                    <b>Release Type:</b></td>
                                <td>%RT</td>
                                <td>PROPER</td>
                            </tr>
                            </tbody>
                        </table>
                        <br>
                    </div>
                </div><!-- /naming_anime_custom -->

                <div class="row field-pair">
                    <label class="nocheck" for="naming_anime_multi_ep">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Multi-Episode Style:</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <select id="naming_anime_multi_ep" name="naming_anime_multi_ep"
                                    class="form-control">
                                % for cur_multi_ep in sorted(multiEpStrings.items(), key=lambda x: x[1]):
                                    <option value="${cur_multi_ep[0]}" ${('', 'selected="selected" class="selected"')[cur_multi_ep[0] == sickrage.srCore.srConfig.NAMING_ANIME_MULTI_EP]}>${cur_multi_ep[1]}</option>
                                % endfor
                            </select>
                        </div>
                    </label>
                </div>

                <div id="naming_example_anime_div">
                    <h3>Single-EP Anime Sample:</h3>
                    <div class="example">
                        <span class="jumbo" id="naming_example_anime">&nbsp;</span>
                    </div>
                    <br>
                </div>

                <div id="naming_example_multi_anime_div">
                    <h3>Multi-EP Anime sample:</h3>
                    <div class="example">
                        <span class="jumbo" id="naming_example_multi_anime">&nbsp;</span>
                    </div>
                    <br>
                </div>

                <div class="row field-pair">
                    <input type="radio" name="naming_anime" id="naming_anime"
                           value="1" ${('', 'checked')[sickrage.srCore.srConfig.NAMING_ANIME == 1]}/>
                    <label for="naming_anime">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Add Absolute Number</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Add the absolute number to the
                            season/episode format?
                        </div>
                    </label>
                    <label class="nocheck">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">&nbsp;</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Only applies to animes. (eg.
                            S15E45 - 310 vs S15E45)
                        </div>
                    </label>
                </div>

                <div class="row field-pair">
                    <input type="radio" name="naming_anime" id="naming_anime_only"
                           value="2" ${('', 'checked')[sickrage.srCore.srConfig.NAMING_ANIME == 2]}/>
                    <label for="naming_anime_only">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">Only Absolute Number</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Replace season/episode format
                            with absolute number
                        </div>
                    </label>
                    <label class="nocheck">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">&nbsp;</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Only applies to animes.</div>
                    </label>
                </div>

                <div class="row field-pair">
                    <input type="radio" name="naming_anime" id="naming_anime_none"
                           value="3" ${('', 'checked')[sickrage.srCore.srConfig.NAMING_ANIME == 3]}/>
                    <label for="naming_anime_none">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">No Absolute Number</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Dont include the absolute
                            number
                        </div>
                    </label>
                    <label class="nocheck">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">&nbsp;</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">Only applies to animes.</div>
                    </label>
                </div>

            </div><!-- /naming_anime_different -->

            <div></div>
            <input type="submit" class="btn config_submitter" value="Save Changes"/><br>

        </fieldset>
    </div><!-- /tab-pane2 //-->

    <div id="core-tab-pane3" class="tab-pane fade">

        <div class="tab-pane-desc">
            <h3>Metadata</h3>
            <p>The data associated to the data. These are files associated to a TV show in the form of
                images
                and text that, when supported, will enhance the viewing experience.</p>
        </div>

        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <label>
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <label class="component-title">Metadata Type:</label>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <% m_dict = sickrage.srCore.metadataProvidersDict %>
                        <select id="metadataType" class="form-control">
                            % for (cur_id, cur_generator) in sorted(m_dict.items()):
                                <option value="${cur_id}">${cur_generator.name}</option>
                            % endfor
                        </select>
                    </div>
                </label>
                <span>Toggle the metadata options that you wish to be created. <b>Multiple targets may be used.</b></span>
            </div>

            % for (cur_id, cur_generator) in m_dict.items():
                <div class="metadataDiv" id="${cur_id}">
                    <div>
                        <label for="${cur_id}_enabled"><input type="checkbox" class="metadata_checkbox"
                                                              id="${cur_id}_enabled" ${('', 'checked')[bool(cur_generator.enabled)]}/>&nbsp;Enabled</label>
                    </div>
                    <div class="metadata_options_wrapper">
                        <h4>Create:</h4>
                        <div class="metadata_options">
                            <label for="${cur_id}_show_metadata"><input type="checkbox"
                                                                        class="metadata_checkbox"
                                                                        id="${cur_id}_show_metadata" ${('', 'checked')[bool(cur_generator.show_metadata)]}/>&nbsp;Show
                                Metadata</label>
                            <label for="${cur_id}_episode_metadata"><input type="checkbox"
                                                                           class="metadata_checkbox"
                                                                           id="${cur_id}_episode_metadata" ${('', 'checked')[bool(cur_generator.episode_metadata)]}/>&nbsp;Episode
                                Metadata</label>
                            <label for="${cur_id}_fanart"><input type="checkbox"
                                                                 class="float-left metadata_checkbox"
                                                                 id="${cur_id}_fanart" ${('', 'checked')[bool(cur_generator.fanart)]}/>&nbsp;Show
                                Fanart</label>
                            <label for="${cur_id}_poster"><input type="checkbox"
                                                                 class="float-left metadata_checkbox"
                                                                 id="${cur_id}_poster" ${('', 'checked')[bool(cur_generator.poster)]}/>&nbsp;Show
                                Poster</label>
                            <label for="${cur_id}_banner"><input type="checkbox"
                                                                 class="float-left metadata_checkbox"
                                                                 id="${cur_id}_banner" ${('', 'checked')[bool(cur_generator.banner)]}/>&nbsp;Show
                                Banner</label>
                            <label for="${cur_id}_episode_thumbnails"><input type="checkbox"
                                                                             class="float-left metadata_checkbox"
                                                                             id="${cur_id}_episode_thumbnails" ${('', 'checked')[bool(cur_generator.episode_thumbnails)]}/>&nbsp;Episode
                                Thumbnails</label>
                            <label for="${cur_id}_season_posters"><input type="checkbox"
                                                                         class="float-left metadata_checkbox"
                                                                         id="${cur_id}_season_posters" ${('', 'checked')[bool(cur_generator.season_posters)]}/>&nbsp;Season
                                Posters</label>
                            <label for="${cur_id}_season_banners"><input type="checkbox"
                                                                         class="float-left metadata_checkbox"
                                                                         id="${cur_id}_season_banners" ${('', 'checked')[bool(cur_generator.season_banners)]}/>&nbsp;Season
                                Banners</label>
                            <label for="${cur_id}_season_all_poster"><input type="checkbox"
                                                                            class="float-left metadata_checkbox"
                                                                            id="${cur_id}_season_all_poster" ${('', 'checked')[bool(cur_generator.season_all_poster)]}/>&nbsp;Season
                                All Poster</label>
                            <label for="${cur_id}_season_all_banner"><input type="checkbox"
                                                                            class="float-left metadata_checkbox"
                                                                            id="${cur_id}_season_all_banner" ${('', 'checked')[bool(cur_generator.season_all_banner)]}/>&nbsp;Season
                                All Banner</label>
                        </div>
                    </div>
                    <div class="metadata_example_wrapper">
                        <h4>Results:</h4>
                        <div class="metadata_example panel panel-default">
                            <label for="${cur_id}_show_metadata"><span
                                    id="${cur_id}_eg_show_metadata">${cur_generator.eg_show_metadata}</span></label>
                            <label for="${cur_id}_episode_metadata"><span
                                    id="${cur_id}_eg_episode_metadata">${cur_generator.eg_episode_metadata}</span></label>
                            <label for="${cur_id}_fanart"><span
                                    id="${cur_id}_eg_fanart">${cur_generator.eg_fanart}</span></label>
                            <label for="${cur_id}_poster"><span
                                    id="${cur_id}_eg_poster">${cur_generator.eg_poster}</span></label>
                            <label for="${cur_id}_banner"><span
                                    id="${cur_id}_eg_banner">${cur_generator.eg_banner}</span></label>
                            <label for="${cur_id}_episode_thumbnails"><span
                                    id="${cur_id}_eg_episode_thumbnails">${cur_generator.eg_episode_thumbnails}</span></label>
                            <label for="${cur_id}_season_posters"><span
                                    id="${cur_id}_eg_season_posters">${cur_generator.eg_season_posters}</span></label>
                            <label for="${cur_id}_season_banners"><span
                                    id="${cur_id}_eg_season_banners">${cur_generator.eg_season_banners}</span></label>
                            <label for="${cur_id}_season_all_poster"><span
                                    id="${cur_id}_eg_season_all_poster">${cur_generator.eg_season_all_poster}</span></label>
                            <label for="${cur_id}_season_all_banner"><span
                                    id="${cur_id}_eg_season_all_banner">${cur_generator.eg_season_all_banner}</span></label>
                        </div>
                    </div>
                    <input type="hidden" name="${cur_id}_data" id="${cur_id}_data"
                           value="${cur_generator.get_config()}"/>
                </div>
            % endfor

            <div class="clearfix"></div>
            <br>

            <input type="submit" class="btn config_submitter" value="Save Changes"/><br>
        </fieldset>
    </div><!-- /tab-pane3 //-->
</%block>