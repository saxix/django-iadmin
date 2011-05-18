var init_portlets = function($){
//       var $ = jQuery;
        $(function() {
            $(".column").sortable({
                        connectWith: ".column",
                        stop: function(event, ui) {
                            $('.column').each(function() {
                                var column = $(this).attr('id');
//                                 console.log( column );
                                var x = new Array()
                                $('.portlet', this).each(function() {
                                    var portlet = $(this).attr('id');
                                    x.push(portlet);
                                });
//                                 console.log( x.join() );
                                $.cookie(column, x);
                            });
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
            });

            $(".column").disableSelection();

            $(window).load(function() {
                $('.column').each(function() {
                    var column = $(this).attr('id');
                    var ck = $.cookie(column);
//                    console.log( ck );
                    var e = ck.split(',');
                    $.each(e, function(index, value) {
                        var portlet = $('#' + value);
                        $(portlet).detach().appendTo('#' + column);
//                        console.log( column, value );
                    });

                });
            });
        });

}