"""
Servicio de estadísticas previas al partido — TheSportsDB (plan gratuito, sin key).

- Forma: últimos 5 partidos de cada selección (cualquier competición)
- H2H: historial entre los dos equipos

Caché de 6 horas en partido.datos_previos para respetar el rate limit.
"""
import requests
from django.utils import timezone

SDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
TTL_SEGUNDOS = 6 * 3600

_last_error = ''

# Nombres en español → inglés para buscar en TheSportsDB
_ES_EN = {
    'Alemania': 'Germany', 'Arabia Saudita': 'Saudi Arabia', 'Argelia': 'Algeria',
    'Australia': 'Australia', 'Austria': 'Austria', 'Bélgica': 'Belgium',
    'Bosnia y Herzegovina': 'Bosnia and Herzegovina', 'Brasil': 'Brazil',
    'Cabo Verde': 'Cape Verde', 'Catar': 'Qatar', 'Colombia': 'Colombia',
    'Corea del Sur': 'South Korea', 'Costa de Marfil': 'Ivory Coast',
    'Croacia': 'Croatia', 'Curazao': 'Curacao', 'Ecuador': 'Ecuador',
    'Egipto': 'Egypt', 'Escocia': 'Scotland', 'España': 'Spain',
    'Estados Unidos': 'United States', 'Francia': 'France', 'Ghana': 'Ghana',
    'Haití': 'Haiti', 'Inglaterra': 'England', 'Irak': 'Iraq', 'Irán': 'Iran',
    'Japón': 'Japan', 'Jordania': 'Jordan', 'Marruecos': 'Morocco',
    'México': 'Mexico', 'Nigeria': 'Nigeria', 'Noruega': 'Norway',
    'Nueva Zelanda': 'New Zealand', 'Países Bajos': 'Netherlands',
    'Panamá': 'Panama', 'Paraguay': 'Paraguay', 'Portugal': 'Portugal',
    'Rep. Checa': 'Czech Republic', 'República Checa': 'Czech Republic',
    'Rep. Dem. Congo': 'DR Congo', 'Rumanía': 'Romania', 'Senegal': 'Senegal',
    'Sudáfrica': 'South Africa', 'Suecia': 'Sweden', 'Suiza': 'Switzerland',
    'Turquía': 'Turkey', 'Túnez': 'Tunisia', 'Uruguay': 'Uruguay',
    'Uzbekistán': 'Uzbekistan',
}


def _get(endpoint, params=None):
    global _last_error
    try:
        r = requests.get(f"{SDB_BASE}/{endpoint}", params=params or {}, timeout=10)
        r.raise_for_status()
        _last_error = ''
        return r.json()
    except Exception as e:
        _last_error = str(e)
        return None


def _nombre_en(nombre_es):
    return _ES_EN.get(nombre_es, nombre_es)


def _team_id(nombre_es):
    """Busca el idTeam y nombre canónico en TheSportsDB."""
    nombre = _nombre_en(nombre_es)
    data = _get('searchteams.php', {'t': nombre})
    teams = (data or {}).get('teams') or []
    # Preferir coincidencia exacta Soccer
    for t in teams:
        if t.get('strSport') == 'Soccer' and t.get('strTeam', '').lower() == nombre.lower():
            return t['idTeam'], t['strTeam']
    # Primer resultado Soccer
    for t in teams:
        if t.get('strSport') == 'Soccer':
            return t['idTeam'], t['strTeam']
    return None, None


def _forma(team_id, nombre_canonico):
    """Últimos 5 resultados de la selección → ['W','D','L',...]."""
    data = _get('eventslast.php', {'id': team_id})
    events = (data or {}).get('results') or []
    canon = nombre_canonico.lower()
    forma = []
    for e in events:
        home = (e.get('strHomeTeam') or '').strip().lower()
        away = (e.get('strAwayTeam') or '').strip().lower()
        # Identificar si el equipo es local o visitante
        if home == canon:
            es_local = True
        elif away == canon:
            es_local = False
        else:
            continue  # el equipo no aparece en este evento
        hs = e.get('intHomeScore')
        as_ = e.get('intAwayScore')
        if hs is None or as_ is None or hs == '' or as_ == '':
            continue
        try:
            hg, ag = int(hs), int(as_)
        except (ValueError, TypeError):
            continue
        gl = hg if es_local else ag
        gv = ag if es_local else hg
        if gl > gv:
            forma.append('W')
        elif gl < gv:
            forma.append('L')
        else:
            forma.append('D')
    return forma[-5:] if forma else None


def _h2h(id_local, id_vis, canon_local, canon_vis):
    """Historial entre dos selecciones vía TheSportsDB."""
    data = _get('eventsh2h.php', {'idTeam1': id_local, 'idTeam2': id_vis})
    events = (data or {}).get('results') or []
    cl = canon_local.lower()

    victorias_local = empates = victorias_vis = 0
    ultimos = []
    for e in events:
        home = (e.get('strHomeTeam') or '').strip().lower()
        hs = e.get('intHomeScore')
        as_ = e.get('intAwayScore')
        if hs is None or as_ is None or hs == '' or as_ == '':
            continue
        try:
            hg, ag = int(hs), int(as_)
        except (ValueError, TypeError):
            continue
        es_local = home == cl
        gl = hg if es_local else ag
        gv = ag if es_local else hg
        nl = canon_local if es_local else canon_vis
        nv = canon_vis  if es_local else canon_local
        if gl > gv:
            victorias_local += 1
        elif gl < gv:
            victorias_vis += 1
        else:
            empates += 1
        ultimos.append({
            'fecha': (e.get('dateEvent') or '')[:10],
            'local': nl, 'visitante': nv,
            'marcador': f'{hg}-{ag}',
        })
    total = victorias_local + empates + victorias_vis
    if total == 0:
        return None
    return {
        'victorias_local': victorias_local,
        'empates': empates,
        'victorias_visitante': victorias_vis,
        'total': total,
        'ultimos': ultimos[:5],
    }


def get_datos_partido(partido):
    """
    Devuelve dict con forma e H2H desde TheSportsDB.
    Usa caché JSONField (TTL 6h) para minimizar llamadas a la API.
    """
    # Verificar caché
    if partido.datos_previos and partido.datos_previos_ts:
        age = (timezone.now() - partido.datos_previos_ts).total_seconds()
        if age < TTL_SEGUNDOS:
            return partido.datos_previos

    nombre_local = partido.equipo_local.nombre
    nombre_vis   = partido.equipo_visitante.nombre

    # Buscar IDs y nombres canónicos en TheSportsDB
    id_local, canon_local = _team_id(nombre_local)
    id_vis,   canon_vis   = _team_id(nombre_vis)

    datos = {}

    if id_local and canon_local:
        f = _forma(id_local, canon_local)
        if f:
            datos['forma_local'] = f

    if id_vis and canon_vis:
        f = _forma(id_vis, canon_vis)
        if f:
            datos['forma_visitante'] = f

    if id_local and id_vis and canon_local and canon_vis:
        h = _h2h(id_local, id_vis, canon_local, canon_vis)
        if h:
            datos['h2h'] = h

    if datos:
        partido.datos_previos = datos
        partido.datos_previos_ts = timezone.now()
        partido.save(update_fields=['datos_previos', 'datos_previos_ts'])

    return datos or None
