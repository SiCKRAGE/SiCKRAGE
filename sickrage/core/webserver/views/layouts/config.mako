<%inherit file="main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col mx-auto text-center">
            <h1 class="title">${title}</h1>
            <hr class="bg-light"/>
        </div>
    </div>
    <div class="row">
        <div class="col-md-6 mx-auto">
            <div id="config-components">
                <form id="configForm" action="${self.formaction()}" method="post">
                    <div class="card bg-dark">
                        <div class="card-header bg-secondary">
                            <ul class="nav nav-pills card-header-pills" id="config-tabs">
                                    <%block name="tabs"/>
                            </ul>
                        </div>
                        <div id="config">
                            <div class="card-body tab-content">
                                    <%block name="pages"/>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-2 col-md-2 col-sm-2 col-xs-12 pull-left">
                    <input type="button" onclick="$('#configForm').submit()"
                           class="btn btn-secondary config_submitter button" value="${_('Save Changes')}"/>
                    <input type="button" href="/config/reset"
                           class="btn resetConfig button" value="${_('Reset to Defaults')}"/>
                </div>
                <div class="col-lg-10 col-md-10 col-sm-10 col-xs-12 pull-right">
                    <h6 class="pull-right">
                        <b><span class="small">
                            ${_('All non-absolute folder locations are relative to')} ${sickrage.app.data_dir}
                        </span></b>
                    </h6>
                </div>
            </div>
        </div>
    </div>
</%block>