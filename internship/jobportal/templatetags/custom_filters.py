from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """
    Splits a string by the given argument.
    Usage: {{ "a,b,c"|split:"," }}
    """
    if value:
        return value.split(arg)
    return []

@register.filter
def trim(value):
    """
    Removes leading and trailing whitespace.
    Usage: {{ " hello "|trim }}
    """
    if value:
        return str(value).strip()
    return value
