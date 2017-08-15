<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'backuprestore' %></%def>
<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Backup</a></li>
    <li><a data-toggle="tab" href="#core-tab-pane2">Restore</a></li>
</%block>
<%block name="pages">
    <div id="core-tab-pane1" class="tab-pane fade in active clearfix">
        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
            <h3>Backup</h3>
            <p><b>Backup your main database file and config</b></p>
        </div>

        <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
            <div class="row field-pair">
                <div class="col-md-12 component-desc">
                    <div class="input-group input350">
                        <input name="backupDir" id="backupDir" class="form-control"
                               placeholder="Select the folder you wish to save your backup file to"
                               autocapitalize="off"/>
                        <div class="input-group-addon">
                            <a href="#" class="fa fa-download" title="Backup" id="Backup"></a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="Backup" id="Backup-result"></div>
                </div>
            </div>
        </fieldset>
    </div><!-- /tab-pane1 //-->

    <div id="core-tab-pane2" class="tab-pane fade clearfix">
        <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12 tab-pane-desc">
            <h3>Restore</h3>
            <p><b>Restore your main database file and config</b></p>
        </div>
        <fieldset class="col-lg-9 col-md-8 col-sm-8 col-xs-12 tab-pane-list">
            <div class="row field-pair">
                <div class="col-md-12 component-desc">
                    <div class="input-group input350">
                        <input name="backupFile" id="backupFile"
                               placeholder="Select the backup file you wish to restore"
                               class="form-control" autocapitalize="off"/>
                        <div class="input-group-addon">
                            <a href="#" class="fa fa-upload" title="Restore" id="Restore"></a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="Restore" id="Restore-result"></div>
                </div>
            </div>
        </fieldset>
    </div><!-- /tab-pane2 //-->
</%block>
