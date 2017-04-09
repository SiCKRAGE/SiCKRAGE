<%inherit file="/layouts/main.mako"/>
<%block name="content">
    <div class="container">
        <div class="row">
            <div class="col-sm-8 col-sm-offset-2 col-md-6 col-md-offset-3 col-lg-4 col-lg-offset-4">
                <div class="login">
                    <form action="" method="post">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <input class="form-control" id="username" name="username" type="text"
                                           placeholder="Username" autocomplete="off" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <input class="form-control" id="password" name="password" type="password"
                                           placeholder="Password" autocomplete="off" autocapitalize="off"/>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <div class="form-group">
                                    <label class="remember_me" title="for 30 days">
                                        <input class="inlay" id="remember_me" name="remember_me" type="checkbox"
                                               value="1" checked="checked"/>Remember me
                                    </label>
                                    <input class="btn btn-default pull-right" name="submit" type="submit"
                                           value="Login"/>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</%block>
