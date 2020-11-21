<%inherit file="./layouts/main.mako"/>

<%!
    import json
    from collections import OrderedDict
    from sickrage.core.webserver import ApiHandler
%>

<%block name="metas">
    <meta data-var="commands" data-content="${api_commands}">
    <meta data-var="episodes" data-content="${episodes}">
</%block>

<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3>${title}</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="btn-group navbar-btn" data-toggle="buttons">
                                <label class="btn btn-primary">
                                    <input autocomplete="off" id="option-profile" type="checkbox"/> ${_('Profile')}
                                </label>
                                <label class="btn btn-primary">
                                    <input autocomplete="off" id="option-jsonp" type="checkbox"/> ${_('JSONP')}
                                </label>
                            </div>

                            <form class="navbar-form navbar-right">
                                <div class="form-group">
                                    <input autocomplete="off" class="form-control" id="command-search"
                                           placeholder="${_('Command name')}"
                                           type="search"/>
                                </div>
                            </form>
                        </div>
                    </div>


                    <div id="commands_list">
                        % for command, help in api_commands.items():
                        <%
                            command_id = command.replace('.', '-')
                        %>
                            <div class="card mt-1 mb-3">
                                <div class="card-header">
                                    <h4 class="card-title">
                                        <a data-toggle="collapse" data-parent="#commands_list"
                                           href="#command-${command_id}" style="color: #000;">${command}</a>
                                    </h4>
                                </div>
                                <div class="collapse" id="command-${command_id}">
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <blockquote>${help['message']}</blockquote>
                                            </div>
                                        </div>
                                        % if help['data']['optionalParameters'] or help['data']['requiredParameters']:
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <h4>${_('Parameters')}</h4>

                                                    <div class="table-responsive">
                                                        <table class="table">
                                                            <thead>
                                                            <tr>
                                                                <th>${_('Name')}</th>
                                                                <th>${_('Required')}</th>
                                                                <th>${_('Description')}</th>
                                                                <th>${_('Type')}</th>
                                                                <th>${_('Default value')}</th>
                                                                <th>${_('Allowed values')}</th>
                                                            </tr>
                                                            </thead>
                                                            ${display_parameters_doc(help['data']['requiredParameters'], True)}
                                                            ${display_parameters_doc(help['data']['optionalParameters'], False)}
                                                        </table>
                                                    </div>
                                                </div>
                                            </div>
                                        % endif
                                        <div class="row">
                                            <div class="col-md-12">
                                                <h4>${_('Playground')}</h4>
                                                <span>
                                                    ${_('URL:')} <kbd id="command-${command_id}-base-url">${srWebRoot}/api/${apikey}/?cmd=${command}</kbd>
                                                </span>
                                            </div>
                                        </div>
                                        % if help['data']['requiredParameters']:
                                            <br/>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('Required parameters')}</label>
                                                    ${display_parameters_playground(help['data']['requiredParameters'], True, command_id)}
                                                </div>
                                            </div>
                                        % endif
                                        % if help['data']['optionalParameters']:
                                            <br/>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('Optional parameters')}</label>
                                                    ${display_parameters_playground(help['data']['optionalParameters'], False, command_id)}
                                                </div>
                                            </div>
                                        % endif
                                        <br/>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <button class="btn btn-primary shadow" data-action="api-call"
                                                        data-command-name="${command_id}"
                                                        data-base-url="command-${command_id}-base-url"
                                                        data-target="#command-${command_id}-response"
                                                        data-time="#command-${command_id}-time"
                                                        data-url="#command-${command_id}-url">
                                                    ${_('Call API')}
                                                </button>
                                            </div>
                                        </div>

                                        <div class="result-wrapper d-none">
                                            <div class="clearfix">
                                                <span class="float-left">
                                                    ${_('Response:')} <strong
                                                        id="command-${command_id}-time"></strong><br/>
                                                    ${_('URL:')} <kbd id="command-${command_id}-url"></kbd>
                                                </span>
                                                <span class="float-right">
                                                    <button class="btn" data-action="clear-result"
                                                            data-target="#command-${command_id}-response">${_('Clear')}</button>
                                                </span>
                                            </div>

                                            <pre><code class="text-white"
                                                       id="command-${command_id}-response"></code></pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        % endfor
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>

<%def name="display_parameters_doc(parameters, required)">
    <tbody>
        % for parameter in parameters:
            <% parameter_help = parameters[parameter] %>
            <tr>
                <td>
                    % if required:
                        <strong>${parameter}</strong>
                    % else:
                        ${parameter}
                    % endif
                </td>
                <td class="table-fit">
                    % if required:
                        <span class="fas fa-check text-success" title="${_('Yes')}"></span>
                    % else:
                        <span class="fas fa-times text-muted" title="${_('No')}"></span>
                    % endif
                </td>
                <td>${parameter_help.get('desc', '')}</td>
                <td>${parameter_help.get('type', '')}</td>
                <td>${parameter_help.get('defaultValue', '')}</td>
                <td>${parameter_help.get('allowedValues', '')}</td>
            </tr>
        % endfor
    </tbody>
</%def>

<%def name="display_parameters_playground(parameters, required, command)">
    <div class="form-inline">
        % for parameter in parameters:
            <%
                parameter_help = parameters[parameter]
                allowed_values = parameter_help.get('allowedValues', '')
                type = parameter_help.get('type', '')
            %>

            % if isinstance(allowed_values, list):
                <select class="form-control"${('', ' multiple="multiple"')[type == 'list']} name="${parameter}"
                        data-command="${command}">
                    <option>${parameter}</option>

                    % if allowed_values == [0, 1]:
                        <option value="0">${_('No')}</option>
                        <option value="1">${_('Yes')}</option>
                    % else:
                        % for allowed_value in allowed_values:
                            <option value="${allowed_value}">${allowed_value}</option>
                        % endfor
                    % endif
                </select>
            % elif parameter == 'series_id':
                <select class="form-control" name="${parameter}" data-action="update-seasons" data-command="${command}">
                    <option>${parameter}</option>

                    % for show in shows:
                        <option value="${show.series_id}">${show.name}</option>
                    % endfor
                </select>
            % if 'season' in parameters:
                <select class="form-control d-none" name="season" data-action="update-episodes"
                        data-command="${command}">
                    <option>${_('season')}</option>
                </select>
            % endif

            % if 'episode' in parameters:
                <select class="form-control d-none" name="episode" data-command="${command}">
                    <option>${_('episode')}</option>
                </select>
            % endif
            % elif parameter == 'tvdbid':
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number"
                       data-command="${command}"/>
            % elif type == 'int':
                % if parameter not in ('episode', 'season'):
                    <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number"
                           data-command="${command}"/>
                % endif
            % elif type == 'string':
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="text"
                       data-command="${command}"/>
            % endif
        % endfor
    </div>
</%def>