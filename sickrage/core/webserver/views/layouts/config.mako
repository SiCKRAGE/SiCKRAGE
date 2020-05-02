<%inherit file="main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <form id="configForm" action="${self.formaction()}" method="post" novalidate>
                <div class="card">
                    <div class="card-header">
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
                    <div class="card-footer">
                        <div class="float-left">
                            <button type="submit" class="btn config_submitter">${_('Save Changes')}</button>
                            <input type="button" href="/config/reset"
                                   class="btn resetConfig" value="${_('Reset to Defaults')}"/>
                        </div>
                        <div class="float-right">
                            <h6 class="text-right">
                                <b>
                                    <small class="text-warning">
                                        ${_('All non-absolute folder locations are relative to')} ${sickrage.app.data_dir}
                                    </small>
                                </b>
                            </h6>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    </div>
</%block>