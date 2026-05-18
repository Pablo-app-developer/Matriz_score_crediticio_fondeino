"""
Comando: python manage.py actualizar_fixture_oficial

Migra el fixture a los datos OFICIALES del sorteo FIFA World Cup 2026
(realizado el 5 de diciembre de 2024 en Miami).

QUÉ HACE:
  1. Actualiza/crea los 48 equipos con grupos y nombres correctos.
  2. Elimina los pronósticos existentes de la fase de grupos (partidos 1-72).
  3. Elimina y recrea los 72 partidos de grupos con equipos, fechas y estadios
     correctos (horas en COT = UTC-5, hora Colombia).
  4. Los partidos eliminatorios (73+) NO se modifican.

ADVERTENCIA: Los pronósticos de la fase de grupos se pierden. Esto es
intencional porque el fixture anterior era provisional (incorrecto).
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.polla.models import Equipo, Partido, Pronostico


# ── 48 equipos oficiales ──────────────────────────────────────────────────────
EQUIPOS_OFICIAL = [
    # Grupo A
    {'nombre': 'México',               'codigo_fifa': 'MEX', 'bandera_emoji': '🇲🇽', 'grupo': 'A'},
    {'nombre': 'Corea del Sur',        'codigo_fifa': 'KOR', 'bandera_emoji': '🇰🇷', 'grupo': 'A'},
    {'nombre': 'Sudáfrica',            'codigo_fifa': 'RSA', 'bandera_emoji': '🇿🇦', 'grupo': 'A'},
    {'nombre': 'República Checa',      'codigo_fifa': 'CZE', 'bandera_emoji': '🇨🇿', 'grupo': 'A'},
    # Grupo B
    {'nombre': 'Canadá',               'codigo_fifa': 'CAN', 'bandera_emoji': '🇨🇦', 'grupo': 'B'},
    {'nombre': 'Suiza',                'codigo_fifa': 'SUI', 'bandera_emoji': '🇨🇭', 'grupo': 'B'},
    {'nombre': 'Catar',                'codigo_fifa': 'QAT', 'bandera_emoji': '🇶🇦', 'grupo': 'B'},
    {'nombre': 'Bosnia y Herzegovina', 'codigo_fifa': 'BIH', 'bandera_emoji': '🇧🇦', 'grupo': 'B'},
    # Grupo C
    {'nombre': 'Brasil',               'codigo_fifa': 'BRA', 'bandera_emoji': '🇧🇷', 'grupo': 'C'},
    {'nombre': 'Marruecos',            'codigo_fifa': 'MAR', 'bandera_emoji': '🇲🇦', 'grupo': 'C'},
    {'nombre': 'Haití',                'codigo_fifa': 'HAI', 'bandera_emoji': '🇭🇹', 'grupo': 'C'},
    {'nombre': 'Escocia',              'codigo_fifa': 'SCO', 'bandera_emoji': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'grupo': 'C'},
    # Grupo D
    {'nombre': 'Estados Unidos',       'codigo_fifa': 'USA', 'bandera_emoji': '🇺🇸', 'grupo': 'D'},
    {'nombre': 'Paraguay',             'codigo_fifa': 'PAR', 'bandera_emoji': '🇵🇾', 'grupo': 'D'},
    {'nombre': 'Australia',            'codigo_fifa': 'AUS', 'bandera_emoji': '🇦🇺', 'grupo': 'D'},
    {'nombre': 'Turquía',              'codigo_fifa': 'TUR', 'bandera_emoji': '🇹🇷', 'grupo': 'D'},
    # Grupo E
    {'nombre': 'Alemania',             'codigo_fifa': 'GER', 'bandera_emoji': '🇩🇪', 'grupo': 'E'},
    {'nombre': 'Costa de Marfil',      'codigo_fifa': 'CIV', 'bandera_emoji': '🇨🇮', 'grupo': 'E'},
    {'nombre': 'Ecuador',              'codigo_fifa': 'ECU', 'bandera_emoji': '🇪🇨', 'grupo': 'E'},
    {'nombre': 'Curazao',              'codigo_fifa': 'CUW', 'bandera_emoji': '🇨🇼', 'grupo': 'E'},
    # Grupo F
    {'nombre': 'Países Bajos',         'codigo_fifa': 'NED', 'bandera_emoji': '🇳🇱', 'grupo': 'F'},
    {'nombre': 'Japón',                'codigo_fifa': 'JPN', 'bandera_emoji': '🇯🇵', 'grupo': 'F'},
    {'nombre': 'Suecia',               'codigo_fifa': 'SWE', 'bandera_emoji': '🇸🇪', 'grupo': 'F'},
    {'nombre': 'Túnez',                'codigo_fifa': 'TUN', 'bandera_emoji': '🇹🇳', 'grupo': 'F'},
    # Grupo G
    {'nombre': 'Bélgica',              'codigo_fifa': 'BEL', 'bandera_emoji': '🇧🇪', 'grupo': 'G'},
    {'nombre': 'Egipto',               'codigo_fifa': 'EGY', 'bandera_emoji': '🇪🇬', 'grupo': 'G'},
    {'nombre': 'Irán',                 'codigo_fifa': 'IRN', 'bandera_emoji': '🇮🇷', 'grupo': 'G'},
    {'nombre': 'Nueva Zelanda',        'codigo_fifa': 'NZL', 'bandera_emoji': '🇳🇿', 'grupo': 'G'},
    # Grupo H
    {'nombre': 'España',               'codigo_fifa': 'ESP', 'bandera_emoji': '🇪🇸', 'grupo': 'H'},
    {'nombre': 'Uruguay',              'codigo_fifa': 'URU', 'bandera_emoji': '🇺🇾', 'grupo': 'H'},
    {'nombre': 'Arabia Saudita',       'codigo_fifa': 'KSA', 'bandera_emoji': '🇸🇦', 'grupo': 'H'},
    {'nombre': 'Cabo Verde',           'codigo_fifa': 'CPV', 'bandera_emoji': '🇨🇻', 'grupo': 'H'},
    # Grupo I
    {'nombre': 'Francia',              'codigo_fifa': 'FRA', 'bandera_emoji': '🇫🇷', 'grupo': 'I'},
    {'nombre': 'Senegal',              'codigo_fifa': 'SEN', 'bandera_emoji': '🇸🇳', 'grupo': 'I'},
    {'nombre': 'Noruega',              'codigo_fifa': 'NOR', 'bandera_emoji': '🇳🇴', 'grupo': 'I'},
    {'nombre': 'Irak',                 'codigo_fifa': 'IRQ', 'bandera_emoji': '🇮🇶', 'grupo': 'I'},
    # Grupo J
    {'nombre': 'Argentina',            'codigo_fifa': 'ARG', 'bandera_emoji': '🇦🇷', 'grupo': 'J'},
    {'nombre': 'Austria',              'codigo_fifa': 'AUT', 'bandera_emoji': '🇦🇹', 'grupo': 'J'},
    {'nombre': 'Argelia',              'codigo_fifa': 'ALG', 'bandera_emoji': '🇩🇿', 'grupo': 'J'},
    {'nombre': 'Jordania',             'codigo_fifa': 'JOR', 'bandera_emoji': '🇯🇴', 'grupo': 'J'},
    # Grupo K
    {'nombre': 'Portugal',             'codigo_fifa': 'POR', 'bandera_emoji': '🇵🇹', 'grupo': 'K'},
    {'nombre': 'Colombia',             'codigo_fifa': 'COL', 'bandera_emoji': '🇨🇴', 'grupo': 'K'},
    {'nombre': 'Uzbekistán',           'codigo_fifa': 'UZB', 'bandera_emoji': '🇺🇿', 'grupo': 'K'},
    {'nombre': 'Rep. Dem. Congo',      'codigo_fifa': 'COD', 'bandera_emoji': '🇨🇩', 'grupo': 'K'},
    # Grupo L
    {'nombre': 'Inglaterra',           'codigo_fifa': 'ENG', 'bandera_emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'grupo': 'L'},
    {'nombre': 'Croacia',              'codigo_fifa': 'CRO', 'bandera_emoji': '🇭🇷', 'grupo': 'L'},
    {'nombre': 'Ghana',                'codigo_fifa': 'GHA', 'bandera_emoji': '🇬🇭', 'grupo': 'L'},
    {'nombre': 'Panamá',               'codigo_fifa': 'PAN', 'bandera_emoji': '🇵🇦', 'grupo': 'L'},
]

# ── 72 partidos de grupo ──────────────────────────────────────────────────────
# Campos: (numero, cod_local, cod_vis, año, mes, día, hora, min, estadio, ciudad, grupo, jornada)
# Horas en COT (UTC-5 = hora Colombia, sin cambio de horario de verano).
FIXTURE_GRUPOS = [
    # ── JORNADA 1 ─────────────────────────────────────────────────────────────
    ( 1, 'MEX', 'RSA', 2026, 6, 11, 14,  0, 'Estadio Azteca',          'Ciudad de México', 'A', 1),
    ( 2, 'KOR', 'CZE', 2026, 6, 11, 21,  0, 'Estadio Akron',           'Guadalajara',      'A', 1),
    ( 3, 'CAN', 'BIH', 2026, 6, 12, 14,  0, 'BMO Field',               'Toronto',          'B', 1),
    ( 4, 'USA', 'PAR', 2026, 6, 12, 20,  0, 'SoFi Stadium',            'Los Ángeles',      'D', 1),
    ( 5, 'AUS', 'TUR', 2026, 6, 13,  2,  0, 'BC Place',                'Vancouver',        'D', 1),
    ( 6, 'QAT', 'SUI', 2026, 6, 13, 14,  0, "Levi's Stadium",          'San Francisco',    'B', 1),
    ( 7, 'BRA', 'MAR', 2026, 6, 13, 17,  0, 'MetLife Stadium',         'Nueva York',       'C', 1),
    ( 8, 'HAI', 'SCO', 2026, 6, 13, 20,  0, 'Gillette Stadium',        'Boston',           'C', 1),
    ( 9, 'GER', 'CUW', 2026, 6, 14, 12,  0, 'NRG Stadium',             'Houston',          'E', 1),
    (10, 'NED', 'JPN', 2026, 6, 14, 15,  0, 'AT&T Stadium',            'Dallas',           'F', 1),
    (11, 'CIV', 'ECU', 2026, 6, 14, 18,  0, 'Lincoln Financial Field', 'Filadelfia',       'E', 1),
    (12, 'SWE', 'TUN', 2026, 6, 14, 21,  0, 'Estadio BBVA',            'Monterrey',        'F', 1),
    (13, 'ESP', 'CPV', 2026, 6, 15, 11,  0, 'Mercedes-Benz Stadium',   'Atlanta',          'H', 1),
    (14, 'BEL', 'EGY', 2026, 6, 15, 14,  0, 'Lumen Field',             'Seattle',          'G', 1),
    (15, 'KSA', 'URU', 2026, 6, 15, 17,  0, 'Hard Rock Stadium',       'Miami',            'H', 1),
    (16, 'IRN', 'NZL', 2026, 6, 15, 20,  0, 'SoFi Stadium',            'Los Ángeles',      'G', 1),
    (17, 'FRA', 'SEN', 2026, 6, 16, 14,  0, 'MetLife Stadium',         'Nueva York',       'I', 1),
    (18, 'IRQ', 'NOR', 2026, 6, 16, 17,  0, 'Gillette Stadium',        'Boston',           'I', 1),
    (19, 'ARG', 'ALG', 2026, 6, 16, 20,  0, 'Arrowhead Stadium',       'Kansas City',      'J', 1),
    (20, 'AUT', 'JOR', 2026, 6, 16, 23,  0, "Levi's Stadium",          'San Francisco',    'J', 1),
    (21, 'POR', 'COD', 2026, 6, 17, 12,  0, 'NRG Stadium',             'Houston',          'K', 1),
    (22, 'ENG', 'CRO', 2026, 6, 17, 15,  0, 'AT&T Stadium',            'Dallas',           'L', 1),
    (23, 'GHA', 'PAN', 2026, 6, 17, 18,  0, 'BMO Field',               'Toronto',          'L', 1),
    (24, 'UZB', 'COL', 2026, 6, 17, 21,  0, 'Estadio Azteca',          'Ciudad de México', 'K', 1),
    # ── JORNADA 2 ─────────────────────────────────────────────────────────────
    (25, 'CZE', 'RSA', 2026, 6, 18, 11,  0, 'Mercedes-Benz Stadium',   'Atlanta',          'A', 2),
    (26, 'SUI', 'BIH', 2026, 6, 18, 14,  0, 'SoFi Stadium',            'Los Ángeles',      'B', 2),
    (27, 'CAN', 'QAT', 2026, 6, 18, 17,  0, 'BC Place',                'Vancouver',        'B', 2),
    (28, 'MEX', 'KOR', 2026, 6, 18, 20,  0, 'Estadio Akron',           'Guadalajara',      'A', 2),
    (29, 'USA', 'AUS', 2026, 6, 19, 14,  0, 'Lumen Field',             'Seattle',          'D', 2),
    (30, 'SCO', 'MAR', 2026, 6, 19, 17,  0, 'Gillette Stadium',        'Boston',           'C', 2),
    (31, 'BRA', 'HAI', 2026, 6, 19, 20,  0, 'Lincoln Financial Field', 'Filadelfia',       'C', 2),
    (32, 'TUR', 'PAR', 2026, 6, 19, 23,  0, "Levi's Stadium",          'San Francisco',    'D', 2),
    (33, 'NED', 'SWE', 2026, 6, 20, 12,  0, 'NRG Stadium',             'Houston',          'F', 2),
    (34, 'GER', 'CIV', 2026, 6, 20, 15,  0, 'BMO Field',               'Toronto',          'E', 2),
    (35, 'ECU', 'CUW', 2026, 6, 20, 19,  0, 'Arrowhead Stadium',       'Kansas City',      'E', 2),
    (36, 'TUN', 'JPN', 2026, 6, 20, 23,  0, 'Estadio BBVA',            'Monterrey',        'F', 2),
    (37, 'ESP', 'KSA', 2026, 6, 21, 11,  0, 'Mercedes-Benz Stadium',   'Atlanta',          'H', 2),
    (38, 'BEL', 'IRN', 2026, 6, 21, 14,  0, 'SoFi Stadium',            'Los Ángeles',      'G', 2),
    (39, 'URU', 'CPV', 2026, 6, 21, 17,  0, 'Hard Rock Stadium',       'Miami',            'H', 2),
    (40, 'NZL', 'EGY', 2026, 6, 21, 20,  0, 'BC Place',                'Vancouver',        'G', 2),
    (41, 'ARG', 'AUT', 2026, 6, 22, 12,  0, 'AT&T Stadium',            'Dallas',           'J', 2),
    (42, 'FRA', 'IRQ', 2026, 6, 22, 16,  0, 'Lincoln Financial Field', 'Filadelfia',       'I', 2),
    (43, 'NOR', 'SEN', 2026, 6, 22, 19,  0, 'MetLife Stadium',         'Nueva York',       'I', 2),
    (44, 'JOR', 'ALG', 2026, 6, 22, 22,  0, "Levi's Stadium",          'San Francisco',    'J', 2),
    (45, 'POR', 'UZB', 2026, 6, 23, 12,  0, 'NRG Stadium',             'Houston',          'K', 2),
    (46, 'ENG', 'GHA', 2026, 6, 23, 15,  0, 'Gillette Stadium',        'Boston',           'L', 2),
    (47, 'PAN', 'CRO', 2026, 6, 23, 18,  0, 'BMO Field',               'Toronto',          'L', 2),
    (48, 'COL', 'COD', 2026, 6, 23, 21,  0, 'Estadio Akron',           'Guadalajara',      'K', 2),
    # ── JORNADA 3 (partidos simultáneos por grupo) ────────────────────────────
    (49, 'SUI', 'CAN', 2026, 6, 24, 15,  0, 'BC Place',                'Vancouver',        'B', 3),
    (50, 'BIH', 'QAT', 2026, 6, 24, 15,  0, 'Lumen Field',             'Seattle',          'B', 3),
    (51, 'MAR', 'HAI', 2026, 6, 24, 17,  0, 'Mercedes-Benz Stadium',   'Atlanta',          'C', 3),
    (52, 'SCO', 'BRA', 2026, 6, 24, 17,  0, 'Hard Rock Stadium',       'Miami',            'C', 3),
    (53, 'CZE', 'MEX', 2026, 6, 24, 20,  0, 'Estadio Azteca',          'Ciudad de México', 'A', 3),
    (54, 'RSA', 'KOR', 2026, 6, 24, 20,  0, 'Estadio BBVA',            'Monterrey',        'A', 3),
    (55, 'CUW', 'CIV', 2026, 6, 25, 15,  0, 'Lincoln Financial Field', 'Filadelfia',       'E', 3),
    (56, 'ECU', 'GER', 2026, 6, 25, 15,  0, 'MetLife Stadium',         'Nueva York',       'E', 3),
    (57, 'JPN', 'SWE', 2026, 6, 25, 18,  0, 'AT&T Stadium',            'Dallas',           'F', 3),
    (58, 'TUN', 'NED', 2026, 6, 25, 18,  0, 'Arrowhead Stadium',       'Kansas City',      'F', 3),
    (59, 'TUR', 'USA', 2026, 6, 25, 21,  0, 'SoFi Stadium',            'Los Ángeles',      'D', 3),
    (60, 'PAR', 'AUS', 2026, 6, 25, 21,  0, "Levi's Stadium",          'San Francisco',    'D', 3),
    (61, 'NOR', 'FRA', 2026, 6, 26, 14,  0, 'Gillette Stadium',        'Boston',           'I', 3),
    (62, 'SEN', 'IRQ', 2026, 6, 26, 14,  0, 'BMO Field',               'Toronto',          'I', 3),
    (63, 'CPV', 'KSA', 2026, 6, 26, 19,  0, 'NRG Stadium',             'Houston',          'H', 3),
    (64, 'URU', 'ESP', 2026, 6, 26, 19,  0, 'Estadio Akron',           'Guadalajara',      'H', 3),
    (65, 'NZL', 'BEL', 2026, 6, 26, 22,  0, 'BC Place',                'Vancouver',        'G', 3),
    (66, 'EGY', 'IRN', 2026, 6, 26, 22,  0, 'Lumen Field',             'Seattle',          'G', 3),
    (67, 'PAN', 'ENG', 2026, 6, 27, 16,  0, 'MetLife Stadium',         'Nueva York',       'L', 3),
    (68, 'CRO', 'GHA', 2026, 6, 27, 16,  0, 'Lincoln Financial Field', 'Filadelfia',       'L', 3),
    (69, 'COL', 'POR', 2026, 6, 27, 18, 30, 'Hard Rock Stadium',       'Miami',            'K', 3),
    (70, 'COD', 'UZB', 2026, 6, 27, 18, 30, 'Mercedes-Benz Stadium',   'Atlanta',          'K', 3),
    (71, 'ALG', 'AUT', 2026, 6, 27, 21,  0, 'Arrowhead Stadium',       'Kansas City',      'J', 3),
    (72, 'JOR', 'ARG', 2026, 6, 27, 21,  0, 'AT&T Stadium',            'Dallas',           'J', 3),
]


class Command(BaseCommand):
    help = 'Migra el fixture a los datos oficiales del sorteo FIFA World Cup 2026'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '══ ACTUALIZAR FIXTURE OFICIAL FIFA 2026 ══'
        ))

        # ── 1. Actualizar/crear los 48 equipos ───────────────────────────────
        equipos_map = {}
        actualizados = 0
        creados_eq = 0
        for data in EQUIPOS_OFICIAL:
            equipo, created = Equipo.objects.update_or_create(
                codigo_fifa=data['codigo_fifa'],
                defaults={
                    'nombre':        data['nombre'],
                    'bandera_emoji': data['bandera_emoji'],
                    'grupo':         data['grupo'],
                }
            )
            equipos_map[data['codigo_fifa']] = equipo
            if created:
                creados_eq += 1
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'[1/4] Equipos: {actualizados} actualizados, {creados_eq} creados.'
        ))

        # ── 2. Eliminar pronósticos de la fase de grupos ─────────────────────
        prons = Pronostico.objects.filter(partido__numero__lte=72)
        total_prons = prons.count()
        prons.delete()
        self.stdout.write(self.style.WARNING(
            f'[2/4] Eliminados {total_prons} pronósticos de fase de grupos.'
        ))

        # ── 3. Eliminar partidos de grupos y recrearlos ───────────────────────
        eliminados = Partido.objects.filter(numero__lte=72).count()
        Partido.objects.filter(numero__lte=72).delete()

        creados_p = 0
        errores = []
        for row in FIXTURE_GRUPOS:
            num, cod_l, cod_v, y, mo, d, h, mi, estadio, ciudad, _grupo, jornada = row
            eq_local = equipos_map.get(cod_l)
            eq_vis   = equipos_map.get(cod_v)
            if not eq_local:
                errores.append(f'Partido {num}: equipo local "{cod_l}" no encontrado.')
                continue
            if not eq_vis:
                errores.append(f'Partido {num}: equipo visitante "{cod_v}" no encontrado.')
                continue

            naive     = datetime.datetime(y, mo, d, h, mi)
            fecha_hora = timezone.make_aware(naive)

            Partido.objects.create(
                numero=num,
                fase='GRUPOS',
                jornada=jornada,
                equipo_local=eq_local,
                equipo_visitante=eq_vis,
                fecha_hora=fecha_hora,
                estadio=estadio,
                ciudad=ciudad,
            )
            creados_p += 1

        self.stdout.write(self.style.SUCCESS(
            f'[3/4] Partidos: {eliminados} eliminados, {creados_p} recreados.'
        ))
        for err in errores:
            self.stdout.write(self.style.ERROR(f'  ERROR: {err}'))

        # ── 4. Resumen ────────────────────────────────────────────────────────
        total = Partido.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'[4/4] Total partidos en BD: {total} '
            f'(72 grupos + {total - 72} eliminatorios).'
        ))
        self.stdout.write(self.style.WARNING(
            'NOTA: Las horas están en COT (UTC-5, hora Colombia). '
            'Verifica y ajusta en el admin si alguna hora no cuadra. '
            'Los partidos eliminatorios (73+) no fueron modificados.'
        ))
