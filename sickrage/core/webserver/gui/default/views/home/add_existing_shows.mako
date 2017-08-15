<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-md-12">
            <h1 class="title">${title}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div id="newShowPortal">
                <ul class="nav nav-tabs">
                    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Add Existing Show</a></li>
                </ul>
                <div class="tab-content">
                    <div id="core-tab-pane1" class="tab-pane fade in active">
                        <div class="row tab-pane">
                            <form id="addShowForm" method="post" action="${srWebRoot}/home/addShows/addExistingShows"
                                  accept-charset="utf-8">

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

                                <div class="row">
                                    <div class="col-md-12">
                                        <p>SiCKRAGE can add existing shows, using the current options, by using locally
                                            stored NFO/XML metadata to eliminate user interaction. If you would rather
                                            have SickRage prompt you to customize each show, then use the checkbox
                                            below.
                                        </p>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <p>
                                            <input type="checkbox" name="promptForSettings" id="promptForSettings"/>
                                            <label for="promptForSettings">
                                                Prompt me to set settings for each show
                                            </label>
                                        </p>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <p>
                                            <b>
                                                Displaying folders within these directories which aren't already added
                                                to SiCKRAGE:
                                            </b>
                                        </p>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <ul id="rootDirStaticList"></ul>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div id="tableDiv"></div>
                                    </div>
                                </div>
                                <br/>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn btn-primary" type="button" value="Submit"
                                               id="submitShowDirs"/>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
