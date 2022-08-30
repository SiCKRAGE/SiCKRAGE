<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveBackupRestore' %></%def>
<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#backup">${_('Backup')}</a></li>
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#restore">${_('Restore')}</a></li>
</%block>
<%block name="pages">
    <div id="backup" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Backup')}</h3>
                <small class="form-text text-muted">
                    <b>${_('Backup SiCKRAGE')}</b>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-md-12 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <input name="backupDir" id="backupDir" class="form-control"
                                           placeholder="${_('Select the folder you wish to save your backup file to')}"
                                           autocapitalize="off"/>
                                    <div class="input-group-append">
                                      <span class="input-group-text">
                                        <a href="#" class="fas fa-download" title="${_('Backup')}" id="Backup"></a>
                                      </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <br/>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="auto_backup">
                                    <input type="checkbox" class="toggle color-primary is-material" name="auto_backup" id="auto_backup" checked/>
                                    ${_('Automatic Backups')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="col-md-12">
                        <div class="Backup" id="Backup-result"></div>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->

    <div id="restore" class="tab-pane">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Restore')}</h3>
                <small class="form-text text-muted">
                    <b>${_('Restore SiCKRAGE')}</b>
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-md-12 component-desc">
                        <div class="form-row">
                            <div class="col-md-12">
                                <div class="input-group">
                                    <input name="backupFile" id="backupFile"
                                           placeholder="${_('Select the backup file you wish to restore')}"
                                           class="form-control" autocapitalize="off"/>
                                    <div class="input-group-append">
                                    <span class="input-group-text">
                                        <a href="#" class="fas fa-upload" title="${_('Restore')}" id="Restore"></a>
                                    </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <br/>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_main_database">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_main_database" id="restore_main_database" checked/>
                                    ${_('Restore main database file')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_config_database">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_config_database" id="restore_config_database" checked/>
                                    ${_('Restore config database file')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_cache_database">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_cache_database" id="restore_cache_database" checked/>
                                    ${_('Restore cache database file')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_image_cache">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_image_cache" id="restore_image_cache" checked/>
                                    ${_('Restore image cache files')}
                                </label>
                                <div class="checkbox"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="col-md-12">
                        <div class="Restore" id="Restore-result"></div>
                    </div>
                </div>
            </fieldset>
        </div>
    </div><!-- /tab-pane2 //-->
</%block>
