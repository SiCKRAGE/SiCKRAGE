<%
    import sickrage

    if sickrage.srCore.srConfig.ROOT_DIRS:
        backend_pieces = sickrage.srCore.srConfig.ROOT_DIRS.split('|')
        backend_default = 'rd-' + backend_pieces[0]
        backend_dirs = backend_pieces[1:]
    else:
        backend_default = ''
        backend_dirs = []
%>

<span id="sampleRootDir"></span>

<input type="hidden" id="whichDefaultRootDir" value="${backend_default}"/>
<div class="rootdir-selectbox">
    <label for="rootDirs">
        <select name="rootDir" id="rootDirs" class="form-control form-control-inline" size="6">
            % for cur_dir in backend_dirs:
                <option value="${cur_dir}">${cur_dir}</option>
            % endfor
        </select>
    </label>
</div>
<div id="rootDirsControls" class="rootdir-controls">
    <input class="btn btn-inline pull-left" type="button" id="addRootDir" value="New"/>
    <input class="btn btn-inline pull-left" type="button" id="editRootDir" value="Edit"/>
    <input class="btn btn-inline pull-left" type="button" id="deleteRootDir" value="Delete"/>
    <input class="btn btn-inline pull-left" type="button" id="defaultRootDir" value="Set as Default *"/>
</div>
<label for="rootDirText">
    <input type="text" style="display: none" id="rootDirText" autocapitalize="off"/>
</label>
