<%inherit file="../layouts/config.mako"/>
<%def name='formaction()'><% return 'saveQualities' %></%def>
<%!
    import sickrage
    from sickrage.core.common import Qualities
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
                    ${_('Settings represent minimum and maximum size allowed per episode video file.')}
                </small>
            </div>
            <fieldset class="col-lg-9 col-md-8 col-sm-8 card-text">
                % for quality in sickrage.app.config.quality_sizes.keys():
                    % if quality:
                        <div class="form-row form-group">
                            <div class="col-lg-3 col-md-4 col-sm-5">
                                <label class="component-title">${renderQualityPill(Qualities[quality])}</label>
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
                                           value="${sickrage.app.config.quality_sizes[quality].min_size}"
                                           name="${quality}_min"
                                           id="${quality}_min"
                                           min="0"
                                           title="Specify minimum quality size allowed in MB">
                                    <div class="input-group-append">
                                        <span class="input-group-text">
                                            MB Min
                                        </span>
                                    </div>
                                    <input class="form-control"
                                           type="number"
                                           value="${sickrage.app.config.quality_sizes[quality].max_size}"
                                           name="${quality}_max"
                                           id="${quality}_max"
                                           min="0"
                                           title="Specify maximum quality size allowed in MB">
                                    <div class="input-group-append">
                                        <span class="input-group-text">
                                            MB Max
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
