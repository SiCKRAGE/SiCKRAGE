/*
 *  Raterater 1.1.1
 *  License: MIT - http://www.opensource.org/licenses/mit-license.php
 *  Author: Bain Mullins - http://bainweb.com
 */

;(function( $ ) {
    var data = {};
    var opts = {};
    var elems = null;
    $.fn.raterater = function(options) {

        /* Default options
         */
        $.fn.raterater.defaults = {
            submitFunction: 'submitRating', // this function will be called when a rating is chosen
            allowChange: false, // allow the user to change their mind after they have submitted a rating
            starWidth: 20, // width of the stars in pixels
            spaceWidth: 5, // spacing between stars in pixels
            numStars: 5
        };

        opts = $.extend( {}, $.fn.raterater.defaults, options );
        opts.width = opts.numStars * ( opts.starWidth + opts.spaceWidth ); // total rating div width
        opts.starAspect = 0.9226; // aspect ratio of the font awesome stars

        elems = this;

        /* First we create ze elements
         */
        init();

        /* Zen we position ze elements
         */
        initializePositions();

        return this;
    }

    function init() {
        
        elems.each( function() {
        
            var $this = $( this );
            var id = dataId( $this );

            /* Uh oh... We really need a data-id or bad things happen
             */
            if( !id ) {
                throw "Error: Each raterater element needs a unique data-id attribute.";
            }

            /* This is where we store our important data for each rating box
             */
            data[id] = {
                state: 'inactive', // inactive, hover, or rated
            };

            /* Make our wrapper relative if it is static so we can position children absolutely
             */
            if( $this.css( 'position' ) === 'static' )
                $this.css( 'position', 'relative' );

            /* Add class raterater-wrapper
             */
            $this.addClass('raterater-wrapper');

            /* Clear out anything inside so we can append the relevent children
             */
            $this.html( '' );

            /* We have 4 div children here as different star layers
             * Layer 1 contains the dull filled stars as a background
             * Layer 2 shows the bright filled stars that represent the current user's rating
             * Layer 3 shows the bright filled stars that represent the item's rating
             * Layer 4 shows the outline stars and is just for looks
             * Layer 5 covers the widget and mainly exists to keep event.offsetX from being ruined by child elements
             */
            $.each( [ 'bg', 'hover', 'rating', 'outline', 'cover' ], function() {
                $this.append(' <div class="raterater-layer raterater-' + this + '-layer"></div>' );
            });

            /* Fill the layers with stars
             */
            for( var i = 0; i < opts.numStars; i++ ) {
                $this.children( '.raterater-bg-layer' ).first()
                    .append( '<i class="fa fa-star"></i>' );
                $this.children( '.raterater-outline-layer' ).first()
                    .append( '<i class="fa fa-star-o"></i>' );
                $this.children( '.raterater-hover-layer' ).first()
                    .append( '<i class="fa fa-star"></i>' );
                $this.children( '.raterater-rating-layer' ).first()
                    .append( '<i class="fa fa-star"></i>' );
            }

            /* Register mouse event callbacks
             */
            $this.find( '.raterater-cover-layer' ).hover( mouseEnter, mouseLeave );
            $this.find( '.raterater-cover-layer' ).mousemove( hiliteStarsHover );
            $this.find( '.raterater-cover-layer' ).click( rate );
        });
    }

    function initializePositions() {
        elems.each( function() {
           
            var $this = $( this );
            var id = dataId( $this );
        
            /* Set the width and height of the raterater wrapper and layers
             */
            var width = opts.width + 'px';
            var height = Math.floor( opts.starWidth / opts.starAspect ) + 'px';
            $this.css( 'width', width )
                .css( 'height', height );
            $this.find( '.raterater-layer' ).each(function(){
                $( this ).css( 'width', width )
                    .css( 'height', height );
            });

            /* Absolutely position the stars (necessary for partial stars)
             */
            for( var i = 0; i < opts.numStars; i++ ) {
                $.each( [ 'bg', 'hover', 'rating', 'outline' ], function() {
                    $this.children( '.raterater-' + this + '-layer' ).first().children( 'i' ).eq( i )
                        .css( 'left', i * ( opts.starWidth + opts.spaceWidth ) + 'px' )
                        .css( 'font-size', Math.floor( opts.starWidth / opts.starAspect ) + 'px');
                });
            }

            /* show the item's current rating on the raterater-rating-layer
             */
            var rating = parseFloat( $this.attr( 'data-rating' ) );
            var whole = Math.floor( rating );
            var partial = rating - whole;
            hiliteStars (
                $this.find( '.raterater-rating-layer' ).first(), 
                whole, 
                partial
            );
        });
    }

    function rate(e) {
        var $this = $( e.target ).parent();
        var id = dataId( $this );
        var stars = data[id].whole_stars_hover + data[id].partial_star_hover;

        /* Round stars to 2 decimals
         */
        stars = Math.round( stars * 100 ) / 100;

        /* Set the state to 'rated' to disable functionality
         */
        data[id].state = 'rated';

        /* Add the 'rated' class to the hover layer for additional styling flexibility
         */
        $this.find( '.raterater-hover-layer' ).addClass( 'rated' );

        /* Call the user-defined callback function if it exists
         */
        if( typeof window[opts.submitFunction] === 'function' );
            window[opts.submitFunction]( id, stars );
    }

    /* Calculate the number of stars from the x position of the mouse relative to the cover layer
     * (This is only compicated because of the spacing between stars)
     */
    function calculateStars(x, id) {

        /* Whole star = floor( x / ( star_width + space_width ) ) 
         */
        var whole_stars = Math.floor( x / ( opts.starWidth + opts.spaceWidth ) );

        /* Partial star = max( 1, ( x - whole_stars * ( star_width + space_width ) ) / star_width )
         */
        var partial_star = x - whole_stars * ( opts.starWidth + opts.spaceWidth );
        if( partial_star > opts.starWidth )
            partial_star = opts.starWidth;
        partial_star /= opts.starWidth;

        /* Store our result in the data object
         */
        data[id].whole_stars_hover = whole_stars;
        data[id].partial_star_hover = partial_star;
    }

    /* Given a layer object and rating data, highlight the stars
     */
    function hiliteStars($layer, whole, partial) {
        var id = dataId( $layer.parent() );

        /* highlight the 'whole' stars
         */
        for( var i = 0; i < whole; i++ ) {
            $layer.find( 'i' ).eq( i )
                .css( 'width', opts.starWidth + 'px' );
        }

        /* highlight the partial star
         */
        $layer.find( 'i' ).eq( whole )
            .css( 'width', opts.starWidth * partial + 'px' );

        /* clear the extra stars
         */
        for( var i = whole+1; i < opts.numStars; i++) {
            $layer.find( 'i' ).eq( i )
                .css( 'width', '0px' );
        }
    }

    /* Highlight the hover layer stars
     * This is the callback for the mousemove event
     */
    function hiliteStarsHover(e) {
        var id = dataId( $( e.target ).parent() );
        
        /* Leave it alone, we aren't hovering
         */
        if( data[id].state !== 'hover' ) {
            return;
        }

        /* Get the mouse offsetX
         */
        var x = e.offsetX;

        /* Firefox requires a pageX hack
         */
        if(x === undefined) {
            x = e.pageX - $( e.target ).offset().left;
        }

        data[id].stars = calculateStars( x, id );

        /* Find the layer element
         */
        var $layer = $( e.target ).parent().children( '.raterater-hover-layer' ).first();

        /* Call the more generic highlighting function
         */
        hiliteStars( $layer, data[id].whole_stars_hover, data[id].partial_star_hover );
    }

    /* Active this rating box
     * This is the callback for the mouseenter event 
     */
    function mouseEnter(e) {
        var id = dataId( $( e.target ).parent() );

        /* Leave it alone, we have already rated this item
         */
        if( data[id].state === 'rated' && !opts.allowChange ) {
            return;
        }

        /* set the state to 'hover'
         */
        data[id].state = 'hover';

        /* show the hover layer and hide the rating layer
         */
        $( e.target ).parent().children( '.raterater-rating-layer' ).first().css( 'display', 'none' );
        $( e.target ).parent().children( '.raterater-hover-layer' ).first().css( 'display','block' );
    }

    /* Deactivate this rating box
     * This is the callback for the mouseleave event 
     */
    function mouseLeave(e) {
        var id = dataId( $( e.target ).parent() );

        /* Leave it alone, we have already rated this item
         */
        if( data[id].state === 'rated' ) {
            return;
        }

        /* set the state to 'inactive'
         */
        data[id].state = 'inactive';

        /* hide the hover layer and show the rating layer
         */
        $( e.target ).parent().children( '.raterater-hover-layer' ).first().css( 'display', 'none' );
        $( e.target ).parent().children( '.raterater-rating-layer' ).first().css( 'display','block' );
    }

    /* Shorthand function to get the data-id of an element
     */
    function dataId(e) {
        return $( e ).attr( 'data-id' );
    }

})( jQuery );