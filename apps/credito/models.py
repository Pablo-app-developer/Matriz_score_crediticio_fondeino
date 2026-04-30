from django.db import models
from django.conf import settings
import json


class Modalidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    tasa_mensual = models.DecimalField(max_digits=6, decimal_places=4, help_text="Tasa mensual, e.g. 0.016")
    pd_base = models.DecimalField(max_digits=6, decimal_places=4, help_text="Probabilidad de default base")
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Modalidad'
        verbose_name_plural = 'Modalidades'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({float(self.tasa_mensual)*100:.1f}% mensual)"

    @property
    def tasa_nominal_anual(self):
        return float(self.tasa_mensual) * 12


class Configuracion(models.Model):
    """Parámetros del sistema configurables por el administrador."""

    # Mínimo vital
    porcentaje_minimo_vital = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.50,
        help_text="% del salario neto como mínimo vital (ej: 0.50 = 50%)"
    )

    # Thresholds y scores DataCrédito (max 25)
    t_dc_excelente = models.IntegerField(default=700, help_text="Puntaje DC: Umbral excelente")
    t_dc_bueno = models.IntegerField(default=500, help_text="Puntaje DC: Umbral bueno")
    t_dc_regular = models.IntegerField(default=300, help_text="Puntaje DC: Umbral regular")
    s_dc_excelente = models.IntegerField(default=25)
    s_dc_bueno = models.IntegerField(default=15)
    s_dc_regular = models.IntegerField(default=8)
    s_dc_malo = models.IntegerField(default=0)

    # Antigüedad (max 15)
    t_ant_1 = models.IntegerField(default=24, help_text="Antigüedad: meses umbral 1")
    t_ant_2 = models.IntegerField(default=12)
    t_ant_3 = models.IntegerField(default=6)
    t_ant_4 = models.IntegerField(default=3)
    s_ant_1 = models.IntegerField(default=15)
    s_ant_2 = models.IntegerField(default=12)
    s_ant_3 = models.IntegerField(default=8)
    s_ant_4 = models.IntegerField(default=4)
    s_ant_5 = models.IntegerField(default=0)

    # Vinculación (max 10)
    s_vinc_indefinido = models.IntegerField(default=10)
    s_vinc_fijo = models.IntegerField(default=7)
    s_vinc_servicios = models.IntegerField(default=4)

    # Capacidad de pago (max 25)
    t_cap_bueno = models.DecimalField(max_digits=4, decimal_places=2, default=0.30,
                                      help_text="% endeudamiento umbral bueno")
    t_cap_regular = models.DecimalField(max_digits=4, decimal_places=2, default=0.50,
                                        help_text="% endeudamiento umbral regular")
    s_cap_excelente = models.IntegerField(default=25)
    s_cap_regular = models.IntegerField(default=15)
    s_cap_malo = models.IntegerField(default=5)
    s_cap_bloqueado = models.IntegerField(default=0)

    # Garantías (max 15)
    t_gar_alta = models.DecimalField(max_digits=4, decimal_places=2, default=1.00,
                                     help_text="Cobertura umbral alta (100%)")
    t_gar_media = models.DecimalField(max_digits=4, decimal_places=2, default=0.50)
    t_gar_baja = models.DecimalField(max_digits=4, decimal_places=2, default=0.25)
    s_gar_alta = models.IntegerField(default=15)
    s_gar_media = models.IntegerField(default=10)
    s_gar_baja = models.IntegerField(default=5)
    s_gar_nula = models.IntegerField(default=0)

    # Historial crédito activo (max 10)
    t_hist_bueno = models.DecimalField(max_digits=4, decimal_places=2, default=0.30,
                                       help_text="% capital pagado umbral bueno")
    s_hist_sin = models.IntegerField(default=10)
    s_hist_bueno = models.IntegerField(default=7)
    s_hist_malo = models.IntegerField(default=3)

    # Clasificación
    t_cls_excelente = models.IntegerField(default=80)
    t_cls_bueno = models.IntegerField(default=60)
    t_cls_regular = models.IntegerField(default=40)

    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        verbose_name = 'Configuración'

    def __str__(self):
        return f"Configuración del sistema (actualizada {self.fecha_actualizacion:%d/%m/%Y})"

    def as_dict(self):
        """Convierte los campos a dict para pasarlo al scoring engine."""
        return {f.name: float(getattr(self, f.name)) if hasattr(getattr(self, f.name), '__float__')
                else getattr(self, f.name)
                for f in self._meta.fields
                if f.name not in ('id', 'fecha_actualizacion', 'actualizado_por')}

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


