from django.contrib import admin
from .models import (
    Afiliado, Equipo, Partido, InscripcionPolla,
    Pronostico, PronosticoCampeon, ConfiguracionPolla,
)


@admin.register(Afiliado)
class AfiliadoAdmin(admin.ModelAdmin):
    list_display = ['cedula', 'nombre_completo', 'area', 'cantidad_pollas', 'motivo_doble_polla', 'activo', 'user']
    list_filter = ['cantidad_pollas', 'motivo_doble_polla', 'activo', 'area']
    search_fields = ['cedula', 'nombre_completo', 'correo']
    list_editable = ['cantidad_pollas', 'activo']
    readonly_fields = ['fecha_registro']


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['bandera_emoji', 'nombre', 'codigo_fifa', 'grupo']
    list_filter = ['grupo']
    search_fields = ['nombre', 'codigo_fifa']
    ordering = ['grupo', 'nombre']


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'fase', 'equipo_local', 'equipo_visitante', 'fecha_hora',
                    'goles_local', 'goles_visitante', 'finalizado']
    list_filter = ['fase', 'finalizado', 'jornada']
    list_editable = ['goles_local', 'goles_visitante', 'finalizado']
    search_fields = ['equipo_local__nombre', 'equipo_visitante__nombre']
    ordering = ['fecha_hora', 'numero']


@admin.register(InscripcionPolla)
class InscripcionPollaAdmin(admin.ModelAdmin):
    list_display = ['afiliado', 'numero_polla', 'puntos_totales', 'aciertos_resultado',
                    'aciertos_marcador', 'activa']
    list_filter = ['numero_polla', 'activa']
    search_fields = ['afiliado__cedula', 'afiliado__nombre_completo']
    ordering = ['-puntos_totales', '-aciertos_marcador']


@admin.register(Pronostico)
class PronosticoAdmin(admin.ModelAdmin):
    list_display = ['inscripcion', 'partido', 'goles_local', 'goles_visitante',
                    'acerto_resultado', 'acerto_marcador', 'puntos_obtenidos']
    list_filter = ['acerto_resultado', 'acerto_marcador', 'partido__fase']
    search_fields = ['inscripcion__afiliado__nombre_completo', 'inscripcion__afiliado__cedula']
    readonly_fields = ['puntos_obtenidos', 'acerto_resultado', 'acerto_marcador',
                       'fecha_creacion', 'fecha_modificacion']


@admin.register(PronosticoCampeon)
class PronosticoCampeonAdmin(admin.ModelAdmin):
    list_display = ['inscripcion', 'equipo', 'acerto', 'fecha_creacion']
    list_filter = ['equipo', 'acerto']
    list_editable = ['acerto']


@admin.register(ConfiguracionPolla)
class ConfiguracionPollaAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Torneo', {'fields': ('nombre_torneo', 'polla_cerrada')}),
        ('Puntos fase de grupos', {'fields': ('pts_resultado_grupos', 'pts_marcador_grupos')}),
        ('Puntos eliminatorias', {'fields': ('pts_resultado_eliminatoria', 'pts_marcador_eliminatoria')}),
        ('Premios', {'fields': ('premio_campeon_sorteo', 'premios_top5_grupos', 'premios_top5_general')}),
        ('Fechas', {'fields': ('fecha_inicio_inscripciones', 'fecha_cierre_inscripciones',
                               'fecha_cierre_pronostico_campeon')}),
        ('Captación', {'fields': ('mensaje_no_afiliado', 'enlace_afiliacion')}),
    )

    def has_add_permission(self, request):
        return not ConfiguracionPolla.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
