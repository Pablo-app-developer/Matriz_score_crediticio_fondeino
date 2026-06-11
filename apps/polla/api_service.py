"""
Servicio de estadísticas previas al partido.

Usa la propia BD de la Polla (modelo Partido con resultados cargados).
No requiere ninguna API externa ni clave de configuración.

- Forma: últimos partidos finalizados de cada equipo en este torneo
- H2H: partidos finalizados donde se enfrentaron ambos equipos
"""
from django.db.models import Q


def get_datos_partido(partido):
    """
    Devuelve dict con forma e H2H calculados desde la BD interna.
    Retorna None si no hay ningún partido finalizado relevante aún.
    """
    from .models import Partido  # importación local para evitar circular

    local = partido.equipo_local
    vis   = partido.equipo_visitante

    qs_finalizados = Partido.objects.filter(
        goles_local__isnull=False,
        goles_visitante__isnull=False,
        finalizado=True,
    ).exclude(pk=partido.pk).select_related('equipo_local', 'equipo_visitante')

    datos = {}

    # ── Forma local: últimos 5 partidos jugados por el equipo local ──
    matches_local = list(
        qs_finalizados.filter(
            Q(equipo_local=local) | Q(equipo_visitante=local)
        ).order_by('-fecha_hora')[:5]
    )
    if matches_local:
        datos['forma_local'] = _calcular_forma(matches_local, local)

    # ── Forma visitante: últimos 5 partidos jugados por el equipo visitante ──
    matches_vis = list(
        qs_finalizados.filter(
            Q(equipo_local=vis) | Q(equipo_visitante=vis)
        ).order_by('-fecha_hora')[:5]
    )
    if matches_vis:
        datos['forma_visitante'] = _calcular_forma(matches_vis, vis)

    # ── H2H: partidos entre estos dos equipos ──
    h2h_matches = list(
        qs_finalizados.filter(
            Q(equipo_local=local, equipo_visitante=vis) |
            Q(equipo_local=vis,   equipo_visitante=local)
        ).order_by('-fecha_hora')[:5]
    )
    if h2h_matches:
        datos['h2h'] = _calcular_h2h(h2h_matches, local, vis)

    return datos or None


def _calcular_forma(matches, equipo):
    forma = []
    for m in matches:
        if m.equipo_local == equipo:
            gl, gv = m.goles_local, m.goles_visitante
        else:
            gl, gv = m.goles_visitante, m.goles_local
        if gl > gv:
            forma.append('W')
        elif gl < gv:
            forma.append('L')
        else:
            forma.append('D')
    return forma


def _calcular_h2h(matches, local, vis):
    victorias_local = 0
    empates = 0
    victorias_vis = 0
    ultimos = []

    for m in matches:
        if m.equipo_local == local:
            gl, gv = m.goles_local, m.goles_visitante
            nombre_l = local.nombre
            nombre_v = vis.nombre
        else:
            gl, gv = m.goles_visitante, m.goles_local
            nombre_l = vis.nombre
            nombre_v = local.nombre

        if gl > gv:
            victorias_local += 1
        elif gl < gv:
            victorias_vis += 1
        else:
            empates += 1

        ultimos.append({
            'fecha': m.fecha_hora.strftime('%Y-%m-%d'),
            'local': nombre_l,
            'visitante': nombre_v,
            'marcador': f'{m.goles_local}-{m.goles_visitante}',
        })

    return {
        'victorias_local': victorias_local,
        'empates': empates,
        'victorias_visitante': victorias_vis,
        'total': victorias_local + empates + victorias_vis,
        'ultimos': ultimos,
    }
