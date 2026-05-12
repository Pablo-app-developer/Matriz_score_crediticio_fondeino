from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.credito.models import EvaluacionCredito, Modalidad
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Restaura la evaluación #19 como placeholder editable'

    def handle(self, *args, **options):
        if EvaluacionCredito.objects.filter(pk=19).exists():
            self.stdout.write(self.style.WARNING('Ya existe una evaluación con ID 19.'))
            return

        User = get_user_model()
        user = User.objects.filter(rol='admin').first() or User.objects.first()
        modalidad = Modalidad.objects.filter(activa=True).first() or Modalidad.objects.first()

        if not user or not modalidad:
            self.stdout.write(self.style.ERROR('Se necesita al menos un usuario y una modalidad en la base de datos.'))
            return

        ev = EvaluacionCredito(
            pk=19,
            evaluado_por=user,
            tipo_documento='C.C.',
            cedula='0',
            nombre_completo='[RESTAURAR - Completar datos]',
            area='', cargo='',
            tipo_vinculacion='Indefinido',
            antiguedad_meses=0,
            salario_bruto=0,
            puntaje_datacredito=700,
            tiene_credito_activo=False,
            pct_capital_pagado=0,
            cuotas_otras_entidades=0,
            otras_obligaciones=[],
            cuota_aporte=0, cuota_ahorro=0,
            saldo_aportes=0, saldo_ahorros=0,
            modalidad=modalidad,
            fecha_desembolso=timezone.now().date(),
            monto_solicitado=1,
            n_cuotas=1,
            motivo='Restaurada',
            salario_neto=0, minimo_vital=0,
            total_cuotas=0, disponible_final=0,
            estado_mv='Pendiente',
            pct_endeudamiento=0,
            score_datacredito=0, score_antiguedad=0,
            score_vinculacion=0, score_capacidad_pago=0,
            score_garantias=0, score_credito_activo=0,
            score_total=0,
            clasificacion='ALTO RIESGO',
            decision='REVISAR',
        )
        ev.save()
        self.stdout.write(self.style.SUCCESS(
            'Evaluación #19 creada como placeholder. Ábrala en el sistema y use "Editar" para ingresar los datos correctos.'
        ))
