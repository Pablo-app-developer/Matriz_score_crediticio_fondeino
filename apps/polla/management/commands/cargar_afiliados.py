"""
Comando: python manage.py cargar_afiliados <ruta_excel>

Columnas del Excel (insensible a mayúsculas):
  cedula, nombre_completo, correo, telefono, area, cantidad_pollas, motivo_doble

Comportamiento:
  - Afiliado nuevo -> se crea + inscripciones.
  - Afiliado existente -> se actualizan datos y se reporta. Si cantidad_pollas sube
    de 1 a 2, se crea la Polla B. Nunca se reduce de 2 a 1 (solo warning).
"""

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from apps.polla.models import Afiliado, InscripcionPolla


class Command(BaseCommand):
    help = 'Carga o actualiza afiliados desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo .xlsx')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Simula la carga sin guardar cambios en la base de datos'
        )

    def handle(self, *args, **options):
        ruta = options['archivo']
        dry_run = options['dry_run']

        try:
            df = pd.read_excel(ruta)
        except FileNotFoundError:
            raise CommandError(f'Archivo no encontrado: {ruta}')
        except Exception as e:
            raise CommandError(f'No se pudo leer el archivo: {e}')

        self.stdout.write(f'Filas encontradas: {len(df)}')
        if dry_run:
            self.stdout.write(self.style.WARNING('--- MODO DRY-RUN: no se guardan cambios ---'))

        col_map = {c.lower().strip(): c for c in df.columns}

        def get_col(row, *names):
            for n in names:
                if n in col_map:
                    val = row.get(col_map[n], '')
                    if pd.isna(val):
                        return ''
                    return str(val).strip()
            return ''

        creados, actualizados, nuevas_pollas, warnings, errores = [], [], [], [], []

        for idx, row in df.iterrows():
            fila = idx + 2

            cedula = get_col(row, 'cedula', 'cédula', 'documento', 'id')
            if not cedula:
                errores.append(f'Fila {fila}: cédula vacía, se omite.')
                continue

            nombre = get_col(row, 'nombre_completo', 'nombre', 'nombres')
            if not nombre:
                errores.append(f'Fila {fila}: nombre vacío para cédula {cedula}, se omite.')
                continue

            correo = get_col(row, 'correo', 'email')
            telefono = get_col(row, 'telefono', 'teléfono', 'celular')
            area = get_col(row, 'area', 'área', 'departamento')

            raw_pollas = get_col(row, 'cantidad_pollas', 'pollas')
            try:
                cantidad_pollas = int(float(raw_pollas)) if raw_pollas else 1
                if cantidad_pollas not in (1, 2):
                    cantidad_pollas = 1
            except (ValueError, TypeError):
                cantidad_pollas = 1

            motivo_raw = get_col(row, 'motivo_doble', 'motivo').upper()
            motivo_doble = motivo_raw if motivo_raw in ('NUEVO', 'AUMENTO') else None
            if cantidad_pollas == 2 and not motivo_doble:
                motivo_doble = 'NUEVO'

            try:
                afiliado = Afiliado.objects.get(cedula=cedula)

                afiliado.nombre_completo = nombre
                if correo:
                    afiliado.correo = correo
                if telefono:
                    afiliado.telefono = telefono
                if area:
                    afiliado.area = area

                if cantidad_pollas == 2 and afiliado.cantidad_pollas == 1:
                    afiliado.cantidad_pollas = 2
                    afiliado.motivo_doble_polla = motivo_doble
                    if not dry_run:
                        afiliado.save()
                        InscripcionPolla.objects.get_or_create(
                            afiliado=afiliado, numero_polla=2
                        )
                    nuevas_pollas.append(f'  {nombre} ({cedula}) — motivo: {motivo_doble}')
                elif cantidad_pollas == 1 and afiliado.cantidad_pollas == 2:
                    warnings.append(
                        f'  {nombre} ({cedula}): Excel dice 1 polla pero ya tiene 2. '
                        'No se reduce automáticamente.'
                    )
                    if not dry_run:
                        afiliado.save()
                else:
                    if not dry_run:
                        afiliado.save()

                actualizados.append(f'  {nombre} ({cedula})')

            except Afiliado.DoesNotExist:
                if not dry_run:
                    afiliado = Afiliado.objects.create(
                        cedula=cedula,
                        nombre_completo=nombre,
                        correo=correo,
                        telefono=telefono,
                        area=area,
                        cantidad_pollas=cantidad_pollas,
                        motivo_doble_polla=motivo_doble if cantidad_pollas == 2 else None,
                    )
                    InscripcionPolla.objects.create(afiliado=afiliado, numero_polla=1)
                    if cantidad_pollas == 2:
                        InscripcionPolla.objects.create(afiliado=afiliado, numero_polla=2)
                creados.append(f'  {nombre} ({cedula})')

            except Exception as e:
                errores.append(f'  Fila {fila} ({cedula}): error inesperado — {e}')

        # ── Reporte ──
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[+] Creados: {len(creados)}'))
        for l in creados:
            self.stdout.write(l)

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO(f'[~] Ya existian (actualizados): {len(actualizados)}'))
        for l in actualizados:
            self.stdout.write(l)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[*] Nuevas pollas asignadas: {len(nuevas_pollas)}'))
        for l in nuevas_pollas:
            self.stdout.write(l)

        if warnings:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'[!] Advertencias: {len(warnings)}'))
            for l in warnings:
                self.stdout.write(self.style.WARNING(l))

        if errores:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'[X] Errores: {len(errores)}'))
            for l in errores:
                self.stdout.write(self.style.ERROR(l))

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Dry-run completado. Nada fue guardado.'))
