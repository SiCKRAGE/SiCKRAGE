<%!
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
%>
<%def name="renderQualityPill(quality)">
    % if quality in qualityPresets:
        <span class="quality ${qualityPresetStrings[quality]}">${qualityPresetStrings[quality]}</span>
    % elif quality in Quality.combinedQualityStrings:
        <span class="quality ${Quality.cssClassStrings[quality]}">${Quality.combinedQualityStrings[quality]}</span>
    % elif quality in Quality.qualityStrings:
        <span class="quality ${Quality.cssClassStrings[quality]}">${Quality.qualityStrings[quality]}</span>
    % else:
        <span class="quality Custom">Custom</span>
    % endif
</%def>
