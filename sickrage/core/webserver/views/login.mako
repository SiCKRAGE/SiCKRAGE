<%inherit file="./layouts/main.mako"/>
<%block name="content">
    <div class="row">
        <div class="col-lg-4 mx-auto">
            <div class="login">
                <form action="" method="post">
                    <div class="row">
                        <div class="col-md-12">
                            <img src="${srWebRoot}/images/logo.png" style="width: 100%"/>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-user"></span>
                                        </span>
                                    </div>
                                    <input class="form-control" title="${_('Username')}" name="username"
                                           placeholder="${_('Username')}" autocomplete="off"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">
                                <div class="input-group">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">
                                            <span class="fas fa-key"></span>
                                        </span>
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
                                <label class="remember_me" title="${_('for 30 days')}">
                                    <input id="remember_me" name="remember_me" type="checkbox" value="1"
                                           checked="checked"/>&nbsp;${_('Remember me')}
                                </label>
                                <input class="btn btn-default pull-right" name="submit" type="submit"
                                       value="${_('Login')}"/>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</%block>