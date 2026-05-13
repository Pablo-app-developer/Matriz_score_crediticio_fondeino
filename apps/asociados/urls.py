from django.urls import path
from . import views

app_name = 'asociados'

urlpatterns = [
    path('solicitud-credito/', views.solicitud_credito, name='solicitud_credito'),
]
