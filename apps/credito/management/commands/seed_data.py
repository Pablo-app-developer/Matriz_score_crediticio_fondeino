"""
Comando para poblar datos iniciales del sistema FONDEINO:
- Modalidades de crédito
- Configuración de scoring
- Usuario administrador
"""
from django.core.management.base import BaseCommand
from apps.credito.models import Modalidad, Configuracion
from apps.accounts.models import Usuario


MODALIDADES = [
    ('Credi-Prima',          0.0170, 0.0150),
    ('Credi-Anticipo',       0.0170, 0.0150),
    ('Credi-Calamidad',      0.0100, 0.0150),
    ('Credi-Estudio',        0.0120, 0.0150),
    ('Credi-Emprender',      0.0120, 0.0400),
    ('Credi-Express',        0.0140, 0.0400),
    ('Credi-Libre Inversion',0.0160, 0.0800),
    ('Credi-Aportes',        0.0100, 0.0150),
    ('Credi-Consumo Hogar',  0.0120, 0.0150),
    ('Credi-Salud',          0.0100, 0.0150),
]


class Command(BaseCommand):
    help = 'Carga datos iniciales: modalidades, configuración y usuario admin'

    def add_arguments(self, parser):
        parser.add_argument('--admin-password', default='Fondeino2026*',
                            help='Contraseña del usuario administrador')

    def handle(self, *args, **options):
        # Modalidades
        created = 0
        for nombre, tasa, pd in MODALIDADES:
            _, c = Modalidad.objects.get_or_create(
                nombre=nombre,
                defaults={'tasa_mensual': tasa, 'pd_base': pd}
            )
            if c:
                created += 1
        self.stdout.write(f'  Modalidades: {created} creadas')

        # Configuración
        cfg, c = Configuracion.objects.get_or_create(pk=1)
        if c:
            self.stdout.write('  Configuración: creada con valores por defecto')
        else:
            self.stdout.write('  Configuración: ya existe')

        # Usuario admin
        pwd = options['admin_password']
        if not Usuario.objects.filter(username='admin').exists():
            u = Usuario.objects.create_superuser(
                username='admin',
                password=pwd,
                email='admin@fondeino.com',
                first_name='Administrador',
                last_name='FONDEINO',
                rol=Usuario.ROL_ADMIN,
            )
            self.stdout.write(f'  Usuario admin creado (contraseña: {pwd})')
        else:
            self.stdout.write('  Usuario admin ya existe')

        self.stdout.write(self.style.SUCCESS('OK - Datos iniciales cargados correctamente'))
