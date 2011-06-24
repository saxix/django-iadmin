(function($) {
    $(document).ready(function() {
        jQuery('.link_to_model').each(function() {
            $(this).click(function() {
                var target = $(this).attr('id').replace(/^edit_/, '#');
                var val = $(target).val();
                var view = $(this).attr('name');
                console.log( target, val, view  );
                if ( val && view ){
                    var url = Resolver.reverse(view, [val] );
                    window.location = url;
                }
            });

        });
    });
})(jQuery);
       