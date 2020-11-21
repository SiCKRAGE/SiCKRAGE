<%inherit file="./layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-4 mx-auto">
            <div class="login">
                <div class="row">
                    <div class="col-md-12">
                        <img src="${srWebRoot}/images/logo.png" style="width: 100%"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="text-center">
                            <%
                                message = ""
                                if sickrage.app.config.general.sso_auth_enabled:
                                    message += "We are currently unable to reach the SiCKRAGE SSO authorization server"

                                if sickrage.app.config.general.ip_whitelist_enabled:
                                    if len(message):
                                        message += ", "
                                    message += "You're IP address <span class='text-info'>" + request.remote_ip + "</span> is currently not whitelisted to bypass authentication"

                                if sickrage.app.config.general.ip_whitelist_localhost_enabled:
                                    if len(message):
                                        message += ", "
                                    message += "You can bypass authentication if you login from a client on localhost"

                                message += ", Please try again later!"
                            %>
                            ${message}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>