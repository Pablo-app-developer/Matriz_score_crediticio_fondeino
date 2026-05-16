"""
Comando: python manage.py cargar_fixture_mundial [--limpiar]

Carga los 48 equipos y la estructura de partidos del Mundial 2026.
NOTA: Los datos de grupos y fechas son provisionales. El admin debe
      verificar y actualizar desde el panel de administración.

El Mundial FIFA 2026 se juega del 11 de junio al 19 de julio de 2026.
Sedes: USA, México y Canadá.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.polla.models import Equipo, Partido


EQUIPOS = [
    # Grupo A
    {'nombre': 'Estados Unidos', 'codigo_fifa': 'USA', 'bandera_emoji': '🇺🇸', 'grupo': 'A'},
    {'nombre': 'Marruecos',      'codigo_fifa': 'MAR', 'bandera_emoji': '🇲🇦', 'grupo': 'A'},
    {'nombre': 'Uzbekistán',     'codigo_fifa': 'UZB', 'bandera_emoji': '🇺🇿', 'grupo': 'A'},
    {'nombre': 'Nueva Zelanda',  'codigo_fifa': 'NZL', 'bandera_emoji': '🇳🇿', 'grupo': 'A'},
    # Grupo B
    {'nombre': 'México',         'codigo_fifa': 'MEX', 'bandera_emoji': '🇲🇽', 'grupo': 'B'},
    {'nombre': 'Alemania',       'codigo_fifa': 'GER', 'bandera_emoji': '🇩🇪', 'grupo': 'B'},
    {'nombre': 'Sudáfrica',      'codigo_fifa': 'RSA', 'bandera_emoji': '🇿🇦', 'grupo': 'B'},
    {'nombre': 'Indonesia',      'codigo_fifa': 'IDN', 'bandera_emoji': '🇮🇩', 'grupo': 'B'},
    # Grupo C
    {'nombre': 'Canadá',         'codigo_fifa': 'CAN', 'bandera_emoji': '🇨🇦', 'grupo': 'C'},
    {'nombre': 'Portugal',       'codigo_fifa': 'POR', 'bandera_emoji': '🇵🇹', 'grupo': 'C'},
    {'nombre': 'Túnez',          'codigo_fifa': 'TUN', 'bandera_emoji': '🇹🇳', 'grupo': 'C'},
    {'nombre': 'Bolivia',        'codigo_fifa': 'BOL', 'bandera_emoji': '🇧🇴', 'grupo': 'C'},
    # Grupo D
    {'nombre': 'Francia',        'codigo_fifa': 'FRA', 'bandera_emoji': '🇫🇷', 'grupo': 'D'},
    {'nombre': 'Japón',          'codigo_fifa': 'JPN', 'bandera_emoji': '🇯🇵', 'grupo': 'D'},
    {'nombre': 'Honduras',       'codigo_fifa': 'HON', 'bandera_emoji': '🇭🇳', 'grupo': 'D'},
    {'nombre': 'Rumanía',        'codigo_fifa': 'ROU', 'bandera_emoji': '🇷🇴', 'grupo': 'D'},
    # Grupo E
    {'nombre': 'España',         'codigo_fifa': 'ESP', 'bandera_emoji': '🇪🇸', 'grupo': 'E'},
    {'nombre': 'Corea del Sur',  'codigo_fifa': 'KOR', 'bandera_emoji': '🇰🇷', 'grupo': 'E'},
    {'nombre': 'DR Congo',       'codigo_fifa': 'COD', 'bandera_emoji': '🇨🇩', 'grupo': 'E'},
    {'nombre': 'Uruguay',        'codigo_fifa': 'URU', 'bandera_emoji': '🇺🇾', 'grupo': 'E'},
    # Grupo F
    {'nombre': 'Inglaterra',     'codigo_fifa': 'ENG', 'bandera_emoji': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'grupo': 'F'},
    {'nombre': 'Irán',           'codigo_fifa': 'IRN', 'bandera_emoji': '🇮🇷', 'grupo': 'F'},
    {'nombre': 'Panamá',         'codigo_fifa': 'PAN', 'bandera_emoji': '🇵🇦', 'grupo': 'F'},
    {'nombre': 'Colombia',       'codigo_fifa': 'COL', 'bandera_emoji': '🇨🇴', 'grupo': 'F'},
    # Grupo G
    {'nombre': 'Brasil',         'codigo_fifa': 'BRA', 'bandera_emoji': '🇧🇷', 'grupo': 'G'},
    {'nombre': 'Suiza',          'codigo_fifa': 'SUI', 'bandera_emoji': '🇨🇭', 'grupo': 'G'},
    {'nombre': 'Nigeria',        'codigo_fifa': 'NGA', 'bandera_emoji': '🇳🇬', 'grupo': 'G'},
    {'nombre': 'Jamaica',        'codigo_fifa': 'JAM', 'bandera_emoji': '🇯🇲', 'grupo': 'G'},
    # Grupo H
    {'nombre': 'Argentina',      'codigo_fifa': 'ARG', 'bandera_emoji': '🇦🇷', 'grupo': 'H'},
    {'nombre': 'Australia',      'codigo_fifa': 'AUS', 'bandera_emoji': '🇦🇺', 'grupo': 'H'},
    {'nombre': 'Camerún',        'codigo_fifa': 'CMR', 'bandera_emoji': '🇨🇲', 'grupo': 'H'},
    {'nombre': 'Eslovaquia',     'codigo_fifa': 'SVK', 'bandera_emoji': '🇸🇰', 'grupo': 'H'},
    # Grupo I
    {'nombre': 'Países Bajos',   'codigo_fifa': 'NED', 'bandera_emoji': '🇳🇱', 'grupo': 'I'},
    {'nombre': 'Arabia Saudita', 'codigo_fifa': 'KSA', 'bandera_emoji': '🇸🇦', 'grupo': 'I'},
    {'nombre': 'Egipto',         'codigo_fifa': 'EGY', 'bandera_emoji': '🇪🇬', 'grupo': 'I'},
    {'nombre': 'Ecuador',        'codigo_fifa': 'ECU', 'bandera_emoji': '🇪🇨', 'grupo': 'I'},
    # Grupo J
    {'nombre': 'Bélgica',        'codigo_fifa': 'BEL', 'bandera_emoji': '🇧🇪', 'grupo': 'J'},
    {'nombre': 'Irak',           'codigo_fifa': 'IRQ', 'bandera_emoji': '🇮🇶', 'grupo': 'J'},
    {'nombre': 'Senegal',        'codigo_fifa': 'SEN', 'bandera_emoji': '🇸🇳', 'grupo': 'J'},
    {'nombre': 'Venezuela',      'codigo_fifa': 'VEN', 'bandera_emoji': '🇻🇪', 'grupo': 'J'},
    # Grupo K
    {'nombre': 'Dinamarca',      'codigo_fifa': 'DEN', 'bandera_emoji': '🇩🇰', 'grupo': 'K'},
    {'nombre': 'Jordania',       'codigo_fifa': 'JOR', 'bandera_emoji': '🇯🇴', 'grupo': 'K'},
    {'nombre': 'Ghana',          'codigo_fifa': 'GHA', 'bandera_emoji': '🇬🇭', 'grupo': 'K'},
    {'nombre': 'Hungría',        'codigo_fifa': 'HUN', 'bandera_emoji': '🇭🇺', 'grupo': 'K'},
    # Grupo L
    {'nombre': 'Austria',        'codigo_fifa': 'AUT', 'bandera_emoji': '🇦🇹', 'grupo': 'L'},
    {'nombre': 'Turquía',        'codigo_fifa': 'TUR', 'bandera_emoji': '🇹🇷', 'grupo': 'L'},
    {'nombre': 'Escocia',        'codigo_fifa': 'SCO', 'bandera_emoji': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'grupo': 'L'},
    {'nombre': 'Costa de Marfil','codigo_fifa': 'CIV', 'bandera_emoji': '🇨🇮', 'grupo': 'L'},
]


def _dt(year, month, day, hour=18):
    """Crea datetime consciente en zona horaria América/Bogotá."""
    naive = datetime.datetime(year, month, day, hour, 0)
    return timezone.make_aware(naive)


class Command(BaseCommand):
    help = 'Carga el fixture del Mundial FIFA 2026 (equipos + partidos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar', action='store_true',
            help='Elimina equipos y partidos existentes antes de cargar'
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            Partido.objects.all().delete()
            Equipo.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos anteriores eliminados.'))

        # ── Equipos ──
        equipos_creados = 0
        equipos_map = {}
        for data in EQUIPOS:
            equipo, created = Equipo.objects.update_or_create(
                codigo_fifa=data['codigo_fifa'],
                defaults={
                    'nombre': data['nombre'],
                    'bandera_emoji': data['bandera_emoji'],
                    'grupo': data['grupo'],
                }
            )
            equipos_map[data['codigo_fifa']] = equipo
            if created:
                equipos_creados += 1

        self.stdout.write(self.style.SUCCESS(f'OK Equipos: {len(EQUIPOS)} procesados, {equipos_creados} nuevos.'))

        # ── Partidos de fase de grupos ──
        # Cada grupo tiene 4 equipos -> 6 partidos (round-robin)
        # Orden de enfrentamientos: 1v2, 3v4, 1v3, 2v4, 4v1, 2v3
        grupos = {}
        for data in EQUIPOS:
            grupos.setdefault(data['grupo'], []).append(data['codigo_fifa'])

        partidos_creados = 0
        num = 1

        # Fechas de grupos: Jun 11-28, 2026 (3 jornadas)
        # Jornada 1: Jun 11-17  Jornada 2: Jun 18-23  Jornada 3: Jun 24-28
        jornadas_offset = {1: 0, 2: 7, 3: 14}
        grupo_letras = list('ABCDEFGHIJKL')
        base_fecha = datetime.date(2026, 6, 11)

        for g_idx, letra in enumerate(grupo_letras):
            codigos = grupos.get(letra, [])
            if len(codigos) < 4:
                continue
            t1, t2, t3, t4 = codigos
            enfrentamientos = [
                (1, t1, t2), (1, t3, t4),
                (2, t1, t3), (2, t2, t4),
                (3, t1, t4), (3, t2, t3),
            ]
            hora_ciclo = [14, 17, 20]
            for jornada, cod_local, cod_vis in enfrentamientos:
                dias_extra = jornadas_offset[jornada] + (g_idx % 4)
                hora = hora_ciclo[(g_idx + jornada) % 3]
                fecha = base_fecha + datetime.timedelta(days=dias_extra)
                fecha_hora = _dt(fecha.year, fecha.month, fecha.day, hora)

                _, created = Partido.objects.get_or_create(
                    numero=num,
                    defaults={
                        'fase': 'GRUPOS',
                        'jornada': jornada,
                        'equipo_local': equipos_map[cod_local],
                        'equipo_visitante': equipos_map[cod_vis],
                        'fecha_hora': fecha_hora,
                        'estadio': '(Por confirmar)',
                        'ciudad': '(Por confirmar)',
                    }
                )
                if created:
                    partidos_creados += 1
                num += 1

        self.stdout.write(self.style.SUCCESS(f'OK Partidos de grupos: {num - 1} partidos procesados.'))

        # ── Ronda de 32 (16 partidos) ──
        placeholder = equipos_map.get('USA')  # placeholder hasta conocer clasificados
        for i in range(1, 17):
            _, created = Partido.objects.get_or_create(
                numero=num,
                defaults={
                    'fase': 'TREINTA_DOS',
                    'equipo_local': placeholder,
                    'equipo_visitante': placeholder,
                    'fecha_hora': _dt(2026, 7, 1 + (i % 4), 18),
                    'estadio': '(Por confirmar)',
                    'ciudad': '(Por confirmar)',
                }
            )
            if created:
                partidos_creados += 1
            num += 1

        # ── Octavos de final (8 partidos) ──
        for i in range(1, 9):
            _, created = Partido.objects.get_or_create(
                numero=num,
                defaults={
                    'fase': 'OCTAVOS',
                    'equipo_local': placeholder,
                    'equipo_visitante': placeholder,
                    'fecha_hora': _dt(2026, 7, 5 + (i % 4), 18),
                    'estadio': '(Por confirmar)',
                    'ciudad': '(Por confirmar)',
                }
            )
            if created:
                partidos_creados += 1
            num += 1

        # ── Cuartos (4 partidos) ──
        for i in range(1, 5):
            _, created = Partido.objects.get_or_create(
                numero=num,
                defaults={
                    'fase': 'CUARTOS',
                    'equipo_local': placeholder,
                    'equipo_visitante': placeholder,
                    'fecha_hora': _dt(2026, 7, 9 + (i % 2), 18),
                    'estadio': '(Por confirmar)',
                    'ciudad': '(Por confirmar)',
                }
            )
            if created:
                partidos_creados += 1
            num += 1

        # ── Semifinales (2 partidos) ──
        for i, dia in enumerate([14, 15]):
            _, created = Partido.objects.get_or_create(
                numero=num,
                defaults={
                    'fase': 'SEMIS',
                    'equipo_local': placeholder,
                    'equipo_visitante': placeholder,
                    'fecha_hora': _dt(2026, 7, dia, 19),
                    'estadio': '(Por confirmar)',
                    'ciudad': '(Por confirmar)',
                }
            )
            if created:
                partidos_creados += 1
            num += 1

        # ── Tercer puesto ──
        _, created = Partido.objects.get_or_create(
            numero=num,
            defaults={
                'fase': 'TERCERO',
                'equipo_local': placeholder,
                'equipo_visitante': placeholder,
                'fecha_hora': _dt(2026, 7, 18, 15),
                'estadio': '(Por confirmar)',
                'ciudad': '(Por confirmar)',
            }
        )
        if created:
            partidos_creados += 1
        num += 1

        # ── Final ──
        _, created = Partido.objects.get_or_create(
            numero=num,
            defaults={
                'fase': 'FINAL',
                'equipo_local': placeholder,
                'equipo_visitante': placeholder,
                'fecha_hora': _dt(2026, 7, 19, 17),
                'estadio': 'MetLife Stadium',
                'ciudad': 'Nueva Jersey / Nueva York',
            }
        )
        if created:
            partidos_creados += 1

        total_partidos = Partido.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'OK Total partidos en BD: {total_partidos} ({partidos_creados} nuevos).'
        ))
        self.stdout.write(self.style.WARNING(
            'IMPORTANTE: Los grupos y fechas son provisionales. '
            'Actualiza el fixture desde el panel de administracion con los datos oficiales de FIFA.'
        ))
