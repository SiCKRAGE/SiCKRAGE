<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <form id="addShowForm" method="post" action="${srWebRoot}/home/addShows/addExistingShows"
                  accept-charset="utf-8">
                <div class="card">
                    <div class="card-header">
                        <h3>${title}</h3>
                    </div>
                    <div class="card-body">
                        <div class="card bg-transparent mb-3">
                            <div class="card-header">
                                <ul class="nav nav-pills card-header-pills">
                                    <li class="nav-item px-1">
                                        <a class="nav-link active"
                                           data-toggle="tab"
                                           href="#manage">
                                            ${_('Manage Directories')}
                                        </a>
                                    </li>
                                    <li class="nav-item px-1">
                                        <a class="nav-link"
                                           data-toggle="tab"
                                           href="#customize">
                                            ${_('Customize Options')}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                            <div class="card-body tab-content">
                                <div id="manage" class="tab-pane active">
                                        <%include file="../includes/root_dirs.mako"/>
                                </div>
                                <div id="customize" class="tab-pane">
                                        <%include file="../includes/add_show_options.mako"/>
                                </div>
                            </div>
                        </div>

                        <div class="card bg-transparent mb-3">
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-12">
                                        <p>
                                            ${_('SiCKRAGE can add existing shows, using the current options, by using '
                                            'locally stored NFO/XML metadata to eliminate user interaction. If you '
                                            'would rather have SiCKRAGE prompt you to customize each show, then use '
                                            'the checkbox below.')}
                                        </p>
                                        <label>
                                            <input type="checkbox" class="toggle color-primary is-material" name="promptForSettings" id="promptForSettings"/>
                                            ${_('Prompt me to set settings for each show')}
                                        </label>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="list-group" id="rootDirStaticList"></div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div id="tableDiv"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                    <div class="card-footer">
                        <input class="btn btn-primary" type="button" value="${_('Submit')}"
                               id="submitShowDirs"/>
                    </div>
                </div>
            </form>
        </div>
    </div>
</%block>
