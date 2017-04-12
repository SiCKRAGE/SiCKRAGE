<!-- displayShow Modals -->
<%def name="displayShowModals()">
    <div id="manualSearchModalFailed" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">Manual Search</h4>
                </div>
                <div class="modal-body">
                    <p>Do you want to mark this episode as failed?</p>
                    <p class="text-warning">
                        <small>The episode release name will be added to the failed history, preventing it to be
                            downloaded again.
                        </small>
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">No</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">Failed</button>
                </div>
            </div>
        </div>
    </div>

    <div id="manualSearchModalQuality" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">Manual Search</h4>
                </div>
                <div class="modal-body">
                    <p>Do you want to include the current episode quality in the search?</p>
                    <p class="text-warning">
                        <small>Choosing No will ignore any releases with the same episode quality as the one currently
                            downloaded/snatched.
                        </small>
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">No</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">Yes</button>
                </div>
            </div>
        </div>
    </div>
</%def>