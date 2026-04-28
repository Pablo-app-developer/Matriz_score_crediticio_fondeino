from django.db import models
from django.conf import settings
from datetime import date
from dateutil.relativedelta import relativedelta


class CargaNomina(models.Model):
    """Registro de cada carga mensual de nómina."""
    archivo = models.FileField(upload_to='nomina/')
    periodo = models.CharField(max_length=20, help_text="Ej: 2026-04")
    fecha_carga = models.DateTimeField(auto_now_add=True)
    cargado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_empleados = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Carga de Nómina'
        verbose_name_plural = 'Cargas de Nómina'
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"Nómina {self.periodo} - {self.total_empleados} empleados"


class Empleado(models.Model):
    """Base de datos de empleados activos (última nómina cargada)."""
    carga = models.ForeignKey(CargaNomina, on_delete=models.CASCADE, related_name='empleados')

    cedula = models.CharField(max_length=20, db_index=True)
    nombre = models.CharField(max_length=200)
    estado = models.CharField(max_length=50, blank=True)
    area = models.CharField(max_length=100, blank=True)
    cargo = models.CharField(max_length=150, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_retiro = models.DateField(null=True, blank=True)
    fecha_contrato_hasta = models.DateField(null=True, blank=True)
    salario = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.cedula} - {self.nombre}"

    @property
    def tipo_vinculacion(self):
        if not self.fecha_contrato_hasta:
            return 'Indefinido'
        return 'A termino fijo'

    @property
    def antiguedad_meses(self):
        if not self.fecha_ingreso:
            return 0
        delta = relativedelta(date.today(), self.fecha_ingreso)
        return delta.years * 12 + delta.months
