$(document).ready(function() { 

    function make_row(indexer_id, season, episode, name, checked) {
        if (checked)
            var checked = ' checked';
        else
            var checked = '';
        
        var row_class = $('#row_class').val();
        
        var row = '';
        row += ' <tr class="'+row_class+'">';
        row += '  <td><input type="checkbox" class="'+indexer_id+'-epcheck" name="'+indexer_id+'-'+season+'x'+episode+'"'+checked+'></td>';
        row += '  <td>'+season+'x'+episode+'</td>';
        row += '  <td style="width: 100%">'+name+'</td>';
        row += ' </tr>'
        
        return row;
    }

    $('.allCheck').click(function(){
        var indexer_id = $(this).attr('id').split('-')[1];
        $('.'+indexer_id+'-epcheck').prop('checked', $(this).prop('checked'));
    });

    $('.get_more_eps').click(function(){
        var cur_indexer_id = $(this).attr('id');
        var checked = $('#allCheck-'+cur_indexer_id).prop('checked');
        var last_row = $('tr#'+cur_indexer_id);
        
        $.getJSON(sbRoot+'/manage/showEpisodeStatuses',
                  {
                   indexer_id: cur_indexer_id,
                   whichStatus: $('#oldStatus').val()
                  },
                  function (data) {
                      $.each(data, function(season,eps){
                          $.each(eps, function(episode, name) {
                              //alert(season+'x'+episode+': '+name);
                              last_row.after(make_row(cur_indexer_id, season, episode, name, checked));
                          });
                      });
                  });
        $(this).hide();
    });

    // selects all visible episode checkboxes.
    $('.selectAllShows').click(function(){
        $('.allCheck').each(function(){
                this.checked = true;
        });
        $('input[class*="-epcheck"]').each(function(){
                this.checked = true;
        });
    });

    // clears all visible episode checkboxes and the season selectors
    $('.unselectAllShows').click(function(){
        $('.allCheck').each(function(){
                this.checked = false;
        });
        $('input[class*="-epcheck"]').each(function(){
                this.checked = false;
        });
    });

});