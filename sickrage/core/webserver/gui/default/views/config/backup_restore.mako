<%inherit file="../layouts/main.mako"/>

<%block name="content">
    <div id="config">
        <form name="configForm" method="post" action="backuprestore">
            <ul class="nav nav-tabs">
                <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Backup</a></li>
                <li><a data-toggle="tab" href="#core-tab-pane2">Restore</a></li>
            </ul>

            <div class="tab-content">
                <div id="core-tab-pane1" class="tab-pane fade in active clearfix">
                    <div class="tab-pane-desc">
                        <h3>Backup</h3>
                        <p><b>Backup your main database file and config</b></p>
                    </div>

                    <fieldset class="tab-pane-list">
                        <div class="field-pair">
                            Select the folder you wish to save your backup file to:

                            <br><br>

                            <input type="text" name="backupDir" id="backupDir"
                                   class="form-control input-sm input350" autocapitalize="off"/>
                            <input class="btn btn-inline" type="button" value="Backup" id="Backup"/>

                            <br>

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
                        <div class="field-pair">
                            Select the backup file you wish to restore:

                            <br><br>

                            <input type="text" name="backupFile" id="backupFile"
                                   class="form-control input-sm input350" autocapitalize="off"/>
                            <input class="btn btn-inline" type="button" value="Restore" id="Restore"/>

                            <br>

                        </div>
                        <div class="Restore" id="Restore-result"></div>
                    </fieldset>
                </div><!-- /tab-pane2 //-->
            </div>
        </form>
    </div>
</%block>
