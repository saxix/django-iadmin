Resolver = null;
(function($) {
    $(document).ready(function() {
        $("#nojsmessage").hide();
    });
    
    Resolver = function() {
            return {
                reverse: function(name, args) {
                    var ret;
                    var arguments = {};
                    var c = 0;

                    // Convert args to keyed dictionary
                    for (i in args) {
                        arguments[c] = args[i];
                        c++;
                    }

                    $.ajax({
                        async: false,
                        url: '/admin/i/reverse/' + name + '/',
                        data: arguments,
                        success: function(html) {
                            ret = html;
                        }
                    });

                    if (ret.length > 0) {
                        return ret;
                    }
                    else {
                        return null;
                    }

                }
            }
        }();
})(jQuery);