"""
Servicio de datos previos al partido usando football-data.org (API gratuita).

Requiere: settings.FOOTBALL_DATA_KEY y equipo.api_football_id en ambos equipos.
"""
import requests
from django.conf import settings
from django.utils import timezone

BASE_URL = "https://api.football-data.org/v4"
TTL_SEGUNDOS = 6 * 3600  # 6 horas de caché


def _api_key():
    return getattr(settings, 'FOOTBALL_DATA_KEY', '') or ''


def _get(endpoint, params=None):
    key = _api_key()
    if not key:
        return None
    try:
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers={"X-Auth-Token": key},
            params=params or {},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_datos_partido(partido):
    """
    Devuelve dict con datos previos del partido, usando caché JSONField.
    Retorna None si la API no está configurada o los equipos no tienen api_football_id.
    """
    if not _api_key():
        return None

    id_local = partido.equipo_local.api_football_id
    id_vis = partido.equipo_visitante.api_football_id
    if not id_local or not id_vis:
        return None

    # Verificar caché
    if partido.datos_previos and partido.datos_previos_ts:
        age = (timezone.now() - partido.datos_previos_ts).total_seconds()
        if age < TTL_SEGUNDOS:
            return partido.datos_previos

    datos = {}

    # Últimos 20 partidos del equipo local (para H2H + forma)
    resp_local = _get(f'teams/{id_local}/matches', {'status': 'FINISHED', 'limit': 20})
    matches_local = (resp_local or {}).get('matches', [])

    # Últimos 5 partidos del equipo visitante (para forma)
    resp_vis = _get(f'teams/{id_vis}/matches', {'status': 'FINISHED', 'limit': 5})
    matches_vis = (resp_vis or {}).get('matches', [])

    if matches_local:
        h2h_matches = [
            m for m in matches_local
            if m['homeTeam']['id'] == id_vis or m['awayTeam']['id'] == id_vis
        ]
        if h2h_matches:
            datos['h2h'] = _parse_h2h(h2h_matches, id_local, id_vis)

        datos['forma_local'] = _parse_forma(matches_local[-5:], id_local)

    if matches_vis:
        datos['forma_visitante'] = _parse_forma(matches_vis, id_vis)

    if datos:
        partido.datos_previos = datos
        partido.datos_previos_ts = timezone.now()
        partido.save(update_fields=['datos_previos', 'datos_previos_ts'])

    return datos or None


def _parse_h2h(matches, id_local, id_vis):
    victorias_local = 0
    empates = 0
    victorias_vis = 0
    ultimos = []

    for m in matches:
        home_id = m['homeTeam']['id']
        score = m.get('score', {}).get('fullTime', {})
        hg = score.get('home')
        ag = score.get('away')
        if hg is None or ag is None:
            continue

        if home_id == id_local:
            gl, gv = hg, ag
            nombre_l = m['homeTeam']['name']
            nombre_v = m['awayTeam']['name']
        else:
            gl, gv = ag, hg
            nombre_l = m['awayTeam']['name']
            nombre_v = m['homeTeam']['name']

        if gl > gv:
            victorias_local += 1
        elif gl < gv:
            victorias_vis += 1
        else:
            empates += 1

        ultimos.append({
            'fecha': m['utcDate'][:10],
            'local': nombre_l,
            'visitante': nombre_v,
            'marcador': f'{hg}-{ag}',
        })

    return {
        'victorias_local': victorias_local,
        'empates': empates,
        'victorias_visitante': victorias_vis,
        'total': victorias_local + empates + victorias_vis,
        'ultimos': ultimos[:5],
    }


def _parse_forma(matches, team_id):
    forma = []
    for m in matches:
        home_id = m['homeTeam']['id']
        score = m.get('score', {}).get('fullTime', {})
        hg = score.get('home')
        ag = score.get('away')
        if hg is None or ag is None:
            continue

        gl = hg if home_id == team_id else ag
        gv = ag if home_id == team_id else hg

        if gl > gv:
            forma.append('W')
        elif gl < gv:
            forma.append('L')
        else:
            forma.append('D')

    return forma[-5:]
