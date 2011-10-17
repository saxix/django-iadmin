(function($) {
    $(document).ready(function() {
        function formatItem(row) {
            return row[1];
        };

        function formatResult(row) {
            return row[1];
        };

        enable_autocomplete = function(){
            $(".autocomplete").each(function() {
                var url = $(this).next().val();
                $(this).autocomplete(url, { formatResult:formatResult, formatItem:formatItem})
                        .result(function(event, data, formatted) {$(this).prev().val(formatted);})
                            .focus(function(){$(this).prev().val('');})
//                        .blur(function(){$(this).search();});
            })
        };

        $('.add-row a').click(function() {
            enable_autocomplete();
        });
        
        enable_autocomplete();

    });
})(jQuery);
