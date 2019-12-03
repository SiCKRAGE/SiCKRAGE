<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveQualities' %></%def>
<%!
    import sickrage
    from sickrage.core.common import Quality
%>

<%block name="menus">
    <li class="nav-item px-1"><a class="nav-link" data-toggle="tab" href="#quality-sizes">${_('Quality Sizes')}</a>
    </li>
</%block>

<%block name="pages">
    <%namespace file="../includes/quality_defaults.mako" import="renderQualityPill"/>
    <div id="quality-sizes" class="tab-pane active">
        <div class="form-row">
            <div class="col-lg-3 col-md-4 col-sm-4 card-title">
                <h3>${_('Quality Sizes')}</h3>
                <small class="form-text text-muted">
                    ${_('Use default qualitiy sizes or specify custom ones per quality definition.')}<br/>
                    ${_('Settings represent maximum size allowed per episode video file.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                % for qtype in Quality.qualitySizes.keys():
                    % if qtype:
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${renderQualityPill(qtype)}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 component-desc">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-file"></span>
                                        </span>
                                    </div>
                                    <input class="form-control"
                                           type="number"
                                           % if qtype in sickrage.app.config.quality_sizes:
                                             value="${sickrage.app.config.quality_sizes[qtype]}"
                                           % else:
                                               value="${Quality.qualitySizes[qtype]}"
                                           % endif
                                           name="${qtype}"
                                           id="${qtype}"
                                           min="1"
                                           title="Specify max quality size allowed in MB">
                                    <div class="input-group-append">
                                        <span class="input-group-text">
                                            MB
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    % endif
                % endfor

                <div class="form-row">
                    <div class="col-md-12">
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                    </div>
                </div>

            </fieldset>
        </div>
    </div><!-- /tab-pane1 //-->
</%block>
