<%!
    import sickrage
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings
%>

<%
    selected = None
    qualities = Quality.splitQuality(sickrage.srCore.srConfig.QUALITY_DEFAULT)

    anyQualities = qualities[0]
    anyQualityList = filter(lambda x: x > Quality.NONE, Quality.qualityStrings)

    bestQualities = qualities[1]
    bestQualityList = filter(lambda x: Quality.SDTV <= x < Quality.UNKNOWN, Quality.qualityStrings)

    overall_quality = Quality.combineQualities(anyQualities, bestQualities)
%>

<div class="row">
    <div class="col-md-12">
        <div class="input-group input350">
            <div class="input-group-addon">
                <span class="glyphicon glyphicon-sunglasses"></span>
            </div>
            <select id="qualityPreset" name="quality_preset" class="form-control" title="Quality Presets">
                <option value="0">Custom</option>
                % for curPreset in sorted(qualityPresets):
                    <option value="${curPreset}" ${('', 'selected="selected"')[curPreset == overall_quality]} ${('', 'style="padding-left: 15px;"')[qualityPresetStrings[curPreset].endswith("0p")]}>${qualityPresetStrings[curPreset]}</option>
                % endfor
            </select>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12">
        <div id="customQuality" style="padding-left: 0;">
            <p>
                <b style="text-decoration: underline;">Preferred</b> qualities will replace those in
                <b style="text-decoration: underline;">Allowed</b>, even if they are lower.
            </p>

            <div style="padding-right: 40px; text-align: left; float: left;">
                <h5>Allowed</h5>
                <div class="input-group input350">
                    <div class="input-group-addon">
                        <span class="glyphicon glyphicon-sunglasses"></span>
                    </div>
                    <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}"
                            title="Allowed Qualities"
                            class="form-control">
                        % for curQuality in sorted(anyQualityList):
                            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${Quality.qualityStrings[curQuality]}</option>
                        % endfor
                    </select>
                </div>
            </div>

            <div style="text-align: left; float: left;">
                <h5>Preferred</h5>
                <div class="input-group input350">
                    <div class="input-group-addon">
                        <span class="glyphicon glyphicon-sunglasses"></span>
                    </div>
                    <select id="bestQualities" name="bestQualities" multiple="multiple"
                            size="${len(bestQualityList)}" title="Preferred Qualities"
                            class="form-control">
                        % for curQuality in sorted(bestQualityList):
                            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${Quality.qualityStrings[curQuality]}</option>
                        % endfor
                    </select>
                </div>
            </div>
        </div>
    </div>
</div>
