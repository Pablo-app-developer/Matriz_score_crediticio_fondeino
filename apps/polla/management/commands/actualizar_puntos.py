"""
Comando: python manage.py actualizar_puntos

Recalcula los puntos de todas las inscripciones activas. Idempotente.
Ejecutar después de cargar resultados de partidos.
"""

from django.core.management.base import BaseCommand

from apps.polla.models import ConfiguracionPolla
from apps.polla.scoring import recalcular_todo


class Command(BaseCommand):
    help = 'Recalcula los puntos de todas las inscripciones activas'

    def handle(self, *args, **options):
        config = ConfiguracionPolla.get()
        self.stdout.write('Recalculando puntos...')
        total = recalcular_todo(config)
        self.stdout.write(self.style.SUCCESS(f'OK Puntos actualizados para {total} inscripciones.'))
