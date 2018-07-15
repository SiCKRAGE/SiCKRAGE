<%inherit file="main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-md-6 mx-auto">
            <div id="config-components">
                <form id="configForm" action="${self.formaction()}" method="post">
                    <div class="card bg-dark">
                        <div class="card-header bg-secondary">
                            <h3 class="float-md-left"><i class="fas fa-wrench"></i> ${title}</h3>
                            <ul class="nav nav-pills card-header-pills float-md-right" id="config-menus">
                                    <%block name="menus"/>
                            </ul>
                        </div>
                        <div id="config">
                            <div class="card-body tab-content">
                                    <%block name="pages"/>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-auto text-left py-1">
                                <input type="submit"
                                       class="btn btn-secondary config_submitter" value="${_('Save Changes')}"/>
                        </div>
                        <div class="col-auto text-left py-1">
                                <input type="button" href="/config/reset"
                                       class="btn btn-secondary resetConfig" value="${_('Reset to Defaults')}"/>
                        </div>
                        <div class="col pull-right">
                            <h6 class="text-right">
                                <b><span class="small">
                                    ${_('All non-absolute folder locations are relative to')} ${sickrage.app.data_dir}
                                </span></b>
                            </h6>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>