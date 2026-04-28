from django import template

register = template.Library()


@register.filter
def sum_field(lst, field):
    """Suma un campo de una lista de dicts: {{ plan|sum_field:"interes" }}"""
    try:
        return sum(item[field] for item in lst)
    except (KeyError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    return float(value) * float(arg)


@register.filter
def pct(value):
    return f"{float(value) * 100:.2f}%"


@register.filter
def cop(value):
    """Formato colombiano: 1250000 → 1.250.000"""
    try:
        val = int(round(float(value)))
        return f"{val:,}".replace(",", ".")
    except (TypeError, ValueError):
        return value
