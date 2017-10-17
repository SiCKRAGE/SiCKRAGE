<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import urllib
    import sickrage
%>
<%block name="content">
    <div id="addShowPortal">
        <div class="row">
            <div class="col-md-12">
                <h1 class="title">${title}</h1>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <a href="${srWebRoot}/home/addShows/newShow/" id="btnNewShow" class="btn btn-large">
                    <div class="button">
                        <div class="icon-addnew-show"></div>
                    </div>
                    <div class="buttontext">
                        <h3>${_('Add New Show')}</h3>
                        <p>
                            ${_('For shows that you haven\'t downloaded yet, this option finds a show on theTVDB.com, '
                            'creates a directory for it\'s episodes and adds it.')}
                        </p>
                    </div>
                </a>
            </div>
        </div>
        <br/>
        <div class="row">
            <div class="col-md-12">
                <a href="${srWebRoot}/home/addShows/traktShows" id="btnNewShow"
                   class="btn btn-large">
                    <div class="button">
                        <div class="icon-trakt-show"></div>
                    </div>
                    <div class="buttontext">
                        <h3>${_('Add from Trakt')}</h3>
                        <p>
                            ${_('For shows that you haven\'t downloaded yet, this option lets you choose a show from '
                            'one of the Trakt lists to add to SiCKRAGE.')}
                        </p>
                    </div>
                </a>
            </div>
        </div>
        <br/>
        <div class="row">
            <div class="col-md-12">
                <a href="${srWebRoot}/home/addShows/popularShows/" id="btnNewShow" class="btn btn-large">
                    <div class="button">
                        <div class="icon-imdb-show"></div>
                    </div>
                    <div class="buttontext">
                        <h3>${_('Add from IMDB')}</h3>
                        <p>
                            ${_('View IMDB\'s list of the most popular shows. This feature uses IMDB\'s MOVIEMeter '
                            'algorithm to identify popular TV Series.')}
                        </p>
                    </div>
                </a>
            </div>
        </div>
        <br/>
        <div class="row">
            <div class="col-md-12">
                <a href="${srWebRoot}/home/addShows/existingShows/" id="btnExistingShow" class="btn btn-large">
                    <div class="button">
                        <div class="icon-addexisting-show"></div>
                    </div>
                    <div class="buttontext">
                        <h3>${_('Add Existing Shows')}</h3>
                        <p>
                            ${_('Use this option to add shows that already have a folder created on your hard drive. '
                            'SickRage will scan your existing metadata/episodes and add the show accordingly.')}
                        </p>
                    </div>
                </a>
            </div>
        </div>

    </div>
</%block>
