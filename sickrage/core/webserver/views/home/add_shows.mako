<%inherit file="../layouts/main.mako"/>
<%!
    import os.path
    import urllib
    import sickrage
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="row">
                <div class="col-md-12">
                    <a href="${srWebRoot}/home/addShows/newShow/">
                        <div class="card card-block text-white bg-dark">
                            <div class="card-header"><i class="sickrage-core sickrage-core-addnew"></i></div>
                            <div class="card-body">
                                <h4 class="card-title">${_('Add New Show')}</h4>
                                <p class="card-text">${_('For shows that you haven\'t downloaded yet, this option finds a show on theTVDB.com, creates a directory for it\'s episodes and adds it.')}</p>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-md-12">
                    <a href="${srWebRoot}/home/addShows/traktShows">
                        <div class="card card-block text-white bg-dark">
                            <div class="card-header"><i class="sickrage-core sickrage-core-addtrakt"></i></div>
                            <div class="card-body">
                                <h4 class="card-title">${_('Add from Trakt')}</h4>
                                <p class="card-text">${_('For shows that you haven\'t downloaded yet, this option lets you choose a show from one of the Trakt lists to add to SiCKRAGE.')}</p>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-md-12">
                    <a href="${srWebRoot}/home/addShows/popularShows">
                        <div class="card card-block text-white bg-dark">
                            <div class="card-header"><i class="sickrage-core sickrage-core-addimdb"></i></div>
                            <div class="card-body">
                                <h4 class="card-title">${_('Add from IMDB')}</h4>
                                <p class="card-text">${_('View IMDB\'s list of the most popular shows. This feature uses IMDB\'s MOVIEMeter algorithm to identify popular TV Series.')}</p>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-md-12">
                    <a href="${srWebRoot}/home/addShows/existingShows">
                        <div class="card card-block text-white bg-dark">
                            <div class="card-header"><i class="sickrage-core sickrage-core-addexisting"></i></div>
                            <div class="card-body">
                                <h4 class="card-title">${_('Add Existing Shows')}</h4>
                                <p class="card-text">${_('Use this option to add shows that already have a folder created on your hard drive. SickRage will scan your existing metadata/episodes and add the show accordingly.')}</p>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    </div>
</%block>
