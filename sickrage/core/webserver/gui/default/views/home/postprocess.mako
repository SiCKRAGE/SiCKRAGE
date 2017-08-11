<%inherit file="../layouts/main.mako"/>
<%!
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-8 col-lg-offset-2 col-md-10 col-md-offset-1">
            <h1 class="title">${title}</h1>
            <form name="processForm" method="post" action="processEpisode" style="line-height: 40px;">
                <input type="hidden" id="type" name="proc_type" value="manual">
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b>Enter the folder containing the episode</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <div class="input-group input200">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-folder-open"></span>
                            </div>
                            <input name="proc_dir" id="episodeDir" class="form-control" autocapitalize="off"
                                   title="directory"/>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b>Process Method to be used:</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <div class="input-group input200">
                            <div class="input-group-addon">
                                <span class="glyphicon glyphicon-refresh"></span>
                            </div>
                            <select name="process_method" id="process_method" title="Choose post-processing method"
                                    class="form-control form-control-inline input-sm">
                                <% process_method_text = {'copy': "Copy", 'move': "Move", 'hardlink': "Hard Link", 'symlink' : "Symbolic Link"} %>
                                % for curAction in ('copy', 'move', 'hardlink', 'symlink'):
                                    <option value="${curAction}" ${('', 'selected="selected"')[sickrage.srCore.srConfig.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b>Force already Post Processed Dir/Files:</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="force" name="force" type="checkbox" title="">
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b>Mark Dir/Files as priority download:</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="is_priority" name="is_priority" type="checkbox" title="">
                        <span style="line-height: 0; font-size: 12px;"><i>&nbsp;(Check it to replace the file even if it exists at higher quality)</i></span>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <b>Delete files and folders:</b>
                    </div>
                    <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                        <input id="delete_on" name="delete_on" type="checkbox" title="">
                        <span style="line-height: 0; font-size: 12px;"><i>&nbsp;(Check it to delete files and folders like auto processing)</i></span>
                    </div>
                </div>
                % if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
                    <div class="row">
                        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                            <b>Mark download as failed:</b>
                        </div>
                        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
                            <input id="failed" name="failed" type="checkbox" title="">
                        </div>
                    </div>
                % endif
                <div class="row">
                    <div class="col-md-12">
                        <input id="submit" class="btn" type="submit" value="Process"/>
                    </div>
                </div>
            </form>
        </div>
    </div>
</%block>
