<%inherit file="./layouts/main.mako"/>
<%!
    import sickrage
%>

<%block name="content">
    <div class="row">
        % for announcement in sickrage.app.announcements.get():
            <div class="col-lg-2 mx-auto">
                <div class="announcement-container">
                    <div class="card mb-3" style="max-width: 540px;">
                        <div class="row no-gutters">
                            <div class="col-md-4">
                                <img src="${announcement.image}" class="card-img" alt="">
                            </div>
                            <div class="col-md-8">
                                <div class="card-body">
                                    <h5 class="card-title">${announcement.title}</h5>
                                    <p class="card-text">${announcement.description}</p>
                                    <p class="card-text"><small class="text-muted">${announcement.date}</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        % endfor
    </div>
</%block>