$(document).ready(function(){

  $('#submitMassEdit').click(function(){
    var editArr = new Array()
  
    $('.editCheck').each(function() {
      if (this.checked == true) {
        editArr.push($(this).attr('id').split('-')[1])
      }
    });

    if (editArr.length == 0)
        return

    url = 'massEdit?toEdit='+editArr.join('|')
    window.location.href = url
  });


  $('#submitMassUpdate').click(function(){
  
    var updateArr = new Array()
    var refreshArr = new Array()
    var renameArr = new Array()
    var subtitleArr = new Array()
    var deleteArr = new Array()
	var removeArr = new Array()
    var metadataArr = new Array()

    $('.updateCheck').each(function() {
      if (this.checked == true) {
        updateArr.push($(this).attr('id').split('-')[1])
      }
    });

    $('.refreshCheck').each(function() {
      if (this.checked == true) {
        refreshArr.push($(this).attr('id').split('-')[1])
      }
    });  

    $('.renameCheck').each(function() {
      if (this.checked == true) {
        renameArr.push($(this).attr('id').split('-')[1])
      }
    });

	$('.subtitleCheck').each(function() {
      if (this.checked == true) {
        subtitleArr.push($(this).attr('id').split('-')[1])
      }
    });

	$('.removeCheck').each(function() {
	  if (this.checked == true) {
		removeArr.push($(this).attr('id').split('-')[1])
	  }
	});
    
    var deleteCount = 0;

    $('.deleteCheck').each(function() {
        if (this.checked == true) {
            deleteCount++;
        }
    });
    
    if (deleteCount >= 1) {
        bootbox.confirm("You have selected to delete " + deleteCount + " show(s).  Are you sure you wish to cntinue? All files will be removed from your system.", function(result) {
            if (result) {
                $('.deleteCheck').each(function() {
                    if (this.checked == true) {
                        deleteArr.push($(this).attr('id').split('-')[1])
                    }
                });
            }
            if (updateArr.length+refreshArr.length+renameArr.length+subtitleArr.length+deleteArr.length+removeArr.length+metadataArr.length == 0)
                return false;                   
            url = 'massUpdate?toUpdate='+updateArr.join('|')+'&toRefresh='+refreshArr.join('|')+'&toRename='+renameArr.join('|')+'&toSubtitle='+subtitleArr.join('|')+'&toDelete='+deleteArr.join('|')+'&toRemove='+removeArr.join('|')+'&toMetadata='+metadataArr.join('|');
            window.location.href = url
        });
    }
    else
    {
        if (updateArr.length+refreshArr.length+renameArr.length+subtitleArr.length+deleteArr.length+removeArr.length+metadataArr.length == 0)
            return false;
        url = 'massUpdate?toUpdate='+updateArr.join('|')+'&toRefresh='+refreshArr.join('|')+'&toRename='+renameArr.join('|')+'&toSubtitle='+subtitleArr.join('|')+'&toDelete='+deleteArr.join('|')+'&toRemove='+removeArr.join('|')+'&toMetadata='+metadataArr.join('|');
        window.location.href = url       
    }
/*
    $('.metadataCheck').each(function() {
      if (this.checked == true) {
        metadataArr.push($(this).attr('id').split('-')[1])
      }
    });
*/

  });

  $('.bulkCheck').click(function(){
    
    var bulkCheck = this;
    var whichBulkCheck = $(bulkCheck).attr('id');

    $('.'+whichBulkCheck).each(function(){
        if (!this.disabled)
            this.checked = !this.checked 
    });
  });

  ['.editCheck', '.updateCheck', '.refreshCheck', '.renameCheck', '.deleteCheck', '.removeCheck'].forEach(function(name) {
    var lastCheck = null;

    $(name).click(function(event) {

      if(!lastCheck || !event.shiftKey) {
        lastCheck = this;
        return;
      }

      var check = this;
      var found = 0;

      $(name).each(function() {
        switch (found) {
          case 2: return false;
          case 1: 
            if (!this.disabled)
              this.checked = lastCheck.checked;
        }

        if (this == check || this == lastCheck)
          found++;
      });

      lastClick = this;
    });

  });
  
});
