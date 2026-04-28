from django.urls import path
from . import views

app_name = 'credito'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nueva/', views.evaluacion, name='evaluacion'),
    path('historico/', views.historico, name='historico'),
    path('detalle/<int:pk>/', views.detalle, name='detalle'),
    path('detalle/<int:pk>/editar/', views.evaluacion_editar, name='evaluacion_editar'),
    path('detalle/<int:pk>/eliminar/', views.evaluacion_eliminar, name='evaluacion_eliminar'),
    path('detalle/<int:pk>/pdf/', views.evaluacion_pdf, name='evaluacion_pdf'),
    # API AJAX
    path('api/empleado/', views.buscar_empleado, name='api_empleado'),
    path('api/empleado/nombre/', views.buscar_empleado_nombre, name='api_empleado_nombre'),
    path('api/modalidad/', views.get_modalidad_tasa, name='api_modalidad'),
    # Admin
    path('configuracion/', views.configuracion, name='configuracion'),
    path('modalidades/', views.modalidades_lista, name='modalidades'),
    path('modalidades/nueva/', views.modalidad_crear, name='modalidad_crear'),
    path('modalidades/<int:pk>/editar/', views.modalidad_editar, name='modalidad_editar'),
]
