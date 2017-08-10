<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveQualities' %></%def>
<%!
    import sickrage
%>

<%block name="tabs">
    <li class="active"><a data-toggle="tab" href="#core-tab-pane1">Quality Sizes</a></li>
</%block>

<%block name="pages">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
    <div id="core-tab-pane1" class="tab-pane fade in active">
        <div class="tab-pane-desc">
            <h3>Quality Sizes</h3>
            <p>Use default qualitiy sizes or specify custom ones per quality definition.</p>
            <div>
                <p class="note"> Settings represent maximum size allowed per episode video file.</p>
            </div>
        </div>
        <fieldset class="tab-pane-list">

            % for qtype, qsize in sickrage.srCore.srConfig.QUALITY_SIZES.items():
                % if qsize:
                    <div class="row field-pair">
                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                            <label class="component-title">${renderQualityPill(qtype)}</label>
                        </div>
                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                            <div class="input-group input350">
                                <div class="input-group-addon">
                                    <span class="glyphicon glyphicon-file"></span>
                                </div>
                                <input class="form-control"
                                       type="number"
                                       value="${qsize}"
                                       name="${qtype}"
                                       id="${qtype}"
                                       min="1"
                                       title="Specify minimum quality size allowed in MB">
                                <div class="input-group-addon">
                                    MB
                                </div>
                            </div>
                        </div>
                    </div>
                % endif
            % endfor

            <div class="row">
                <div class="col-md-12">
                    <input type="submit" class="btn config_submitter" value="Save Changes"/>
                </div>
            </div>

        </fieldset>
    </div><!-- /tab-pane1 //-->
</%block>
