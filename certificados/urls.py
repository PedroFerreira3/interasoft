from django.urls import path
from . import views

urlpatterns = [
    path('<int:certificado_id>/visualizar/', views.visualizar_certificado, name='visualizar_certificado'),
]
