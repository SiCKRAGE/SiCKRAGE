<%!
    import html
    import sickrage
    from sickrage.core.common import Quality, Qualities
%>
<%def name="renderQualityPill(quality, showTitle=False, overrideClass=None)">
    <%
        # Build a string of quality names to use as title attribute
        if showTitle:
            iQuality, pQuality = Quality.split_quality(quality)
            title = _('Initial Quality:') + '\n'
            if iQuality:
                for curQual in iQuality:
                    title += "  " + curQual.display_name + "\n"
            else:
                title += "  None\n"
            title += "\n" + _("Preferred Quality:") + "\n"
            if pQuality:
                for curQual in pQuality:
                    title += "  " + curQual.display_name + "\n"
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

        if Qualities(quality):
            cssClass = Qualities(quality).css_name
            qualityString = Qualities(quality).display_name
        else:
            cssClass = "Custom"
            qualityString = "Custom"

        cssClass = "badge p-1 align-middle text-white " + cssClass
        if overrideClass:
            cssClass = overrideClass
    %>
    <span ${title} class="${cssClass}">${qualityString}</span>
</%def>
