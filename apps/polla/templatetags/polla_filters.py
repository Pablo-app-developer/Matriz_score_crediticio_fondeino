from django import template

register = template.Library()


@register.filter
def medalla(posicion):
    return {1: '🥇', 2: '🥈', 3: '🥉'}.get(posicion, '')


@register.filter
def resultado_icon(acerto):
    return '✅' if acerto else '❌'


@register.filter
def resultado_clase(acerto_resultado, acerto_marcador):
    """Devuelve la clase CSS según el tipo de acierto."""
    if acerto_marcador:
        return 'table-success'
    if acerto_resultado:
        return 'table-warning'
    return ''


@register.simple_tag
def puntos_posibles_grupos(config):
    return config.pts_resultado_grupos + config.pts_marcador_grupos


@register.simple_tag
def puntos_posibles_eliminatoria(config):
    return config.pts_resultado_eliminatoria + config.pts_marcador_eliminatoria
