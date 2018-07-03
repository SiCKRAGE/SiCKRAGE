<%inherit file="main.mako"/>
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
            <div id="config-components">
                <form id="configForm" action="${self.formaction()}" method="post">
                    <div class="card ">
                        <div class="card-header">
                            <ul class="nav nav-tabs card-header-tabs" id="config-tabs">
                                    <%block name="tabs"/>
                            </ul>
                            <div id="config">
                                <div class="card-body">
                                    <div class="card-text">
                                        <%block name="pages"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-2 col-md-2 col-sm-2 col-xs-12">
                    <input type="button" onclick="$('#configForm').submit()"
                           class="btn pull-left config_submitter button" value="${_('Save Changes')}"/>
                    <a type="button" href="/config/reset" class="btn pull-left resetConfig button">
                        ${_('Reset to Defaults')}
                    </a>
                </div>
                <div class="col-lg-10 col-md-10 col-sm-10 col-xs-12 pull-right">
                    <h6 class="pull-right">
                        <b>
                            <span class="config-path-title">
                                ${_('All non-absolute folder locations are relative to')}
                                <span style="white-space:pre" class="path pull-right">${sickrage.app.data_dir}</span>
                            </span>
                        </b>
                    </h6>
                </div>
            </div>
        </div>
    </div>
</%block>