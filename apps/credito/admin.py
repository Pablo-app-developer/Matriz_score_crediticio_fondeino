from django.contrib import admin
from .models import EvaluacionCredito, Modalidad, Configuracion


@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tasa_mensual', 'pd_base', 'activa']
    list_editable = ['activa']


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    pass


@admin.register(EvaluacionCredito)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ['fecha_evaluacion', 'cedula', 'nombre_completo', 'monto_solicitado',
                    'score_total', 'clasificacion', 'decision']
    list_filter = ['clasificacion', 'decision', 'modalidad']
    search_fields = ['cedula', 'nombre_completo']
    readonly_fields = [f.name for f in EvaluacionCredito._meta.fields
                       if f.name not in ('decision_comite', 'observaciones')]
