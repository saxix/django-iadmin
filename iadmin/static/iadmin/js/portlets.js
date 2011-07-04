var init_portlets = function($, prefix) {
    var COOKIE_NAME = 'layout' + prefix;
    $.unparam = function (value) {
        var params = {}, pieces = value.split('&'), pair, i, l;
        // Loop through query string pieces and assign params.
        for (i = 0,l = pieces.length; i < l; i++) {
            pair = pieces[i].split('=', 2);
            // Repeated parameters with the same name are overwritten. Parameters
            // with no value get set to boolean true.
            params[decodeURIComponent(pair[0])] = (pair.length == 2 ?
                    decodeURIComponent(pair[1].replace(/\+/g, ' ')) : true);
        }
        return params;
    };
    var save_layout = function() {
        $('.column').each(function(index, value) {
            //var column = $(this).attr('id');
            var p = new Array();
            $('.portlet', this).each(function() {
                p.push($(this).attr('id') + ":" + $(this).find(".portlet-content").is(":visible"));
            });
            layout[index] = p.join(",");
        });
        $.cookie(COOKIE_NAME, $.param(layout), { expires: 365, path: '/' });
    }

    var restore_layout = function() {
        var layout = $.unparam($.cookie( COOKIE_NAME ));
        var column = null, portlets = null, params = null;
        $('.column').each(function(col) {
            //column = $(this).attr('id');
            portlets = layout[col].split(",");
            $.each(portlets, function(index, value) {
                if (value) {
                    params = value.split(":");
                    var portlet = $('#' + params[0]);
                    $(portlet).detach().appendTo('#column' + (1+col));
                    if (params[1] == "false") {
                        $(portlet).find(".portlet-content").hide();
                    }
                }
            });
        });
    }

    var layout = {}
    $(function() {
        $(".column").sortable({
            connectWith: ".column",
            stop: function(event, ui) {
                save_layout();
            }
        });

        $(".portlet").addClass("ui-widget ui-widget-content ui-helper-clearfix ui-corner-all")
                .find(".portlet-header")
                .addClass("ui-widget-header ui-corner-all")
                .prepend("<span class='ui-icon ui-icon-minusthick'></span>")
                .end()
                .find(".portlet-content");

        $(".portlet-header .ui-icon").click(function() {
            $(this).toggleClass("ui-icon-minusthick").toggleClass("ui-icon-plusthick");
            $(this).parents(".portlet:first").find(".portlet-content").toggle();
            save_layout();
        });

        $(".column").disableSelection();

        $(window).load(function() {
            restore_layout();
        });
    });

};