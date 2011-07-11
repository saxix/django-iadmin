
# this module manage 1.2 - 1.3 differences
try:
    from django.core.context_processors import static
except ImportError:
    from django.conf import settings
    def static(request):
        """
        Adds static-related context variables to the context.

        """
        return {'STATIC_URL': settings.STATIC_URL}