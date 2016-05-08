<%inherit file="/layouts/api.mako"/>

<%!
    from sickrage.core.webserver.api import ApiHandler
%>

<%block name="metas">
    <meta data-var="commands" data-content="${ApiHandler(application, request).api_calls.keys()}">
    <meta data-var="episodes" data-content="${episodes}">
</%block>

<%block name="content">
    <div id="content">
        <div class="panel-group" id="commands_list">
            % for cmd, func in ApiHandler(application, request).api_calls.items():
            <%
                command_id = cmd.replace('.', '-')
                help = func(application, request, **{'help':1}).run()
            %>
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h4 class="panel-title">
                        <a data-toggle="collapse" data-parent="#commands_list" href="#command-${command_id}">${cmd}</a>
                    </h4>
                </div>
                <div class="panel-collapse collapse" id="command-${command_id}">
                    <div class="panel-body">
                        <blockquote>${help['message']}</blockquote>

                        % if help['data']['optionalParameters'] or help['data']['requiredParameters']:
                        <h4>Parameters</h4>

                        <table class="tablesorter">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Required</th>
                                <th>Description</th>
                                <th>Type</th>
                                <th>Default value</th>
                                <th>Allowed values</th>
                            </tr>
                        </thead>
                        ${display_parameters_doc(help['data']['requiredParameters'], True)}
                        ${display_parameters_doc(help['data']['optionalParameters'], False)}
                        </table>
                        % endif

                        <h4>Playground</h4>

                        URL: <kbd id="command-${command_id}-base-url">/api/${apikey}/?cmd=${cmd}</kbd><br>

                        % if help['data']['requiredParameters']:
                            Required parameters: ${display_parameters_playground(help['data']['requiredParameters'], True, command_id)}<br>
                        % endif

                        % if help['data']['optionalParameters']:
                            Optional parameters: ${display_parameters_playground(help['data']['optionalParameters'], False, command_id)}<br>
                        % endif

                        <button class="btn btn-primary" data-action="api-call" data-command-name="${command_id}" data-base-url="command-${command_id}-base-url" data-target="#command-${command_id}-response" data-time="#command-${command_id}-time" data-url="#command-${command_id}-url">Call API</button><br>

                        <div class="result-wrapper hidden">
                            <div class="clearfix">
                                <span class="pull-left">
                                    Response: <strong id="command-${command_id}-time"></strong><br>
                                    URL: <kbd id="command-${command_id}-url"></kbd>
                                </span>
                                <span class="pull-right">
                                    <button class="btn btn-default" data-action="clear-result" data-target="#command-${command_id}-response">Clear</button>
                                </span>
                            </div>

                            <pre><code id="command-${command_id}-response"></code></pre>
                        </div>
                    </div>
                </div>
            </div>
            % endfor
        </div>
    </div>

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
                <td class="text-center">
                    % if required:
                        <span class="glyphicon glyphicon-ok text-success" title="Yes"></span>
                    % else:
                        <span class="glyphicon glyphicon-remove text-muted" title="No"></span>
                    % endif
                </td>
                <td>${parameter_help['desc'] if 'desc' in parameter_help else ''}</td>
                <td>${parameter_help['type'] if 'type' in parameter_help else ''}</td>
                <td>${parameter_help['defaultValue'] if 'defaultValue' in parameter_help else ''}</td>
                <td>${parameter_help['allowedValues'] if 'allowedValues' in parameter_help else ''}</td>
            </tr>
        % endfor
        </tbody>
    </%def>

    <%def name="display_parameters_playground(parameters, required, command)">
        <div class="form-inline">
            % for parameter in parameters:
            <%
                parameter_help = parameters[parameter]
                allowed_values = parameter_help['allowedValues'] if 'allowedValues' in parameter_help else ''
                type = parameter_help['type'] if 'type' in parameter_help else ''
            %>

            % if isinstance(allowed_values, list):
                <select class="form-control"${('', ' multiple="multiple"')[type == 'list']} name="${parameter}" data-command="${cmd}">
                    <option>${parameter}</option>

                    % if allowed_values == [0, 1]:
                        <option value="0">No</option>
                        <option value="1">Yes</option>
                    % else:
                        % for allowed_value in allowed_values:
                        <option value="${allowed_value}">${allowed_value}</option>
                        % endfor
                    % endif
                </select>
            % elif parameter == 'indexerid':
                <select class="form-control" name="${parameter}" data-action="update-seasons" data-command="${cmd}">
                    <option>${parameter}</option>

                    % for show in shows:
                    <option value="${show.indexerid}">${show.name}</option>
                    % endfor
                </select>

                % if 'season' in parameters:
                <select class="form-control hidden" name="season" data-action="update-episodes" data-command="${cmd}">
                    <option>season</option>
                </select>
                % endif

                % if 'episode' in parameters:
                <select class="form-control hidden" name="episode" data-command="${cmd}">
                    <option>episode</option>
                </select>
                % endif
            % elif parameter == 'tvdbid':
                <select class="form-control" name="${parameter}" data-command="${cmd}">
                    <option>${parameter}</option>

                    % for show in shows:
                    <option value="${show.indexerid}">${show.name}</option>
                    % endfor
                </select>
            % elif type == 'int':
                % if parameter not in ('episode', 'season'):
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number" data-command="${cmd}" />
                % endif
            % elif type == 'string':
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="text" data-command="${cmd}" />
            % endif
        % endfor
        </div>
    </%def>
</%block>