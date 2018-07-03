<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import urllib
    import sickrage
%>
<%block name="content">
    <div id="addShowPortal">
        <div class="row align-items-center">
            <div class="col"></div>
            <div class="col">
                <h1 class="title">${title}</h1>
                <hr/>
            </div>
            <div class="col"></div>
        </div>
        <div class="row align-items-center">
            <div class="col"></div>
            <div class="col">
                <a href="${srWebRoot}/home/addShows/newShow/">
                    <div class="card card-block text-white bg-dark mb-3">
                        <div class="card-header"><i class="icons-sickrage icons-sickrage-add-new"></i></div>
                        <div class="card-body">
                            <h4 class="card-title">${_('Add New Show')}</h4>
                            <p class="card-text">${_('For shows that you haven\'t downloaded yet, this option finds a show on theTVDB.com, '
                            'creates a directory for it\'s episodes and adds it.')}</p>
                        </div>
                    </div>
                </a>
            </div>
            <div class="col"></div>
        </div>
        <br/>
        <div class="row align-items-center">
            <div class="col"></div>
            <div class="col">
                <a href="${srWebRoot}/home/addShows/traktShows">
                    <div class="card card-block text-white bg-dark mb-3">
                        <div class="card-header"><i class="icons-sickrage icons-sickrage-add-trakt"></i></div>
                        <div class="card-body">
                            <h4 class="card-title">${_('Add from Trakt')}</h4>
                            <p class="card-text">${_('For shows that you haven\'t downloaded yet, this option lets you '
                            'choose a show from one of the Trakt lists to add to SiCKRAGE.')}</p>
                        </div>
                    </div>
                </a>
            </div>
            <div class="col"></div>
        </div>
        <br/>
        <div class="row align-items-center">
            <div class="col"></div>
            <div class="col">
                <a href="${srWebRoot}/home/addShows/popularShows">
                    <div class="card card-block text-white bg-dark mb-3">
                        <div class="card-header"><i class="icons-sickrage icons-sickrage-add-imdb"></i></div>
                        <div class="card-body">
                            <h4 class="card-title">${_('Add from IMDB')}</h4>
                            <p class="card-text">${_('View IMDB\'s list of the most popular shows. This feature uses '
                            'IMDB\'s MOVIEMeter algorithm to identify popular TV Series.')}</p>
                        </div>
                    </div>
                </a>
            </div>
            <div class="col"></div>
        </div>
        <br/>
        <div class="row align-items-center">
            <div class="col"></div>
            <div class="col">
                <a href="${srWebRoot}/home/addShows/existingShows">
                    <div class="card card-block text-white bg-dark mb-3">
                        <div class="card-header"><i class="icons-sickrage icons-sickrage-add-existing"></i></div>
                        <div class="card-body">
                            <h4 class="card-title">${_('Add Existing Shows')}</h4>
                            <p class="card-text">${_('Use this option to add shows that already have a folder created '
                            'on your hard drive. SickRage will scan your existing metadata/episodes and add the show '
                            'accordingly.')}</p>
                        </div>
                    </div>
                </a>
            </div>
            <div class="col"></div>
        </div>
    </div>
</%block>
