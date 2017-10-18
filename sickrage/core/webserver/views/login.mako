<%inherit file="./layouts/main.mako"/>
<%block name="content">
    <div class="row">
        <div class="col-lg-4 col-lg-offset-4 col-md-6 col-md-offset-3 col-sm-8 col-sm-offset-2 col-xs-10 col-xs-offset-1" align="center">
            <div class="login">
                <form action="" method="post">
                    <div class="row">
                        <div class="col-md-12" align="center">
                            <img src="/images/login.png" />
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">
                                <div class="input-group">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-user"></span>
                                    </div>
                                    <input class="form-control" title="${_('Username')}" name="username" type="text"
                                           placeholder="${_('Username')}" autocomplete="off"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">
                                <div class="input-group">
                                    <div class="input-group-addon">
                                        <span class="glyphicon glyphicon-lock"></span>
                                    </div>
                                    <input class="form-control" title="${_('Password')}" name="password" type="password"
                                           placeholder="${_('Password')}" autocomplete="off"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">
                                <label class="remember_me pull-left" title="${_('for 30 days')}">
                                    <input class="inlay" id="remember_me" name="remember_me" type="checkbox" value="1" checked="checked"/>&nbsp;Remember me
                                </label>
                                <input class="btn btn-default pull-right" name="submit" type="submit" value="${_('Login')}"/>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>
