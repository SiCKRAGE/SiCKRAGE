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
                    <ul class="nav nav-tabs" id="config-tabs">
                            <%block name="tabs"/>
                    </ul>
                    <div id="config">
                        <div class="tab-content">
                                <%block name="pages"/>
                        </div>
                    </div>
                </form>
            </div>
            <br/>
            <div class="row">
                <%block name="saveButton">
                    <div class="col-lg-2 col-md-2 col-sm-2 col-xs-12">
                        <input type="button" onclick="$('#configForm').submit()"
                               class="btn pull-left config_submitter button" value="Save Changes"/>
                    </div>
                </%block>
                <div class="col-lg-10 col-md-10 col-sm-10 col-xs-12 pull-right">
                    <h6 class="pull-right">
                        <b>
                            <span class="config-path-title">All non-absolute folder locations are relative to
                                &nbsp;</span>
                            <span class="path pull-right">${sickrage.DATA_DIR}</span>
                        </b>
                    </h6>
                </div>
            </div>
        </div>
    </div>
</%block>