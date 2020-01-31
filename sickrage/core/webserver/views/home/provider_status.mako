<%inherit file="../layouts/main.mako"/>
<%!
    import requests
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card mb-3">
                <div class="card-header">
                    <h3>${_('Providers')}</h3>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table id="providersStatusTable" class="table" width="100%">
                            <thead class="thead-dark">
                            <tr>
                                <th>${_('Name')}</th>
                                <th>${_('URL')}</th>
                                <th>${_('Status')}</th>
                            </tr>
                            </thead>
                            <tbody>
                                % for providerID, providerObj in sickrage.app.search_providers.sort().items():
                                    <% providerURL = providerObj.urls['base_url'] %>
                                    <%
                                        try:
                                            online = True
                                            if 'localhost' not in providerURL:
                                                online = bool(sickrage.app.api.provider.get_status(providerID)['data']['status'])
                                        except Exception:
                                            online = False
                                    %>
                                    <tr>
                                        <td>${providerObj.name}</td>
                                        <td>${providerURL}</td>
                                        % if online:
                                            <td align="center" style="background-color:green">${_('ONLINE')}</td>
                                        % else:
                                            <td align="center" style="background-color:red">${_('OFFLINE')}</td>
                                        % endif
                                    </tr>
                                % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
