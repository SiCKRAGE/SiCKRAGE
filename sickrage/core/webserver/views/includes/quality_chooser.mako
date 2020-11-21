<%!
    import sickrage
    from sickrage.core.common import Quality, Qualities
%>

<%def name="QualityChooser(anyQualities=None, bestQualities=None)">
    <%
        if not anyQualities and not bestQualities:
            anyQualities, bestQualities = Quality.split_quality(sickrage.app.config.general.quality_default)

        overall_quality = Quality.combine_qualities(anyQualities, bestQualities)
    %>

    <div class="row">
        <div class="col-md-12">
            <div class="input-group">
                <div class="input-group-prepend">
                    <span class="input-group-text">
                        <span class="fas fa-glasses"></span>
                    </span>
                </div>
                <select id="qualityPreset" name="quality_preset" class="form-control" title="qualityPreset">
                    <option value="0">Custom</option>
                    % for item in [x for x in Qualities if x.is_preset]:
                        <option value="${item.name}" ${('', 'selected="selected"')[item == overall_quality]} ${('', 'style="padding-left: 15px;"')[item.display_name.endswith("0P")]}>${item.display_name}</option>
                    % endfor
                </select>
            </div>
            <div id="qualityPreset_label">
                <label class="text-info" for="qualityPreset">
                    ${_('Preferred qualities replace existing downloads till highest quality is met')}
                </label>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-md-12">
            <div id="customQuality" style="padding-left: 0;">
                <p>
                    <b style="text-decoration: underline;">${_('Preferred')}</b> ${_('qualities will replace those in')}
                    <b style="text-decoration: underline;">${_('Allowed')}</b>, ${_('even if they are lower.')}
                </p>

                <div class="float-left mx-1">
                    <h5>${_('Allowed')}</h5>
                    <div class="input-group">
                        <div class="input-group-prepend">
                            <span class="input-group-text">
                                <span class="fas fa-glasses"></span>
                            </span>
                        </div>
                        <% anyQualityList = list(filter(lambda x: x > Qualities.NONE, [x for x in Qualities if not x.is_preset])) %>
                        <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}"
                                class="form-control form-control-inline input-sm" title="anyQualities">
                            % for item in sorted(anyQualityList):
                                <option value="${item.name}" ${('', 'selected="selected"')[item in anyQualities]}>${item.display_name}</option>
                            % endfor
                        </select>
                    </div>
                </div>

                <div class="float-left">
                    <h5>${_('Preferred')}</h5>
                    <div class="input-group">
                        <div class="input-group-prepend">
                            <span class="input-group-text">
                                <span class="fas fa-glasses"></span>
                            </span>
                        </div>
                        <% bestQualityList = list(filter(lambda x: Qualities.SDTV <= x < Qualities.UNKNOWN, [x for x in Qualities if not x.is_preset])) %>
                        <select id="bestQualities" name="bestQualities" multiple="multiple"
                                size="${len(bestQualityList)}" class="form-control form-control-inline"
                                title="bestQualities">
                            % for item in sorted(bestQualityList):
                                <option value="${item.name}" ${('', 'selected="selected"')[item in bestQualities]}>${item.display_name}</option>
                            % endfor
                        </select>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%def>