<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div id="newShowPortal">
        <form id="addShowForm" method="post" action="${srWebRoot}/home/addShows/addExistingShows"
              accept-charset="utf-8">

            <div id="tabs">
                <ul>
                    <li><a href="#tabs-1">${_('Manage Directories')}</a></li>
                    <li><a href="#tabs-2">${_('Customize Options')}</a></li>
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
                    <p>
                        ${_('SiCKRAGE can add existing shows, using the current options, by using '
                        'locally stored NFO/XML metadata to eliminate user interaction. If you '
                        'would rather have SickRage prompt you to customize each show, then use '
                        'the checkbox below.')}
                    </p>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    <p>
                        <input type="checkbox" name="promptForSettings" id="promptForSettings"/>
                        <label for="promptForSettings">
                            ${_('Prompt me to set settings for each show')}
                        </label>
                    </p>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    <p>
                        <b>
                            ${_('Displaying folders within these directories which aren\'t already '
                            'added to SiCKRAGE:')}
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
                    <input class="btn btn-primary" type="button" value="${_('Submit')}"
                           id="submitShowDirs"/>
                </div>
            </div>
        </form>
    </div>
</%block>
