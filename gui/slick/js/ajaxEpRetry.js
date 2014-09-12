function enableLink(el) {
	el.on('click.disabled', false);
}

function disableLink(el) {
	el.off('click.disabled');
}


(function () {

    $.ajaxEpRetry = {
        defaults: {
            size:               16,
            colorRow:           false,
            loadingImage:       'loading16_dddddd.gif',
            noImage:            'no16.png',
            yesImage:           'yes16.png'
        }
    };

    
    
    $.fn.ajaxEpRetry = function (options) {
        options = $.extend({}, $.ajaxEpRetry.defaults, options);

        $('.epRetry').click(function () {
        	event.preventDefault();
            if ( !confirm("Mark download as bad and retry?") )
                return false;

            var parent = $(this).parent();
            link = $(this);
            
            // put the ajax spinner (for non white bg) placeholder while we wait
            img=$(this).children('img');
	        img.attr('title','loading');
			img.attr('alt','');
			img.attr('src','/images/' + options.loadingImage);
			
			$.getJSON($(this).attr('href'), function(data){
	            // if they failed then just put the red X
	            if (data.result == 'failure') {
	                img_name = options.noImage;
	                img_result = 'failed';

	            // if the snatch was successful then apply the corresponding class and fill in the row appropriately
	            } else {
	                img_name = options.loadingImage;
	                img_result = 'success';
	                // color the row
	                if (options.colorRow)
	                	parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
	                // applying the quality class
                    var rSearchTerm = /(\w+)\s\((.+?)\)/;
	                    HtmlContent = data.result.replace(rSearchTerm,"$1"+' <span class="quality '+data.quality+'">'+"$2"+'</span>');
	                // update the status column if it exists
                    parent.siblings('.status_column').html(HtmlContent)    	                  
	            }

	            // put the corresponding image as the result for the the row
	            //parent.empty();
	            //parent.append($("<img/>").attr({"src": sbRoot+"/images/"+img_name, "height": options.size, "alt": img_result, "title": img_result}));
	            img.attr('title',img_result);
				img.attr('alt',img_result);
				img.attr('height', options.size);
				img.attr('src',sbRoot+"/images/"+img_name);
				
	        });
			disableLink(link);
	        // fon't follow the link
	        return false;
	    });
	}
})();

