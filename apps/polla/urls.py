from django.urls import path
from . import views

app_name = 'polla'

urlpatterns = [
    # Públicas
    path('', views.index, name='index'),
    path('ranking/', views.ranking, name='ranking'),
    path('reglamento/', views.reglamento, name='reglamento'),

    # Afiliado (requiere login + afiliado activo)
    path('activar/', views.activar_cuenta, name='activar_cuenta'),
    path('pronosticos/', views.pronosticos, name='pronosticos'),
    path('pronosticos/guardar/', views.guardar_pronostico, name='guardar_pronostico'),
    path('campeon/', views.campeon, name='campeon'),
    path('mis-pronosticos/', views.mis_pronosticos, name='mis_pronosticos'),
    path('perfil/<int:afiliado_id>/', views.perfil_afiliado, name='perfil_afiliado'),

    # API
    path('api/empleado/', views.api_empleado_por_cedula, name='api_empleado_por_cedula'),

    # Admin
    path('admin/afiliados/', views.admin_afiliados, name='admin_afiliados'),
    path('admin/afiliados/nuevo/', views.admin_afiliado_nuevo, name='admin_afiliado_nuevo'),
    path('admin/afiliados/<int:afiliado_id>/editar/', views.admin_afiliado_editar, name='admin_afiliado_editar'),
    path('admin/afiliados/<int:afiliado_id>/doble-polla/', views.admin_asignar_doble_polla, name='admin_asignar_doble_polla'),
    path('admin/afiliados/cargar/', views.admin_cargar_afiliados, name='admin_cargar_afiliados'),
    path('admin/resultados/', views.admin_cargar_resultados, name='admin_cargar_resultados'),
    path('admin/reporte/', views.admin_reporte, name='admin_reporte'),
    path('admin/cerrar/', views.admin_cerrar_polla, name='admin_cerrar_polla'),
]
