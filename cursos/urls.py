from django.urls import path
from . import views

app_name = 'cursos'

urlpatterns = [
    path('', views.home, name='home'),
    path('meus-cursos/', views.MeusCursosView.as_view(), name='meus_cursos'),
    path('meus-cursos/<int:curso_id>/', views.detalhes_curso, name='detalhes_curso'),
    path('curso/<int:pk>/matricular/', views.MatricularAlunosView.as_view(), name='matricular_alunos'),
    path('<int:curso_id>/', views.curso_detalhe, name='curso_detalhe'),
    path('<int:curso_id>/desmatricular/<int:aluno_id>/', views.desmatricular_aluno, name='desmatricular_aluno'),
    path('matricular/', views.matricular_alunos, name='matricular_alunos'),
    path('matriculados/', views.listar_matriculados, name='listar_matriculados'),
    path('remover/<int:curso_id>/<int:aluno_id>/', views.remover_aluno, name='remover_aluno'),

    # URLs para aulas e exercícios - ORGANIZADAS
    path('aula/<int:capitulo_id>/', views.assistir_aula, name='assistir_aula'),  # Aulas normais
    path('exercicio/<int:capitulo_id>/', views.assistir_capitulo, name='assistir_capitulo'),  # Exercícios

    path('capitulo/<int:capitulo_id>/marcar_concluido/', views.marcar_concluido, name='marcar_concluido'),

    path('curso/<int:curso_id>/gerar_certificado/', views.gerar_certificado, name='gerar_certificado'),
    path('<int:certificado_id>/visualizar/', views.visualizar_certificado, name='visualizar_certificado'),
    path('api/receber-nota/', views.receber_nota_exercicio, name='receber_nota_exercicio'),
    path('api/nota/', views.registrar_nota, name='registrar_nota'),
    path('boletim/', views.boletim_notas, name='boletim_notas'),
    path('<str:curso_slug>/<str:capitulo_url>_ex/', views.capitulo_exercicio, name='capitulo_exercicio'),
]

