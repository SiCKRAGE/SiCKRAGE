$(document).ready(function() {
    window.console_debug = false; // jshint ignore:line
    window.console_prefix = 'Restart: '; // jshint ignore:line
    window.current_pid = ''; // jshint ignore:line

    var isAliveUrl = srRoot + '/home/is_alive/';

    var checkIsAlive = setInterval(isAlive, 1000);

    function isAlive() {  // jshint ignore:line
        $.get(isAliveUrl, function(data) {
            if (data.msg.toLowerCase() === '') {
                // if it's still initializing then just wait and try again
                $('#shut_down_loading').hide();
                $('#shut_down_success').show();
                $('#restart_message').show();
            } else {
                // if this is before we've even shut down then just try again later
                //if (current_pid === '' || data.msg == current_pid) { // jshint ignore:line
                //    current_pid = data.msg; // jshint ignore:line
                // if we're ready to go then redirect to new url
                //} else {
                    clearInterval(checkIsAlive);
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                    setTimeout(function () {
                        window.location = srRoot + '/' + srDefaultPage + '/';
                    }, 5000);
                //}
            }

        }, 'jsonp');
    }
});
