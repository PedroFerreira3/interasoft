# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Usuario
from .forms import ProfessorForm, AlunoForm


# Mixin para verificar se o usuário é uma escola
class EscolaRequiredMixin:
    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.tipo == 'escola', login_url='usuarios:login'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# Decorator para views baseadas em função
def escola_required(view_func):
    decorated_view = login_required(
        user_passes_test(
            lambda u: u.tipo == 'escola',
            login_url='usuarios:login'
        )(view_func)
    )
    return decorated_view


@login_required
def redirecionar_usuario(request):
    if request.user.tipo == 'escola':
        return redirect('usuarios:dashboard_escola')
    elif request.user.tipo == 'professor':
        return redirect('usuarios:dashboard_professor')
    elif request.user.tipo == 'aluno':
        return redirect('usuarios:dashboard_aluno')
    return redirect('usuarios:login')


@escola_required
def dashboard_escola(request):
    total_alunos = Usuario.objects.filter(escola=request.user, tipo='aluno').count()
    total_professores = Usuario.objects.filter(escola=request.user, tipo='professor').count()

    context = {
        'total_alunos': total_alunos,
        'total_professores': total_professores,
    }
    return render(request, 'usuarios/escola/dashboard.html', context)


class AlunoListView(EscolaRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/escola/aluno_list.html'
    context_object_name = 'alunos'

    def get_queryset(self):
        return Usuario.objects.filter(
            escola=self.request.user,
            tipo='aluno'
        )


class ProfessorListView(EscolaRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/escola/professor_list.html'
    context_object_name = 'professores'

    def get_queryset(self):
        return Usuario.objects.filter(
            escola=self.request.user,
            tipo='professor'
        )


class AlunoCreateView(EscolaRequiredMixin, CreateView):
    model = Usuario
    form_class = AlunoForm
    template_name = 'usuarios/escola/aluno_form.html'
    success_url = reverse_lazy('usuarios:aluno_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Aluno cadastrado com sucesso!')
        return super().form_valid(form)


class ProfessorCreateView(EscolaRequiredMixin, CreateView):
    model = Usuario
    form_class = ProfessorForm
    template_name = 'usuarios/escola/professor_form.html'
    success_url = reverse_lazy('usuarios:professor_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['escola'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Professor cadastrado com sucesso!')
        return super().form_valid(form)


@escola_required
def toggle_ativo(request, pk):
    usuario = Usuario.objects.filter(escola=request.user, pk=pk).first()
    if usuario:
        usuario.ativo = not usuario.ativo
        usuario.save()
        messages.success(request, f'Status de {usuario.username} alterado com sucesso!')
    else:
        messages.error(request, 'Usuário não encontrado')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:dashboard_escola'))

@login_required
@user_passes_test(lambda u: u.tipo == 'professor', login_url='usuarios:login')
def dashboard_professor(request):
    return render(request, 'usuarios/professor/dashboard.html')

@login_required
@user_passes_test(lambda u: u.tipo == 'aluno', login_url='usuarios:login')
def dashboard_aluno(request):
    return render(request, 'usuarios/aluno/dashboard.html')