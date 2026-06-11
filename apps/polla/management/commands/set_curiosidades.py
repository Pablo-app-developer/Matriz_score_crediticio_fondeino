"""
Carga datos curiosos manuales en el campo datos_previos de partidos específicos.
Uso: python manage.py set_curiosidades
"""
from django.core.management.base import BaseCommand
from apps.polla.models import Partido


CURIOSIDADES = {
    # México vs Sudáfrica — Partido inaugural del Mundial 2026
    ("México", "Sudáfrica"): [
        "México llegó en racha: 6 victorias y 2 empates en 2026, con 15 goles a favor y solo 2 en contra",
        "Sudáfrica no ganó ningún partido en su preparación para el Mundial (0V-2E-2D en 2026)",
        "Primer gol del torneo: Julián Quiñones (México) al min. 9, asistido por Erik Lira",
        "Sudáfrica terminó con 9 jugadores: Sithole expulsado al min. 50 y Zwane al min. 84",
        "México juega en casa: es uno de los tres países anfitriones junto a EE.UU. y Canadá",
    ],
    # Corea del Sur vs República Checa — Jornada 1 Grupo A
    ("Corea del Sur", "República Checa"): [
        "Corea del Sur llegó en racha: clasificó invicta a Asia (6V-4E) y ganó sus dos amistosos previos 5-0 y 1-0",
        "Sin embargo, lleva 16 años sin ganar su partido inaugural en un Mundial (desde 2010)",
        "República Checa vuelve a un Mundial tras 20 años de ausencia (último fue Alemania 2006)",
        "Los checos llegaron por el camino difícil: repechaje UEFA, eliminando a Irlanda (4-3 en penales) y a Dinamarca (también en penales tras empatar 1-1)",
        "Primer enfrentamiento entre ambas selecciones en un Mundial",
    ],
}


class Command(BaseCommand):
    help = 'Carga datos curiosos manuales en datos_previos de partidos'

    def handle(self, *args, **options):
        actualizados = 0
        for (local, visita), curiosidades in CURIOSIDADES.items():
            qs = Partido.objects.filter(
                equipo_local__nombre=local,
                equipo_visitante__nombre=visita,
            )
            if not qs.exists():
                self.stdout.write(self.style.WARNING(
                    f'Partido no encontrado: {local} vs {visita}'
                ))
                continue
            for partido in qs:
                datos = partido.datos_previos or {}
                datos['curiosidades'] = curiosidades
                partido.datos_previos = datos
                partido.save(update_fields=['datos_previos'])
                actualizados += 1
                self.stdout.write(self.style.SUCCESS(
                    f'OK: {partido} — {len(curiosidades)} datos curiosos'
                ))
        self.stdout.write(f'\nTotal actualizados: {actualizados}')
