/**
 *
 * User: sax
 * Date: 1/2/12
 * Time: 11:29 AM
 *
 */
(function($) {
    $.fn.filter_horizontal = function() {
        var avail_width = $(document).width();
        var new_size = (avail_width-300)/2;
        if (new_size > 270){
            $('.selector').width(avail_width-200);
            $('.selector-available, .selector-chosen, .selector-available select, .selector-chosen select').width(new_size);
        }
    };
    addEvent(window, "resize", function(e) {$.fn.filter_horizontal(); });
})(django.jQuery);