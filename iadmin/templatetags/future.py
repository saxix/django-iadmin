
from django import template

register = template.Library()

try:
    register.simple_tag(takes_context=True)
except TypeError:
    from django.template import Node, Variable, generic_tag_compiler, TemplateSyntaxError
    from django.utils.functional import curry
    from inspect import getargspec

    def simple_tag(self, func=None, takes_context=None):
        def dec(func):
            params, xx, xxx, defaults = getargspec(func)
            if takes_context:
                if params[0] == 'context':
                    params = params[1:]
                else:
                    raise TemplateSyntaxError("Any tag function decorated with takes_context=True must have a first argument of 'context'")

            class SimpleNode(Node):
                def __init__(self, vars_to_resolve):
                    self.vars_to_resolve = map(Variable, vars_to_resolve)

                def render(self, context):
                    resolved_vars = [var.resolve(context) for var in self.vars_to_resolve]
                    if takes_context:
                        func_args = [context] + resolved_vars
                    else:
                        func_args = resolved_vars
                    return func(*func_args)

            compile_func = curry(generic_tag_compiler, params, defaults, getattr(func, "_decorated_function", func).__name__, SimpleNode)
            compile_func.__doc__ = func.__doc__
            self.tag(getattr(func, "_decorated_function", func).__name__, compile_func)
            return func

        if func is None:
            # @register.simple_tag(...)
            return dec
        elif callable(func):
            # @register.simple_tag
            return dec(func)
        else:
            raise TemplateSyntaxError("Invalid arguments provided to simple_tag")

    setattr(register.__class__, 'simple_tag', simple_tag)



