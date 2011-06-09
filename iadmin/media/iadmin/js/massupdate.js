$(function() {
    $('#col1 input[type=text], #col1 select').each(function() {
        $(this).attr('disabled', 'disabled');
    });
    $('.fastfieldvalue').click(function() {
        var check = $(this).parent().find('.enabler');
        var selection = $(this).text();
        $(check).attr('checked', true);
        var target = $(this).parent().find('input, select').not('.enabler');
        $(target).removeAttr('disabled');
        if ($(target).is('select')) {
            $('option', target).each(function(i, selected) {
                if ($(this).text() == selection) {
                    $(this).attr('selected', true);
                    return;
                }
            });
        } else if ($(target).is('input')) {
            $(target).val(selection);
        }
    });
    $('.enabler').click(function() {
        if ($(this).is(':checked')) {
            $(this).next().removeAttr('disabled');
        } else {
            $(this).next().attr('disabled', 'disabled');
        }
    })
});