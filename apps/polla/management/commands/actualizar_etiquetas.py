"""
Comando: python manage.py actualizar_etiquetas

Asigna las etiquetas correctas del bracket FIFA 2026 a los partidos
de fases eliminatorias (Ronda de 32, Octavos, Cuartos, Semis, Final).

Los partidos de grupos NO se tocan.
"""
from django.core.management.base import BaseCommand
from apps.polla.models import Partido

# (numero_partido, etiqueta_local, etiqueta_visitante)
BRACKET = [
    # ── Ronda de 32 ── (partidos 73-88)
    (73,  '1° Grupo A',            '2° Grupo B'),
    (74,  '1° Grupo B',            '2° Grupo A'),
    (75,  '1° Grupo C',            '2° Grupo D'),
    (76,  '1° Grupo D',            '2° Grupo C'),
    (77,  '1° Grupo E',            '2° Grupo F'),
    (78,  '1° Grupo F',            '2° Grupo E'),
    (79,  '1° Grupo G',            '2° Grupo H'),
    (80,  '1° Grupo H',            '2° Grupo G'),
    (81,  '1° Grupo I',            '2° Grupo J'),
    (82,  '1° Grupo J',            '2° Grupo I'),
    (83,  '1° Grupo K',            '2° Grupo L'),
    (84,  '1° Grupo L',            '2° Grupo K'),
    (85,  'Mejor 3° (A/B/C/D)',    'Mejor 3° (E/F/G/H)'),
    (86,  'Mejor 3° (A/B/C/D)',    'Mejor 3° (E/F/G/H)'),
    (87,  'Mejor 3° (I/J/K/L)',    'Mejor 3° (A/B/C/D)'),
    (88,  'Mejor 3° (I/J/K/L)',    'Mejor 3° (I/J/K/L)'),
    # ── Octavos de final ── (partidos 89-96)
    (89,  'Ganador P73',           'Ganador P74'),
    (90,  'Ganador P75',           'Ganador P76'),
    (91,  'Ganador P77',           'Ganador P78'),
    (92,  'Ganador P79',           'Ganador P80'),
    (93,  'Ganador P81',           'Ganador P82'),
    (94,  'Ganador P83',           'Ganador P84'),
    (95,  'Ganador P85',           'Ganador P86'),
    (96,  'Ganador P87',           'Ganador P88'),
    # ── Cuartos de final ── (partidos 97-100)
    (97,  'Ganador P89',           'Ganador P90'),
    (98,  'Ganador P91',           'Ganador P92'),
    (99,  'Ganador P93',           'Ganador P94'),
    (100, 'Ganador P95',           'Ganador P96'),
    # ── Semifinales ── (101-102)
    (101, 'Ganador P97',           'Ganador P98'),
    (102, 'Ganador P99',           'Ganador P100'),
    # ── Tercer puesto ──
    (103, 'Perdedor SF1 (P101)',   'Perdedor SF2 (P102)'),
    # ── Final ──
    (104, 'Ganador SF1 (P101)',    'Ganador SF2 (P102)'),
]


class Command(BaseCommand):
    help = 'Asigna etiquetas del bracket FIFA 2026 a los partidos eliminatorios.'

    def handle(self, *args, **options):
        actualizados = 0
        no_encontrados = []

        for numero, et_local, et_visitante in BRACKET:
            try:
                p = Partido.objects.get(numero=numero)
                p.etiqueta_local = et_local
                p.etiqueta_visitante = et_visitante
                p.save(update_fields=['etiqueta_local', 'etiqueta_visitante'])
                actualizados += 1
                self.stdout.write(f'  P{numero}: {et_local} vs {et_visitante}')
            except Partido.DoesNotExist:
                no_encontrados.append(numero)

        self.stdout.write(self.style.SUCCESS(f'\nOK: {actualizados} partidos actualizados.'))
        if no_encontrados:
            self.stdout.write(self.style.WARNING(
                f'No encontrados: {no_encontrados} — verifica que el fixture esté cargado.'
            ))
