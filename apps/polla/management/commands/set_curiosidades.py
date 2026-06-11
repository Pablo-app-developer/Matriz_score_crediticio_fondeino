"""
Carga datos curiosos manuales en el campo datos_previos de partidos específicos.
Uso: python manage.py set_curiosidades
"""
from django.core.management.base import BaseCommand
from apps.polla.models import Partido


CURIOSIDADES = {
    # México vs Sudáfrica — Partido inaugural del Mundial 2026
    ("México", "Sudáfrica"): [
        "Partido inaugural del Mundial 2026, jugado en el Estadio Azteca (Ciudad de México)",
        "Primer gol del torneo: Julián Quiñones (México) al min. 9, asistido por Erik Lira",
        "Raúl Jiménez cerró el 2-0 al min. 67 con asistencia de Roberto Alvarado",
        "Sudáfrica terminó con 9 jugadores: Sithole expulsado al 50' y Zwane al 84'",
        "México es uno de los tres países anfitriones del torneo junto a EE.UU. y Canadá",
    ],
    # Corea del Sur vs República Checa — Jornada 1 Grupo A
    ("Corea del Sur", "República Checa"): [
        "Primera participación de República Checa en un Mundial desde Alemania 2006 (20 años)",
        "Corea del Sur no perdió ningún partido en la fase de clasificación AFC",
        "Primer choque competitivo oficial entre ambas selecciones en un Mundial",
        "Se disputó en el Estadio Akron (Guadalajara), casa del Chivas de Guadalajara",
        "República Checa clasificó al Mundial tras superar el repechaje europeo",
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
