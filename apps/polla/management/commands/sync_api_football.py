"""
Comando: python manage.py sync_api_football

Consulta api-football.com para obtener los IDs de los 48 equipos
del Mundial FIFA 2026 (league=1, season=2026) y los guarda en
Equipo.api_football_id.

Requiere: API_FOOTBALL_KEY configurado en variables de entorno.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.polla.models import Equipo

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"


class Command(BaseCommand):
    help = 'Sincroniza IDs de equipos del Mundial 2026 con api-football.com'

    def handle(self, *args, **options):
        key = getattr(settings, 'API_FOOTBALL_KEY', '')
        if not key:
            self.stdout.write(self.style.ERROR(
                'API_FOOTBALL_KEY no está configurado. '
                'Agrégalo al archivo .env y a las variables de entorno en Vercel.'
            ))
            return

        headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        }

        self.stdout.write('Consultando equipos del Mundial 2026 (league=1, season=2026)...')
        try:
            r = requests.get(
                f"{BASE_URL}/teams",
                headers=headers,
                params={"league": 1, "season": 2026},
                timeout=15,
            )
            r.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al consultar la API: {e}'))
            return

        equipos_api = r.json().get('response', [])
        if not equipos_api:
            self.stdout.write(self.style.WARNING(
                'La API no devolvió equipos para WC 2026. '
                'Es posible que la temporada todavía no esté disponible. '
                'Intenta de nuevo más cerca del inicio del torneo (11 jun 2026).'
            ))
            return

        # Construir lookups: code (3 letras) y nombre normalizado
        api_por_code = {}
        api_por_nombre = {}
        for item in equipos_api:
            t = item['team']
            code = (t.get('code') or '').upper().strip()
            if code:
                api_por_code[code] = t['id']
            api_por_nombre[t['name'].lower().strip()] = t['id']

        actualizados = 0
        sin_match = []

        for equipo in Equipo.objects.all():
            api_id = api_por_code.get(equipo.codigo_fifa)
            if not api_id:
                api_id = api_por_nombre.get(equipo.nombre.lower().strip())
            if not api_id:
                # Búsqueda parcial por nombre
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
