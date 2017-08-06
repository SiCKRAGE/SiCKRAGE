<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'backuprestore' %></%def>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Backup</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Restore</a></li>
</%block>
<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active clearfix">
        <div class="tab-pane-desc">
            <h3>Backup</h3>
            <p><b>Backup your main database file and config</b></p>
        </div>

        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Backup folder</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="input-group">
                                <input name="backupDir" id="backupDir"
                                       class="form-control" autocapitalize="off"/>
                                <div class="input-group-addon">
                                    <a href="#" class="glyphicon glyphicon-floppy-save" id="Backup"></a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <label for="backupDir">Select the folder you wish to save your backup file to</label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="Backup" id="Backup-result"></div>
        </fieldset>

    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="tab-pane fade clearfix">
        <div class="tab-pane-desc">
            <h3>Restore</h3>
            <p><b>Restore your main database file and config</b></p>
        </div>
        <fieldset class="tab-pane-list">
            <div class="row field-pair">
                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                    <label class="component-title">Backup file</label>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="input-group">
                                <input name="backupFile" id="backupFile"
                                       class="form-control" autocapitalize="off"/>
                                <div class="input-group-addon">
                                    <a href="#" class="glyphicon glyphicon-floppy-open" id="Restore"></a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <label for="backupFile">Select the backup file you wish to restore</label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="Restore" id="Restore-result"></div>
        </fieldset>
    </div><!-- /tab-pane2 //-->
</%block>
