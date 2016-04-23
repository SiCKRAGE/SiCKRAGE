<%inherit file="../layouts/main.mako"/>

<%!
    import datetime
    import locale

    import sickrage
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
    from sickrage.core.helpers.srdatetime import srDateTime, date_presets, time_presets
    from sickrage.metadata import GenericMetadata
%>

<%block name="content">

    <% indexer = 0 %>
    % if sickrage.srCore.srConfig.INDEXER_DEFAULT:
        <% indexer = sickrage.srCore.srConfig.INDEXER_DEFAULT %>
    % endif

    <div id="config">
        <div id="ui-content">
            <form name="configForm" method="post" action="backuprestore">
                <div id="ui-components">
                    <ul>
                        <li><a href="#core-component-group1">Backup</a></li>
                        <li><a href="#core-component-group2">Restore</a></li>
                    </ul>

                    <div id="core-component-group1" class="component-group clearfix">
                        <div class="component-group-desc">
                            <h3>Backup</h3>
                            <p><b>Backup your main database file and config</b></p>
                        </div>

                        <fieldset class="component-group-list">
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

                    </div><!-- /component-group1 //-->

                    <div id="core-component-group2" class="component-group clearfix">
                        <div class="component-group-desc">
                            <h3>Restore</h3>
                            <p><b>Restore your main database file and config</b></p>
                        </div>

                        <fieldset class="component-group-list">
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
                    </div><!-- /component-group2 //-->
                </div><!-- /ui-components -->
            </form>
        </div>
    </div>

    <div class="clearfix"></div>
</%block>
