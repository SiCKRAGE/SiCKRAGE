<%inherit file="../layouts/main.mako"/>
<%block name="content">
<h1 class="header">${header}</h1>
${info_download_station}
<iframe id="extFrame" src="${webui_url}" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
</%block>
