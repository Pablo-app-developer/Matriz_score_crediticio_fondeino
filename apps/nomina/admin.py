from django.contrib import admin
from .models import CargaNomina, Empleado


@admin.register(CargaNomina)
class CargaNominaAdmin(admin.ModelAdmin):
    list_display = ['periodo', 'fecha_carga', 'total_empleados', 'activa', 'cargado_por']
    list_filter = ['activa']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombre', 'area', 'cargo', 'salario']
    search_fields = ['cedula', 'nombre']
    list_filter = ['area']
