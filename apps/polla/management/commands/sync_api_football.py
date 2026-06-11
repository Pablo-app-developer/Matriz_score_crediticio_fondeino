"""
Comando: python manage.py sync_api_football

Consulta football-data.org para obtener los IDs de los equipos
del Mundial FIFA 2026 y los guarda en Equipo.api_football_id.

Requiere: FOOTBALL_DATA_KEY configurado en variables de entorno.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.polla.models import Equipo

BASE_URL = "https://api.football-data.org/v4"


class Command(BaseCommand):
    help = 'Sincroniza IDs de equipos del Mundial 2026 con football-data.org'

    def handle(self, *args, **options):
        key = getattr(settings, 'FOOTBALL_DATA_KEY', '')
        if not key:
            self.stdout.write(self.style.ERROR(
                'FOOTBALL_DATA_KEY no está configurado. '
                'Regístrate en football-data.org, obtén la clave gratuita '
                'y agrégala como variable de entorno en Vercel.'
            ))
            return

        headers = {"X-Auth-Token": key}

        self.stdout.write('Consultando equipos del Mundial 2026 (WC, season=2026)...')
        try:
            r = requests.get(
                f"{BASE_URL}/competitions/WC/teams",
                headers=headers,
                params={"season": 2026},
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al consultar la API: {e}'))
            return

        equipos_api = r.json().get('teams', [])
        if not equipos_api:
            self.stdout.write(self.style.WARNING(
                'La API no devolvió equipos para WC 2026. '
                'Es posible que la temporada todavía no esté disponible.'
            ))
            return

        # Lookups por tla (código 3 letras) y nombre normalizado
        api_por_tla = {}
        api_por_nombre = {}
        for t in equipos_api:
            tla = (t.get('tla') or '').upper().strip()
            if tla:
                api_por_tla[tla] = t['id']
            api_por_nombre[t['name'].lower().strip()] = t['id']
            short = (t.get('shortName') or '').lower().strip()
            if short:
                api_por_nombre[short] = t['id']

        actualizados = 0
        sin_match = []

        for equipo in Equipo.objects.all():
            api_id = api_por_tla.get(equipo.codigo_fifa)
            if not api_id:
                api_id = api_por_nombre.get(equipo.nombre.lower().strip())
            if not api_id:
                for nombre_api, aid in api_por_nombre.items():
                    if equipo.nombre.lower() in nombre_api or nombre_api in equipo.nombre.lower():
                        api_id = aid
                        break

            if api_id:
                equipo.api_football_id = api_id
                equipo.save(update_fields=['api_football_id'])
                actualizados += 1
                self.stdout.write(f'  OK {equipo.codigo_fifa} ({equipo.nombre}) → ID {api_id}')
            else:
                sin_match.append(f'{equipo.codigo_fifa} ({equipo.nombre})')

        self.stdout.write(self.style.SUCCESS(f'\nOK: {actualizados} equipos sincronizados.'))
        if sin_match:
            self.stdout.write(self.style.WARNING(
                f'Sin match ({len(sin_match)}): {", ".join(sin_match)}\n'
                'Actualiza api_football_id manualmente desde el admin de Django.'
            ))
