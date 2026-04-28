from django.urls import path
from . import views

app_name = 'credito'

urlpatterns = [
    path('', views.evaluacion, name='evaluacion'),
    path('historico/', views.historico, name='historico'),
    path('detalle/<int:pk>/', views.detalle, name='detalle'),
    # API AJAX
    path('api/empleado/', views.buscar_empleado, name='api_empleado'),
    path('api/modalidad/', views.get_modalidad_tasa, name='api_modalidad'),
    # Admin
    path('configuracion/', views.configuracion, name='configuracion'),
    path('modalidades/', views.modalidades_lista, name='modalidades'),
    path('modalidades/nueva/', views.modalidad_crear, name='modalidad_crear'),
    path('modalidades/<int:pk>/editar/', views.modalidad_editar, name='modalidad_editar'),
]
