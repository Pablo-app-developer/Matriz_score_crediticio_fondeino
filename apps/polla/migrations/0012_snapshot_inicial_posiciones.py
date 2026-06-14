from django.db import migrations


def snapshot_inicial(apps, schema_editor):
    """Inicializa `posicion_anterior` retroactivamente: calcula la posición
    que cada inscripción tenía ANTES del último partido finalizado, restando
    sus puntos/aciertos del último pronóstico. Así los deltas (▲/▼) ya
    reflejan la última jornada sin tener que esperar al próximo partido.
    """
    Partido = apps.get_model('polla', 'Partido')
    InscripcionPolla = apps.get_model('polla', 'InscripcionPolla')
    Pronostico = apps.get_model('polla', 'Pronostico')

    ultimo = Partido.objects.filter(finalizado=True).order_by('-fecha_hora').first()
    if ultimo is None:
        return

    inscripciones = list(
        InscripcionPolla.objects.filter(
            activa=True, afiliado__user__isnull=False,
        ).select_related('afiliado')
    )
    if not inscripciones:
        return

    pron_ultimo = {
        p.inscripcion_id: p
        for p in Pronostico.objects.filter(partido=ultimo)
    }

    scores = []
    for insc in inscripciones:
        p = pron_ultimo.get(insc.pk)
        if p:
            pts = insc.puntos_totales - p.puntos_obtenidos
            am = insc.aciertos_marcador - (1 if p.acerto_marcador else 0)
            ar = insc.aciertos_resultado - (1 if p.acerto_resultado else 0)
        else:
            pts = insc.puntos_totales
            am = insc.aciertos_marcador
            ar = insc.aciertos_resultado
        scores.append((insc, pts, am, ar))

    scores.sort(key=lambda x: (-x[1], -x[2], -x[3], x[0].afiliado.nombre_completo))

    a_actualizar = []
    for pos, (insc, *_) in enumerate(scores, start=1):
        insc.posicion_anterior = pos
        a_actualizar.append(insc)

    InscripcionPolla.objects.bulk_update(a_actualizar, ['posicion_anterior'])


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0011_inscripcionpolla_posicion_anterior'),
    ]

    operations = [
        migrations.RunPython(snapshot_inicial, migrations.RunPython.noop),
    ]
