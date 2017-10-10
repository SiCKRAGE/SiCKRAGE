<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div id="summary2" class="align-left">
        <div class="row">
            <div class="col-md-12">
                <h3>
                    Post-Processor:
                    ${(('Not in progress', 'In Progress')[postProcessorRunning], 'Paused')[postProcessorPaused]}
                </h3>
                <a class="btn"
                   href="${srWebRoot}/manage/manageQueues/pausePostProcessor?paused=${('1', '0')[bool(postProcessorPaused)]}">
                    <i class="icon-${('paused', 'play')[bool(postProcessorPaused)]}"></i>${('Pause', 'Unpause')[bool(postProcessorPaused)]}
                </a>
            </div>
        </div>


        <div class="row">
            <div class="col-md-12">
                <h3>Post-Processor Queue:</h3>
                <table>
                    <tr>
                        <td>Auto:</td>
                        <td><i>${postProcessorQueueLength['auto']} pending items</i></td>
                    </tr>
                    <tr>
                        <td>Manual:</td>
                        <td><i>${postProcessorQueueLength['manual']} pending items</i></td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</%block>
