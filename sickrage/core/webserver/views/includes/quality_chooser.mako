<%!
    import sickrage
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings
%>

<%def name="QualityChooser(anyQualities=None, bestQualities=None)">
    <%
        if not anyQualities and not bestQualities:
            anyQualities, bestQualities = Quality.splitQuality(sickrage.app.config.quality_default)

        overall_quality = Quality.combineQualities(anyQualities, bestQualities)
    %>

    <div class="row">
        <div class="col-md-12">
            <div class="input-group input350">
                <div class="input-group-addon">
                    <span class="glyphicon glyphicon-sunglasses"></span>
                </div>
                <select id="qualityPreset" name="quality_preset" class="form-control" title="qualityPreset">
                    <option value="0">Custom</option>
                    % for curPreset in qualityPresets:
                        <option value="${curPreset}" ${('', 'selected="selected"')[curPreset == overall_quality]} ${('', 'style="padding-left: 15px;"')[qualityPresetStrings[curPreset].endswith("0p")]}>${qualityPresetStrings[curPreset]}</option>
                    % endfor
                </select>
            </div>
            <div id="qualityPreset_label">
                <label for="qualityPreset">
                    <p>${_('Preferred qualities replace existing downloads till highest quality is met')}</p>
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

                <div style="padding-right: 40px; text-align: left; float: left;">
                    <h5>${_('Allowed')}</h5>
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-sunglasses"></span>
                        </div>
                        <% anyQualityList = filter(lambda x: x > Quality.NONE, Quality.qualityStrings) %>
                        <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}"
                                class="form-control form-control-inline input-sm" title="anyQualities">
                            % for curQuality in sorted(anyQualityList):
                                <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${Quality.qualityStrings[curQuality]}</option>
                            % endfor
                        </select>
                    </div>
                </div>

                <div style="text-align: left; float: left;">
                    <h5>${_('Preferred')}</h5>
                    <div class="input-group input350">
                        <div class="input-group-addon">
                            <span class="glyphicon glyphicon-sunglasses"></span>
                        </div>
                        <% bestQualityList = filter(lambda x: Quality.SDTV <= x < Quality.UNKNOWN, Quality.qualityStrings) %>
                        <select id="bestQualities" name="bestQualities" multiple="multiple"
                                size="${len(bestQualityList)}" class="form-control form-control-inline input-sm"
                                title="bestQualities">
                            % for curQuality in sorted(bestQualityList):
                                <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${Quality.qualityStrings[curQuality]}</option>
                            % endfor
                        </select>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%def>