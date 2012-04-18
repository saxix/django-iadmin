Resolver = null;
Array.prototype.remove= function(){
    var what, a= arguments, L= a.length, ax;
    while(L && this.length){
        what= a[--L];
        while((ax= this.indexOf(what))!= -1){
            this.splice(ax, 1);
        }
    }
    return this;
};

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
})(django.jQuery);
