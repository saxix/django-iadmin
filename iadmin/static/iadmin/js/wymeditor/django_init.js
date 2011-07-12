(function($) {
    $(document).ready(function() {
        $("#id_content").wymeditor({ // "FIELDNAME" is the name of the field you want to give the wysiwyg features
            updateSelector: "input:submit",
            updateEvent: "click"
        });
    });
})(jQuery);
