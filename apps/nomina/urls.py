from django.urls import path
from . import views

app_name = 'nomina'

urlpatterns = [
    path('upload/', views.upload_nomina, name='upload'),
    path('', views.lista_nomina, name='lista'),
]
