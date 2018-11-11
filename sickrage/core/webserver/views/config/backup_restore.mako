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
                    <b>${_('Backup your main database file and config')}</b>
                </small>
            </div>

            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                <div class="form-row form-group">
                    <div class="col-md-12 component-desc">
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
                    <b>${_('Restore your main database file and config')}</b>
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
                                <label for="restore_database">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_database" id="restore_database" checked/>
                                    ${_('Restore database files')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_config">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_config" id="restore_config" checked/>
                                    ${_('Restore configuration file')}
                                </label>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="col-md-12">
                                <label for="restore_cache">
                                    <input type="checkbox" class="toggle color-primary is-material" name="restore_cache" id="restore_cache" checked/>
                                    ${_('Restore cache files')}
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
