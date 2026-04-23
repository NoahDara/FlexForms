from django import template

register = template.Library()


@register.filter
def dictkey(d, key):
    """
    Returns d[key] from a dictionary. Useful in templates where the key is
    a variable (e.g. a model PK) rather than a string literal.

    Usage:
        {{ my_dict|dictkey:some_variable }}
    """
    return d.get(key, '')


@register.filter
def avatar_color(n):
    """
    Returns a cycling hex colour based on an integer index.
    Used to give each avatar a distinct background colour.

    Usage:
        {{ forloop.counter|avatar_color }}
    """
    colors = ['#6576ff', '#09c2de', '#1ee0ac', '#f4bd0e', '#e85347']
    return colors[(int(n) - 1) % len(colors)]