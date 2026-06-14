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
    from apps.polla.models import Pronostico as _P

    puntos_total = 0
    aciertos_resultado = 0
    aciertos_marcador = 0
    pronosticos_a_actualizar = []

    for pronostico in inscripcion.pronosticos.select_related('partido').all():
        partido = pronostico.partido
        resultado = calcular_puntos(pronostico, partido, config)

        pronostico.puntos_obtenidos = resultado['puntos']
        pronostico.acerto_resultado = resultado['acerto_resultado']
        pronostico.acerto_marcador = resultado['acerto_marcador']
        pronosticos_a_actualizar.append(pronostico)

        puntos_total += resultado['puntos']
        if resultado['acerto_resultado']:
            aciertos_resultado += 1
        if resultado['acerto_marcador']:
            aciertos_marcador += 1

    # bulk_update bypasa el save() del modelo (evita el bloqueo de partidos cerrados)
    if pronosticos_a_actualizar:
        _P.objects.bulk_update(
            pronosticos_a_actualizar,
            ['puntos_obtenidos', 'acerto_resultado', 'acerto_marcador'],
        )

    inscripcion.puntos_totales = puntos_total
    inscripcion.aciertos_resultado = aciertos_resultado
    inscripcion.aciertos_marcador = aciertos_marcador
    inscripcion.save(update_fields=['puntos_totales', 'aciertos_resultado', 'aciertos_marcador'])


def snapshot_posiciones():
    """Captura la posición global actual en `posicion_anterior` para cada
    inscripción visible en el ranking. Llamar antes de un recálculo para
    poder mostrar el delta de posición (▲/▼) tras los nuevos resultados.

    Filtra por `afiliado__user__isnull=False` para coincidir con la vista
    de ranking — si no, las posiciones se inflan por inscripciones sin
    cuenta enlazada y los deltas saldrían erróneos.
    """
    from apps.polla.models import InscripcionPolla

    qs = InscripcionPolla.objects.filter(
        activa=True, afiliado__user__isnull=False,
    ).order_by(
        '-puntos_totales', '-aciertos_marcador', '-aciertos_resultado',
        'afiliado__nombre_completo',
    )
    a_actualizar = []
    for pos, insc in enumerate(qs, start=1):
        if insc.posicion_anterior != pos:
            insc.posicion_anterior = pos
            a_actualizar.append(insc)
    if a_actualizar:
        InscripcionPolla.objects.bulk_update(a_actualizar, ['posicion_anterior'])


def recalcular_todo(config=None):
    """Recalcula puntos de todas las inscripciones activas. Idempotente.

    Antes del recálculo guarda la posición global actual de cada inscripción
    en `posicion_anterior` para poder mostrar el delta tras los nuevos
    resultados.
    """
    from apps.polla.models import ConfiguracionPolla, InscripcionPolla

    if config is None:
        config = ConfiguracionPolla.get()

    snapshot_posiciones()

    inscripciones = InscripcionPolla.objects.filter(activa=True).prefetch_related(
        'pronosticos__partido'
    )
    for inscripcion in inscripciones:
        recalcular_inscripcion(inscripcion, config)

    return inscripciones.count()
