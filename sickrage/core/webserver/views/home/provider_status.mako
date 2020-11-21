<%inherit file="../layouts/main.mako"/>
<%!
    import requests
    import sickrage

    from sickrage.core.helpers import anon_url
    from sickrage.search_providers import SearchProviderType
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
                                    % if providerObj.provider_type not in [SearchProviderType.TORRENT_RSS, SearchProviderType.NEWZNAB] and providerObj.id not in ['bitcannon']:
                                        <% providerURL = providerObj.urls['base_url'] %>
                                        <%
                                            online = True
                                            resp = sickrage.app.api.provider.get_status(providerID)
                                            if resp and 'data' in resp:
                                                online = bool(resp['data']['status'])
                                            else:
                                                online = False
                                        %>

                                        <tr>
                                            <td>${providerObj.name}</td>
                                            <td>
                                                <a href="${anon_url(providerURL)}" rel="noreferrer"
                                                   onclick="window.open(this.href, '_blank'); return false;">
                                                    ${providerURL}
                                                </a>
                                            </td>
                                            % if online:
                                                <td align="center" style="background-color:green">${_('ONLINE')}</td>
                                            % else:
                                                <td align="center" style="background-color:red">${_('OFFLINE')}</td>
                                            % endif
                                        </tr>
                                    % endif
                                % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
