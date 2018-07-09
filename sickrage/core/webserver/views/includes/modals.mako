<!-- Main Modals -->
<%def name="mainModals()">
    <div class="modal fade" id="pleaseWaitDialog" data-backdrop="static" data-keyboard="false">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h1>Please Wait</h1>
                </div>
                <div class="modal-body">
                    <div id="ajax_loader">
                        <i class="fas fa-spinner fa-spin"></i>
                        <div id="current_info"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%def>

<!-- displayShow Modals -->
<%def name="displayShowModals()">
    <div id="manualSearchModalFailed" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">${_('Manual Search')}</h4>
                </div>
                <div class="modal-body">
                    <p>${_('Do you want to mark this episode as failed?')}</p>
                    <p class="text-warning">
                        <small>${_('The episode release name will be added to the failed history, preventing it to be downloaded again.')}</small>
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">${_('No')}</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">${_('Yes')}</button>
                </div>
            </div>
        </div>
    </div>

    <div id="manualSearchModalQuality" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">${_('Manual Search')}</h4>
                </div>
                <div class="modal-body">
                    <p>${_('Do you want to include the current episode quality in the search?')}</p>
                    <p class="text-warning">
                        <small>${_('Choosing No will ignore any releases with the same episode quality as the one currently downloaded/snatched.')}</small>
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">${_('No')}</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">${_('Yes')}</button>
                </div>
            </div>
        </div>
    </div>
</%def>