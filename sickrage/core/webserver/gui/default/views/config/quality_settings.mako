<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
    from sickrage.core.common import Quality
    from sickrage.core.helpers import anon_url
%>
<%block name="content">
    <div id="config">
        <div id="ui-content">

            <form id="configForm" action="saveQualities" method="post">
                <div id="ui-components">
                    <ul>
                        <li><a href="#core-component-group1">Quality Sizes</a></li>
                    </ul>

                    <div id="core-component-group1" class="component-group" style='min-height: 550px;'>

                        <div class="component-group-desc">
                            <h3>Quality Sizes</h3>
                            <p>Use default qualitiy sizes or specify custom ones per quality definition.</p>

                            <div>
                                <p class="note"> Settings repersent maximum size allowed per episode video file.</p>
                            </div>
                        </div>

                        <fieldset class="component-group-list">
                            <table>
                                % for qtype, qsize in sickrage.srCore.srConfig.QUALITY_SIZES.items():
                                <% if qsize == 0: continue %>

                                    <tr>
                                        <td>
                                            <label for="${qtype}"
                                                   style="vertical-align:middle;">${Quality.qualityStrings[qtype]}</label>
                                        </td>
                                        <td>
                                            <input type="number" value="${qsize}" name="${qtype}" id="${qtype}" min="1"> MB
                                        </td>
                                    </tr>
                                % endfor
                            </table>
                            <br><input type="submit" class="btn config_submitter" value="Save Changes"/><br>
                        </fieldset>
                    </div><!-- /component-group1 //-->

                    <br><input type="submit" class="btn config_submitter_refresh" value="Save Changes"/><br>

                </div><!-- /ui-components //-->

            </form>
        </div>
    </div>
</%block>
