<%inherit file="./layouts/main.mako"/>
<%!
    from datetime import datetime
    import sickrage
%>

<%block name="content">
    <div class="container">
        <div class="row">
            % for announcement in announcements:
                <div class="col-md-4 offset-md-0 offset-sm-1 mx-auto">
                    <div id="${announcement.ahash}" class="announcement">
                        <div class="card mb-3" style="max-width: 540px; height: 250px">
                            <div class="row ml-3 mr-3 mt-3">
                                <div class="col-md-11">
                                    <h5 class="card-title">${announcement.title}</h5>
                                </div>
                                % if not announcement.seen:
                                    <div class="col-md-1">
                                        <div class="mark-seen">
                                            <i class="fa fa-circle" style="color: dodgerblue"></i>
                                        </div>
                                    </div>
                                % endif
                            </div>
                            <div class="row no-gutters mx-3">
                                <div class="col-md-2">
                                    <img src="${announcement.image}" class="card-img rounded-circle" alt=""
                                         style="width: 85px;height: 85px;">
                                </div>
                                <div class="col-md-10">
                                    <div class="card-body pt-0">
                                        <div class="card-text">
                                            <div class="text-muted">${datetime.strptime(announcement.date, '%Y-%m-%d').strftime("%b %d, %Y")}</div>
                                        </div>
                                        <div class="card-text">${announcement.description}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        </div>
    </div>
</%block>