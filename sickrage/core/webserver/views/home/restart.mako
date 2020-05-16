<%!
    import sickrage
%>

<meta data-var="srWebRoot" data-content="${srWebRoot}">
<meta data-var="srDefaultPage" data-content="${srDefaultPage}">
<%block name="metas" />

<link rel="stylesheet" type="text/css" href="${srWebRoot}/css/core.min.css"/>
<%block name="css" />

<%block name="content">
    <div class="row mx-auto w-100">
        <div class="col p-0 text-center">
            <div class="card">
                <div class="card-header">
                    <h2>${_('Performing Restart')}</h2>
                </div>
                <div class="card-text progress mx-auto w-100" style="width:50%">
                    <div id="dynamic" class="progress-bar progress-bar-striped active" role="progressbar"></div>
                </div>
                <div class="card-footer">
                    <strong id="message">
                        Waiting for SiCKRAGE to shut down
                    </strong>
                </div>
            </div>
        </div>
    </div>
</%block>

<script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
<script>
    let timeout_id;
    let current_pid = '';
    let current_percent = 0;
    let srWebRoot = $('meta[data-var="srWebRoot"]').data('content');
    let srDefaultPage = $('meta[data-var="srDefaultPage"]').data('content');

    function checkIsAlive() {
        current_percent += 1;

        $("#dynamic").css("width", current_percent + "%").text(current_percent + "% Complete");

        $.ajax({
            url: srWebRoot + '/home/is-alive/',
            dataType: 'jsonp',
            jsonp: 'srcallback',
            success: function (data) {
                if (data.msg !== 'nope') {
                    if (current_pid === '' || data.msg === current_pid) {
                        current_pid = data.msg;
                    } else {
                        clearInterval(timeout_id);
                        $("#dynamic").css({"width": "100%", 'background-color': 'green'}).text("100% Complete");
                        $("#message").text("Loading the home page");
                        window.location = srWebRoot + '/' + srDefaultPage + '/';
                    }
                }
            },
            error: function (error) {
                $("#message").text("Waiting for SiCKRAGE to start again");

                // if it is taking forever just give up
                if (current_percent >= 100) {
                    clearInterval(timeout_id);
                    $("#dynamic").css({"width": "100%", 'background-color': 'red'});
                    $("#message").text("The restart has timed out, perhaps something prevented SiCKRAGE from starting again?");
                }
            }
        });
    }

    timeout_id = setInterval(checkIsAlive, 1000);
</script>
<%block name="scripts" />