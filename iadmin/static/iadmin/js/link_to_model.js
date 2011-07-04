(function($) {
    $(document).ready(function() {
        jQuery('.link_to_model').each(function() {
            $(this).click(function() {
                var target = $(this).attr('id').replace(new RegExp("^edit_", "gi"), '#');
                var val = $(target).val();
                var view = $(this).attr('name');
                if ( val && view ){
                    var url = Resolver.reverse(view, [val] );
                    window.location = url;
                }
            });

        });
    });
})(jQuery);
       