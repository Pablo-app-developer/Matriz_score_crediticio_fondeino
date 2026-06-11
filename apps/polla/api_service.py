"""
Servicio de estadísticas previas al partido usando football-data.org (plan gratuito).

- Forma WC 2026: partidos del torneo actual filtrados por equipo
- H2H histórico: WC 2022 y 2018 (mismos equipos en mundiales anteriores)
- Caché de 6 horas por partido para no agotar el límite de 10 req/min

Requiere: settings.FOOTBALL_DATA_KEY y equipo.api_football_id en ambos equipos.
"""
import requests
from django.conf import settings
from django.utils import timezone

BASE_URL = "https://api.football-data.org/v4"
TTL_SEGUNDOS = 6 * 3600

_last_error = ''


def _api_key():
    return getattr(settings, 'FOOTBALL_DATA_KEY', '') or ''


def _get(endpoint, params=None):
    global _last_error
    key = _api_key()
    if not key:
        _last_error = 'FOOTBALL_DATA_KEY no configurada'
        return None
    try:
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers={"X-Auth-Token": key},
            params=params or {},
            timeout=10,
        )
        r.raise_for_status()
        _last_error = ''
        return r.json()
    except requests.HTTPError as e:
        _last_error = f'HTTP {e.response.status_code}: {e.response.text[:300]}'
        return None
    except Exception as e:
        _last_error = str(e)
        return None


def _wc_matches(season):
    """Devuelve todos los partidos de un Mundial (sin filtro de estado)."""
    resp = _get('competitions/WC/matches', {'season': season})
    return (resp or {}).get('matches', [])


def _finished(m):
    return m.get('status') in ('FINISHED', 'AWARDED')


def get_datos_partido(partido):
    """
    Devuelve dict con forma e H2H, usando caché JSONField.
    Retorna None si la API no está configurada o los equipos no tienen api_football_id.
    """
    if not _api_key():
        return None

    id_local = partido.equipo_local.api_football_id
    id_vis   = partido.equipo_visitante.api_football_id
    if not id_local or not id_vis:
        return None

    # Verificar caché
    if partido.datos_previos and partido.datos_previos_ts:
        age = (timezone.now() - partido.datos_previos_ts).total_seconds()
        if age < TTL_SEGUNDOS:
            return partido.datos_previos

    datos = {}

    # ── WC 2026: forma actual en el torneo ──────────────────────
    wc26 = _wc_matches(2026)
    wc26_fin = [m for m in wc26 if _finished(m)]

    if wc26_fin:
        loc_26 = [m for m in wc26_fin
                  if m['homeTeam']['id'] == id_local or m['awayTeam']['id'] == id_local]
        vis_26 = [m for m in wc26_fin
                  if m['homeTeam']['id'] == id_vis or m['awayTeam']['id'] == id_vis]
        if loc_26:
            datos['forma_local'] = _parse_forma(loc_26[-5:], id_local)
        if vis_26:
            datos['forma_visitante'] = _parse_forma(vis_26[-5:], id_vis)

    # ── H2H: buscar en WC 2026, 2022, 2018 ─────────────────────
    h2h_total = {'victorias_local': 0, 'empates': 0, 'victorias_visitante': 0,
                 'total': 0, 'ultimos': []}

    for season, matches in [(2026, wc26_fin), (2022, None), (2018, None)]:
        if h2h_total['total'] >= 5:
            break
        if matches is None:
            all_m = _wc_matches(season)
            matches = [m for m in all_m if _finished(m)]
        confrontaciones = [
            m for m in matches
            if m['homeTeam']['id'] in (id_local, id_vis)
            and m['awayTeam']['id'] in (id_local, id_vis)
            and m['homeTeam']['id'] != m['awayTeam']['id']
        ]
        if confrontaciones:
            p = _parse_h2h(confrontaciones, id_local, id_vis)
            h2h_total['victorias_local']     += p['victorias_local']
            h2h_total['empates']             += p['empates']
            h2h_total['victorias_visitante'] += p['victorias_visitante']
            h2h_total['total']               += p['total']
            h2h_total['ultimos']             += p['ultimos']

    if h2h_total['total'] > 0:
        h2h_total['ultimos'] = h2h_total['ultimos'][:5]
        datos['h2h'] = h2h_total

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
