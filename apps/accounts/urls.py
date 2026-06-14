from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('inicio/', views.dashboard, name='dashboard'),
    path('panel/', views.panel_selector, name='panel_selector'),
    path('debug-db/', views.debug_db, name='debug_db'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('usuarios/crear/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/password/', views.usuario_cambiar_password, name='usuario_password'),
    path('mi-password/', views.cambiar_mi_password, name='cambiar_mi_password'),
    path('manual/', views.manual_usuario, name='manual'),
    path('protocolo-comite/', views.protocolo_comite, name='protocolo_comite'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/backup/', views.admin_descargar_backup, name='admin_descargar_backup'),
    path('usuarios/<int:pk>/toggle/', views.toggle_permiso, name='toggle_permiso'),
    path('usuarios/<int:pk>/reset-password/', views.resetear_password_polla, name='resetear_password_polla'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
    path('olvide-password/', views.olvide_password, name='password_reset'),
]
