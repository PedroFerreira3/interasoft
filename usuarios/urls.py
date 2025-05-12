# usuarios/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    redirecionar_usuario,
    dashboard_escola,
    dashboard_professor,  # Agora esta view existe
    dashboard_aluno,  # Agora esta view existe
    AlunoListView,
    ProfessorListView,
    AlunoCreateView,
    ProfessorCreateView,
    toggle_ativo
)

app_name = 'usuarios'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='usuarios:login'), name='logout'),
    path('redirecionar/', redirecionar_usuario, name='redirecionar'),

    # Escola
    path('escola/dashboard/', dashboard_escola, name='dashboard_escola'),
    path('escola/alunos/', AlunoListView.as_view(), name='aluno_list'),
    path('escola/alunos/novo/', AlunoCreateView.as_view(), name='aluno_create'),
    path('escola/professores/', ProfessorListView.as_view(), name='professor_list'),
    path('escola/professores/novo/', ProfessorCreateView.as_view(), name='professor_create'),
    path('escola/toggle-ativo/<int:pk>/', toggle_ativo, name='toggle_ativo'),

    # Professor e Aluno
    path('professor/dashboard/', dashboard_professor, name='dashboard_professor'),
    path('aluno/dashboard/', dashboard_aluno, name='dashboard_aluno'),
]