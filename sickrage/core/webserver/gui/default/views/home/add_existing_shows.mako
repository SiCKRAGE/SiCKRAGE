<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">

    <div id="newShowPortal">
        <div id="ui-components">
            <ul>
                <li><a href="#core-component-group1">Add Existing Show</a></li>
            </ul>

            <div id="core-component-group1" class="tab-pane active component-group">

                <form id="addShowForm" method="post" action="/home/addShows/addNewShow" accept-charset="utf-8">

                    <div id="tabs">
                        <ul>
                            <li><a href="#tabs-1">Manage Directories</a></li>
                            <li><a href="#tabs-2">Customize Options</a></li>
                        </ul>
                        <div id="tabs-1" class="existingtabs">
                                <%include file="../includes/root_dirs.mako"/>
                        </div>
                        <div id="tabs-2" class="existingtabs">
                                <%include file="../includes/add_show_options.mako"/>
                        </div>
                    </div>
                    <br>

                    <p>SiCKRAGE can add existing shows, using the current options, by using locally stored NFO/XML
                        metadata to eliminate user interaction.
                        If you would rather have SickRage prompt you to customize each show, then use the checkbox
                        below.</p>

                    <p><input type="checkbox" name="promptForSettings" id="promptForSettings"/> <label
                            for="promptForSettings">Prompt me to set settings for each show</label></p>

                    <hr/>

                    <p><b>Displaying folders within these directories which aren't already added to SiCKRAGE:</b></p>

                    <ul id="rootDirStaticList">
                        <li></li>
                    </ul>
                    <br>
                    <div id="tableDiv"></div>
                    <br>
                    <br>
                    <input class="btn btn-primary" type="button" value="Submit" id="submitShowDirs"/>

                </form>

            </div>
        </div>
    </div>
</%block>