DECISION_COLORS = {
    'APROBAR': 'success',
    'REVISAR / SOLICITAR CODEUDOR': 'warning',
    'RECHAZAR': 'danger',
    'RECHAZAR - CUOTA EXCEDE LÍMITE': 'danger',
}

CLASIFICACION_COLORS = {
    'EXCELENTE': 'success',
    'BUENO': 'primary',
    'REGULAR': 'warning',
    'ALTO RIESGO': 'danger',
}


class EvaluacionCredito(models.Model):
    """Registro histórico de cada evaluación de crédito realizada."""

    # Meta
    evaluado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evaluaciones'
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)

    # Datos solicitante
    tipo_documento = models.CharField(max_length=20, default='C.C.')
    cedula = models.CharField(max_length=20)
    nombre_completo = models.CharField(max_length=200)
    area = models.CharField(max_length=100, blank=True)
    cargo = models.CharField(max_length=150, blank=True)
    tipo_vinculacion = models.CharField(max_length=50)
    antiguedad_meses = models.IntegerField()
    salario_bruto = models.DecimalField(max_digits=14, decimal_places=2)

    # Centrales de riesgo
    puntaje_datacredito = models.IntegerField()
    tiene_credito_activo = models.BooleanField(default=False)
    pct_capital_pagado = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    cuotas_otras_entidades = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Descuentos FONDEINO
    cuota_aporte = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cuota_ahorro = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Garantías
    saldo_aportes = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    saldo_ahorros = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Condiciones del crédito
    modalidad = models.ForeignKey(Modalidad, on_delete=models.PROTECT)
    fecha_desembolso = models.DateField()
    monto_solicitado = models.DecimalField(max_digits=14, decimal_places=2)
    n_cuotas = models.IntegerField()
    motivo = models.CharField(max_length=200, blank=True)

    # Resultados calculados
    salario_neto = models.DecimalField(max_digits=14, decimal_places=2)
    minimo_vital = models.DecimalField(max_digits=14, decimal_places=2)
    total_cuotas = models.DecimalField(max_digits=14, decimal_places=2)
    disponible_final = models.DecimalField(max_digits=14, decimal_places=2)
    estado_mv = models.CharField(max_length=60)
    pct_endeudamiento = models.DecimalField(max_digits=6, decimal_places=4)

    score_datacredito = models.IntegerField()
    score_antiguedad = models.IntegerField()
    score_vinculacion = models.IntegerField()
    score_capacidad_pago = models.IntegerField()
    score_garantias = models.IntegerField()
    score_credito_activo = models.IntegerField()
    score_total = models.IntegerField()

    clasificacion = models.CharField(max_length=30)
    decision = models.CharField(max_length=60)

    # Decisión del comité (opcional, registrada después)
    decision_comite = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Evaluación de Crédito'
        verbose_name_plural = 'Evaluaciones de Crédito'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f"{self.nombre_completo} - ${self.monto_solicitado:,.0f} - {self.decision}"

    @property
    def decision_color(self):
        for key, color in DECISION_COLORS.items():
            if key in self.decision:
                return color
        return 'secondary'

    @property
    def clasificacion_color(self):
        return CLASIFICACION_COLORS.get(self.clasificacion, 'secondary')

    @property
    def score_pct(self):
        return self.score_total


class PrestamoHistorico(models.Model):
    """Registro de créditos aprobados cargados desde Excel histórico."""

    fecha = models.DateField()
    cedula = models.CharField(max_length=20)
    nombre_completo = models.CharField(max_length=200)
    cargo = models.CharField(max_length=150, blank=True)
    proceso = models.CharField(max_length=150, blank=True)
    concepto_prestamo = models.CharField(max_length=200, blank=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='prestamos_historicos'
    )

    class Meta:
        verbose_name = 'Préstamo Histórico'
        verbose_name_plural = 'Préstamos Históricos'
        ordering = ['-fecha', 'nombre_completo']

    def __str__(self):
        return f"{self.nombre_completo} — ${self.monto:,.0f} — {self.fecha:%d/%m/%Y}"
