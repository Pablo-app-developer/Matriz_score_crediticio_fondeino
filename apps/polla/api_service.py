"""
Servicio de datos previos al partido usando api-football.com (RapidAPI).

Flujo:
  1. Se llama get_datos_partido(partido)
  2. Si hay caché válido (< TTL), se devuelve directo
  3. Si no, se consultan 3 endpoints (H2H + forma local + forma visitante)
  4. El resultado se serializa en partido.datos_previos (JSONField)

Requiere: settings.API_FOOTBALL_KEY y equipo.api_football_id en ambos equipos.
"""
import requests
from django.conf import settings
from django.utils import timezone

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
TTL_SEGUNDOS = 6 * 3600  # 6 horas de caché


def _api_key():
    return getattr(settings, 'API_FOOTBALL_KEY', '') or ''


def _get(endpoint, params):
    key = _api_key()
    if not key:
        return None
    try:
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers={
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
            },
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get('response', [])
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

    # H2H (últimos 10 partidos oficiales finalizados)
    h2h_raw = _get('fixtures/headtohead', {
        'h2h': f'{id_local}-{id_vis}',
        'last': 10,
        'status': 'FT',
    })
    if h2h_raw is not None:
        datos['h2h'] = _parse_h2h(h2h_raw, id_local, id_vis)

    # Forma reciente local (últimos 5 partidos finalizados)
    forma_l = _get('fixtures', {'team': id_local, 'last': 5, 'status': 'FT'})
    if forma_l is not None:
        datos['forma_local'] = _parse_forma(forma_l, id_local)

    # Forma reciente visitante
    forma_v = _get('fixtures', {'team': id_vis, 'last': 5, 'status': 'FT'})
    if forma_v is not None:
        datos['forma_visitante'] = _parse_forma(forma_v, id_vis)

    if datos:
        partido.datos_previos = datos
        partido.datos_previos_ts = timezone.now()
        partido.save(update_fields=['datos_previos', 'datos_previos_ts'])

    return datos or None


def _parse_h2h(fixtures, id_local, id_vis):
    victorias_local = 0
    empates = 0
    victorias_vis = 0
    ultimos = []

    for f in fixtures:
        home_id = f['teams']['home']['id']
        hg = f['goals']['home']
        ag = f['goals']['away']
        if hg is None or ag is None:
            continue

        if home_id == id_local:
            gl, gv = hg, ag
            nombre_l = f['teams']['home']['name']
            nombre_v = f['teams']['away']['name']
        else:
            gl, gv = ag, hg
            nombre_l = f['teams']['away']['name']
            nombre_v = f['teams']['home']['name']

        if gl > gv:
            victorias_local += 1
        elif gl < gv:
            victorias_vis += 1
        else:
            empates += 1

        ultimos.append({
            'fecha': f['fixture']['date'][:10],
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


def _parse_forma(fixtures, team_id):
    forma = []
    for f in fixtures:
        home_id = f['teams']['home']['id']
        hg = f['goals']['home']
        ag = f['goals']['away']
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
