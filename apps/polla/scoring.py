from django.db.models import Sum


def calcular_puntos(pronostico, partido, config):
    """Función pura. Retorna dict con puntos y aciertos para un pronóstico."""
    if not partido.finalizado or partido.goles_local is None:
        return {'puntos': 0, 'acerto_resultado': False, 'acerto_marcador': False}

    resultado_real = partido.resultado_texto
    resultado_pronosticado = pronostico.resultado_pronosticado

    acerto_resultado = (resultado_real == resultado_pronosticado)
    acerto_marcador = (
        pronostico.goles_local == partido.goles_local
        and pronostico.goles_visitante == partido.goles_visitante
    )

    puntos = 0
    if partido.es_eliminatoria:
        if acerto_resultado:
            puntos += config.pts_resultado_eliminatoria
        if acerto_marcador:
            puntos += config.pts_marcador_eliminatoria
    else:
        if acerto_resultado:
            puntos += config.pts_resultado_grupos
        if acerto_marcador:
            puntos += config.pts_marcador_grupos

    return {
        'puntos': puntos,
        'acerto_resultado': acerto_resultado,
        'acerto_marcador': acerto_marcador,
    }


def recalcular_inscripcion(inscripcion, config):
    """Recalcula y persiste los puntos de una inscripción. Idempotente."""
    puntos_total = 0
    aciertos_resultado = 0
    aciertos_marcador = 0

    for pronostico in inscripcion.pronosticos.select_related('partido').all():
        partido = pronostico.partido
        resultado = calcular_puntos(pronostico, partido, config)

        pronostico.puntos_obtenidos = resultado['puntos']
        pronostico.acerto_resultado = resultado['acerto_resultado']
        pronostico.acerto_marcador = resultado['acerto_marcador']
        pronostico.save(update_fields=['puntos_obtenidos', 'acerto_resultado', 'acerto_marcador'])

        puntos_total += resultado['puntos']
        if resultado['acerto_resultado']:
            aciertos_resultado += 1
        if resultado['acerto_marcador']:
            aciertos_marcador += 1

    inscripcion.puntos_totales = puntos_total
    inscripcion.aciertos_resultado = aciertos_resultado
    inscripcion.aciertos_marcador = aciertos_marcador
    inscripcion.save(update_fields=['puntos_totales', 'aciertos_resultado', 'aciertos_marcador'])


def recalcular_todo(config=None):
    """Recalcula puntos de todas las inscripciones activas. Idempotente."""
    from apps.polla.models import ConfiguracionPolla, InscripcionPolla

    if config is None:
        config = ConfiguracionPolla.get()

    inscripciones = InscripcionPolla.objects.filter(activa=True).prefetch_related(
        'pronosticos__partido'
    )
    for inscripcion in inscripciones:
        recalcular_inscripcion(inscripcion, config)

    return inscripciones.count()
