<%!
    import html
    import sickrage
    from sickrage.core.common import Quality, qualityPresets, qualityPresetStrings
%>
<%def name="renderQualityPill(quality, showTitle=False, overrideClass=None)">
    <%
        # Build a string of quality names to use as title attribute
        if showTitle:
            iQuality, pQuality = Quality.split_quality(quality)
            title = _('Initial Quality:') + '\n'
            if iQuality:
                for curQual in iQuality:
                    title += "  " + Quality.qualityStrings[curQual] + "\n"
            else:
                title += "  None\n"
            title += "\n" + _("Preferred Quality:") + "\n"
            if pQuality:
                for curQual in pQuality:
                    title += "  " + Quality.qualityStrings[curQual] + "\n"
            else:
                title += "  None\n"
            title = ' title="' + html.escape(title.rstrip(), True) + '"'
        else:
            title = ""

        iQuality = quality & 0xFFFF
        pQuality = quality >> 16

        # If initial and preferred qualities are the same, show pill as initial quality
        if iQuality == pQuality:
            quality = iQuality

        if quality in qualityPresets:
            cssClass = qualityPresetStrings[quality]
            qualityString = qualityPresetStrings[quality]
        elif quality in Quality.combinedQualityStrings:
            cssClass = Quality.cssClassStrings[quality]
            qualityString = Quality.combinedQualityStrings[quality]
        elif quality in Quality.qualityStrings:
            cssClass = Quality.cssClassStrings[quality]
            qualityString = Quality.qualityStrings[quality]
        else:
            cssClass = "Custom"
            qualityString = "Custom"

        cssClass = "badge p-1 align-middle text-white " + cssClass
        if overrideClass:
            cssClass = overrideClass
    %>
    <span ${title} class="${cssClass}">${qualityString}</span>
</%def>
