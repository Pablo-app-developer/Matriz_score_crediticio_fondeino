"""
Comando: python manage.py seed_polla

Crea o actualiza la ConfiguracionPolla con los valores del Mundial 2026.
Es idempotente: se puede correr varias veces sin problema.
"""

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.polla.models import ConfiguracionPolla


def _dt(year, month, day, hour=0, minute=0):
    naive = datetime.datetime(year, month, day, hour, minute)
    return timezone.make_aware(naive)


class Command(BaseCommand):
    help = 'Crea o actualiza la configuración inicial de la Polla Mundialista 2026'

    def handle(self, *args, **options):
        config, created = ConfiguracionPolla.objects.get_or_create(pk=1)

        config.nombre_torneo = 'Polla Mundialista FONDEINO - Copa Mundial FIFA 2026'

        # Puntuación
        config.pts_resultado_grupos = 1
        config.pts_marcador_grupos = 2
        config.pts_resultado_eliminatoria = 2
        config.pts_marcador_eliminatoria = 4

        # Premios
        config.premio_campeon_sorteo = 'Camiseta original de la Selección Colombia'
        config.premios_top5_grupos = (
            'Top 5 de la fase de grupos: premios especiales para los 5 mejores '
            '(por definir por la Junta Directiva de FONDEINO)'
        )
        config.premios_top5_general = (
            'Top 5 general (todas las fases): premios mejorados para los 5 mejores '
            'al finalizar el Mundial (por definir por la Junta Directiva de FONDEINO)'
        )

        # Fechas del Mundial 2026
        # Inscripciones: abiertas ya, cierran el día antes del primer partido
        config.fecha_inicio_inscripciones = _dt(2026, 5, 15, 8, 0)   # Hoy
        config.fecha_cierre_inscripciones = _dt(2026, 6, 10, 23, 59)  # Noche antes del primer partido
        config.fecha_cierre_pronostico_campeon = _dt(2026, 6, 11, 17, 0)  # Antes del primer partido (18h)

        # Captación
        config.mensaje_no_afiliado = (
            '¡Afíliate a FONDEINO y participa en la Polla Mundialista 2026! '
            'La participación tiene un valor de $5.000 por asociado.'
            'Los nuevos asociados y quienes aumenten sus aportes durante la campaña '
            'reciben DOBLE POLLA como beneficio promocional. '
            '¡Dos oportunidades de ganar los premios!'
        )
        config.enlace_afiliacion = 'https://www.fondeino.com/'
        config.polla_cerrada = False

        config.save()

        accion = 'creada' if created else 'actualizada'
        self.stdout.write(self.style.SUCCESS(f'OK ConfiguracionPolla {accion} correctamente.'))
        self.stdout.write(f'  Torneo: {config.nombre_torneo}')
        self.stdout.write(f'  Inscripciones: {config.fecha_inicio_inscripciones.strftime("%d/%m/%Y")} - {config.fecha_cierre_inscripciones.strftime("%d/%m/%Y")}')
        self.stdout.write(f'  Cierre pronostico campeon: {config.fecha_cierre_pronostico_campeon.strftime("%d/%m/%Y %H:%M")}')
        self.stdout.write(f'  Puntos grupos: resultado={config.pts_resultado_grupos}, marcador=+{config.pts_marcador_grupos} (total 3)')
        self.stdout.write(f'  Puntos eliminatorias: resultado={config.pts_resultado_eliminatoria}, marcador=+{config.pts_marcador_eliminatoria} (total 6)')
