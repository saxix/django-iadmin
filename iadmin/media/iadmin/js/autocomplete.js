(function($) {
    $(document).ready(function() {
        function formatItem(row) {
            return row[1];
        }

        function formatResult(row) {
            return row[1];
        }

        $(".autocomplete").each(function() {
            var url = $(this).next().val();
            $(this).autocomplete(url, { formatResult:formatResult, formatItem:formatItem});
        })

        $(".autocomplete").result(function(event, data, formatted) {
            $(this).prev().val(formatted);
        });

        $('.add-row a').click(function() {
            $(".autocomplete").each(function() {
                var url = $(this).next().val();
                $(this).autocomplete(url, { formatResult:formatResult, formatItem:formatItem});
            })
        })
    });
})(jQuery)
