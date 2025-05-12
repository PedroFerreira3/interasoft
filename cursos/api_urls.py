from django.urls import path
from . import api_views
from cursos.views import boletim_notas_api

urlpatterns = [
    path('nota/', api_views.registrar_nota, name='registrar_nota'),
    path('concluir_capitulo/', api_views.concluir_capitulo, name='api_concluir_capitulo'),
    path('boletim/', boletim_notas_api, name='boletim_notas_api'),
]
