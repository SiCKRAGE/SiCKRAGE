<%inherit file="/layouts/main.mako"/>
<%block name="content">
    <div class="login">
        <form action="" method="post">
            <div class="ctrlHolder">
                <input class="inlay" id="username" name="username" type="text"
                       placeholder="Username"
                       autocomplete="off" autocapitalize="off"/>
            </div>
            <div class="ctrlHolder">
                <input class="inlay" id="password" name="password" type="password"
                       placeholder="Password" autocomplete="off" autocapitalize="off"/>
            </div>
            <div class="ctrlHolder">
                <span class="errormessage"></span>
                <label class="remember_me" title="for 30 days"><input class="inlay" id="remember_me" name="remember_me"
                                                                      type="checkbox" value="1" checked="checked"/>
                    Remember
                    me</label>
                <input class="button" name="submit" type="submit" value="Login"/>
            </div>
        </form>
    </div>
</%block>
