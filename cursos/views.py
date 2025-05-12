from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, FormView
from django.shortcuts import get_object_or_404, redirect, render
from django import forms
from django.contrib.auth.decorators import user_passes_test, login_required
from usuarios.models import Usuario
from .models import Curso, Capitulo, Progresso
from certificados.models import Certificado
from django.utils import timezone
from certificados.utils import gerar_certificado
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .serializers import NotaSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from django.contrib import messages



def home(request):
    return render(request, 'cursos/home.html')

# Formulário para selecionar alunos
class MatriculaForm(forms.Form):
    alunos = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(tipo='aluno'),
        widget=forms.CheckboxSelectMultiple
    )

# Página para listar os cursos da escola logada
class MeusCursosView(LoginRequiredMixin, ListView):
    model = Curso
    template_name = 'cursos/meus_cursos.html'

    def get_queryset(self):
        user = self.request.user
        print(f'Usuário logado: {user} (tipo: {user.tipo})')  # Debug do usuário logado

        if user.tipo == 'aluno':
            cursos = Curso.objects.filter(alunos=user)
            print(f'Cursos encontrados para aluno {user}: {[curso.nome for curso in cursos]}')  # Debug dos cursos
            return cursos

        # Para escola ou professor
        cursos = Curso.objects.filter(escola=user)
        print(f'Cursos encontrados para escola/professor {user}: {[curso.nome for curso in cursos]}')  # Debug
        return cursos



# Página para matricular alunos
class MatricularAlunosView(LoginRequiredMixin, FormView):
    template_name = 'cursos/matricular_alunos.html'
    form_class = MatriculaForm

    def dispatch(self, request, *args, **kwargs):
        self.curso = get_object_or_404(Curso, pk=kwargs['pk'], escola=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        alunos_selecionados = form.cleaned_data['alunos']
        self.curso.alunos.add(*alunos_selecionados)
        return redirect('cursos:meus_cursos')

    def get_form(self):
        form = super().get_form()
        # Só mostra alunos que ainda NÃO estão matriculados
        form.fields['alunos'].queryset = Usuario.objects.filter(
            tipo='aluno'
        ).exclude(cursos_matriculados=self.curso)
        return form

def usuario_e_escola(usuario):
    return usuario.is_authenticated and usuario.tipo == 'escola'

@login_required
@user_passes_test(usuario_e_escola)
def matricular_alunos(request):
    cursos = Curso.objects.filter(escola=request.user)
    alunos = Usuario.objects.filter(tipo='aluno')

    if request.method == 'POST':
        curso_id = request.POST.get('curso')
        aluno_ids = request.POST.getlist('alunos')

        curso = Curso.objects.get(id=curso_id)

        for aluno_id in aluno_ids:
            aluno = Usuario.objects.get(id=aluno_id)
            curso.alunos.add(aluno)

        return redirect('cursos:matricular_alunos')

    return render(request, 'cursos/matricular.html', {
        'cursos': cursos,
        'alunos': alunos,
    })


@login_required
def curso_detalhe(request, curso_id):
    try:
        curso = get_object_or_404(Curso, id=curso_id)

        # Verifica se o usuário tem acesso ao curso
        if request.user.tipo == 'aluno' and request.user not in curso.alunos.all():
            messages.error(request, "Você não está matriculado neste curso")
            return redirect('cursos:meus_cursos')

        if request.user.tipo == 'escola' and request.user not in curso.escolas.all():
            messages.error(request, "Este curso não está disponível para sua escola")
            return redirect('cursos:meus_cursos')

        # Só traz capítulos normais (exclui exercícios)
        capitulos = Capitulo.objects.filter(
            curso=curso
        ).exclude(
            codigo__icontains='_ex'
        ).order_by('ordem')

        alunos_matriculados = curso.alunos.all()

        capitulos_concluidos = Progresso.objects.filter(
            aluno=request.user,
            capitulo__in=capitulos,
            concluido=True
        ).values_list('capitulo_id', flat=True)

        # Progresso
        total = capitulos.count()
        concluidos = len(capitulos_concluidos)
        progresso_percentual = int((concluidos / total) * 100) if total > 0 else 0

        # Busca certificado se existir
        certificado = Certificado.objects.filter(aluno=request.user, curso=curso).first()

        return render(request, 'cursos/curso_detalhe.html', {
            'curso': curso,
            'alunos_matriculados': alunos_matriculados,
            'capitulos': capitulos,
            'capitulos_concluidos': capitulos_concluidos,
            'progresso_percentual': progresso_percentual,
            'certificado': certificado,
        })

    except Exception as e:
        messages.error(request, f"Ocorreu um erro: {str(e)}")
        return redirect('cursos:meus_cursos')

@user_passes_test(usuario_e_escola)
def desmatricular_aluno(request, curso_id, aluno_id):
    curso = get_object_or_404(Curso, id=curso_id, escola=request.user)
    aluno = get_object_or_404(Usuario, id=aluno_id, tipo='aluno')
    if request.method == 'POST':
        curso.alunos.remove(aluno)
    return redirect('curso_detalhe', curso_id=curso.id)

@login_required
@user_passes_test(usuario_e_escola)
def listar_matriculados(request):
    cursos = Curso.objects.filter(escola=request.user).prefetch_related('alunos')

    return render(request, 'cursos/listar_matriculados.html', {
        'cursos': cursos,
    })

@login_required
@user_passes_test(usuario_e_escola)
def remover_aluno(request, curso_id, aluno_id):
    curso = get_object_or_404(Curso, id=curso_id, escola=request.user)
    aluno = get_object_or_404(Usuario, id=aluno_id, tipo='aluno')  # Corrigido: Usuario em vez de User
    curso.alunos.remove(aluno)
    return redirect('listar_matriculados')


@login_required
def meus_cursos(request):
    aluno = request.user
    cursos = Curso.objects.filter(alunos=aluno)

    cursos_com_progresso = []
    for curso in cursos:
        cursos_com_progresso.append({
            'curso': curso,
            'progresso': curso.progresso_percentual(aluno)  # Já usa a nova lógica
        })

    return render(request, 'cursos/meus_cursos.html', {
        'object_list': cursos_com_progresso
    })


@login_required
def detalhes_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    if request.user.tipo == 'aluno' and request.user not in curso.alunos.all():
        messages.error(request, "Você não está matriculado neste curso")
        return redirect('cursos:meus_cursos')

    capitulos_aula = curso.get_capitulos_aula()
    progressos = Progresso.objects.filter(
        aluno=request.user,
        capitulo__curso=curso
    ).select_related('capitulo')

    progresso_dict = {p.capitulo_id: p for p in progressos}

    capitulos_concluidos = []
    capitulos_liberados = []
    mensagens_bloqueio = {}

    for index, capitulo in enumerate(capitulos_aula):
        exercicio = capitulo.get_exercicio_relacionado()

        # Verifica conclusão
        if exercicio:
            progresso_ex = progresso_dict.get(exercicio.id)
            concluido = progresso_ex and progresso_ex.nota and float(progresso_ex.nota) >= 8
        else:
            progresso_aula = progresso_dict.get(capitulo.id)
            concluido = progresso_aula and progresso_aula.concluido

        if concluido:
            capitulos_concluidos.append(capitulo.id)

        # Verifica liberação
        if index == 0:
            liberado = True
        else:
            cap_anterior = capitulos_aula[index - 1]
            ex_anterior = cap_anterior.get_exercicio_relacionado()

            if ex_anterior:
                progresso_ex_anterior = progresso_dict.get(ex_anterior.id)
                liberado = progresso_ex_anterior and progresso_ex_anterior.nota and float(
                    progresso_ex_anterior.nota) >= 8
                mensagem = "Complete o exercício anterior com nota ≥ 8"
            else:
                progresso_aula_anterior = progresso_dict.get(cap_anterior.id)
                liberado = progresso_aula_anterior and progresso_aula_anterior.concluido
                mensagem = "Complete o capítulo anterior"

            if not liberado:
                mensagens_bloqueio[capitulo.id] = mensagem

        if liberado:
            capitulos_liberados.append(capitulo.id)

    progresso_percentual = curso.progresso_percentual(request.user)
    certificado = Certificado.objects.filter(aluno=request.user, curso=curso).first()

    return render(request, 'cursos/curso_detalhe.html', {
        'curso': curso,
        'capitulos': capitulos_aula,
        'capitulos_liberados': capitulos_liberados,
        'capitulos_concluidos': capitulos_concluidos,
        'mensagens_bloqueio': mensagens_bloqueio,
        'progresso_percentual': progresso_percentual,
        'certificado': certificado,
    })


@login_required
def assistir_aula(request, capitulo_id):
    capitulo = get_object_or_404(Capitulo, id=capitulo_id)
    user = request.user
    curso = capitulo.curso

    # Verificação de matrícula
    if user not in curso.alunos.all():
        messages.error(request, "Você não está matriculado neste curso")
        return redirect('cursos:meus_cursos')

    # Verifica se é uma aula
    if capitulo.tipo != Capitulo.TIPO_AULA:
        return redirect('cursos:assistir_capitulo', capitulo_id=capitulo_id)

    # Verifica liberação
    capitulos_aula = curso.get_capitulos_aula()
    index = list(capitulos_aula).index(capitulo)

    if index > 0:
        cap_anterior = capitulos_aula[index - 1]
        ex_anterior = cap_anterior.get_exercicio_relacionado()

        if ex_anterior:
            progresso_ex = Progresso.objects.filter(
                aluno=user,
                capitulo=ex_anterior,
                nota__gte=8
            ).first()
            if not progresso_ex:
                messages.error(request, "Você precisa obter nota ≥ 8 no exercício anterior")
                return redirect('cursos:curso_detalhe', curso_id=curso.id)
        else:
            progresso_aula = Progresso.objects.filter(
                aluno=user,
                capitulo=cap_anterior,
                concluido=True
            ).first()
            if not progresso_aula:
                messages.error(request, "Você precisa completar o capítulo anterior")
                return redirect('cursos:curso_detalhe', curso_id=curso.id)

    # Renderização do conteúdo
    base_path = f"cursos/captivate_packages/{curso.nome.replace(' ', '_')}"
    file_name = f"cap{int(capitulo.ordem)}"
    captivate_path = f"{base_path}/{file_name}/index.html"

    return render(request, 'cursos/assistir_aula.html', {
        'capitulo': capitulo,
        'is_exercicio': False,
        'captivate_path': captivate_path,
        'minimo_aprovacao': 8
    })


@login_required
def gerar_certificado(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    user = request.user

    # Verifica se o usuário está matriculado
    if user not in curso.alunos.all():
        return redirect('detalhes_curso', curso_id=curso_id)

    # Verifica se já existe certificado
    if Certificado.objects.filter(aluno=user, curso=curso).exists():
        return redirect('detalhes_curso', curso_id=curso_id)

    # Cria novo certificado
    Certificado.objects.create(
        aluno=user,
        curso=curso,
        criado_em=timezone.now(),
        codigo=f'CERT-{user.id}-{curso.id}-{timezone.now().timestamp()}'
    )

    return redirect('detalhes_curso', curso_id=curso_id)

@login_required
def visualizar_certificado(request, certificado_id):
    certificado = get_object_or_404(Certificado, id=certificado_id, aluno=request.user)
    return render(request, 'certificados/visualizar_certificado.html', {'certificado': certificado})

@csrf_exempt
def receber_nota_exercicio(request):
    if request.method == "POST":
        aluno_id = request.POST.get('aluno_id')
        capitulo_id = request.POST.get('capitulo_id')
        nota = float(request.POST.get('nota', 0))  # Converta para float

        if aluno_id and capitulo_id and nota is not None:
            # Usa Progresso em vez de NotaExercicio
            progresso, created = Progresso.objects.update_or_create(
                aluno_id=aluno_id,
                capitulo_id=capitulo_id,
                defaults={
                    'nota': nota,
                    'concluido': True  # Marca como concluído automaticamente
                }
            )
            return JsonResponse({'status': 'sucesso', 'mensagem': 'Nota salva com sucesso!'})
        else:
            return JsonResponse({'status': 'erro', 'mensagem': 'Dados incompletos!'}, status=400)

    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido!'}, status=405)

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['cursos'] = context['object_list']
    return context


@api_view(['POST'])
def registrar_nota(request):
    serializer = NotaSerializer(data=request.data)
    if serializer.is_valid():
        user_id = serializer.validated_data['user_id']
        capitulo_id = serializer.validated_data['capitulo_id']
        nota = serializer.validated_data['nota']

        try:
            usuario = Usuario.objects.get(id=user_id)  # Alterado de CustomUser para Usuario
            capitulo = Capitulo.objects.get(id=capitulo_id)

            progresso, criado = Progresso.objects.get_or_create(
                aluno=usuario,  # Alterado de 'usuario' para 'aluno'
                capitulo=capitulo,
                defaults={
                    'nota': nota,
                    'concluido': True  # Alterado de 'completou' para 'concluido'
                }
            )

            if not criado:
                progresso.nota = nota
                progresso.concluido = True  # Atualiza o campo correto
                progresso.save()

            return Response({'mensagem': 'Nota registrada com sucesso!'})
        except Usuario.DoesNotExist:  # Alterado de CustomUser para Usuario
            return Response({'erro': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Capitulo.DoesNotExist:
            return Response({'erro': 'Capítulo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def boletim_notas_api(request):
    aluno = request.user
    cursos_com_notas = {}

    # Buscar todos os progressos do aluno, apenas dos capítulos com "_ex" (exercícios)
    progressos = Progresso.objects.filter(aluno=aluno, capitulo__url__icontains='_ex')

    for progresso in progressos:
        curso_nome = progresso.capitulo.curso.nome
        if curso_nome not in cursos_com_notas:
            cursos_com_notas[curso_nome] = []

        cursos_com_notas[curso_nome].append({
            'capitulo_ordem': progresso.capitulo.ordem,
            'capitulo_titulo': progresso.capitulo.titulo,
            'nota': progresso.nota
        })

    return Response({'cursos_com_notas': cursos_com_notas})

def get_exercicio_relacionado(capitulo):
    return Capitulo.objects.filter(
        curso=capitulo.curso,
        codigo=f"{capitulo.codigo}_ex"
    ).first()


@login_required
def assistir_capitulo(request, capitulo_id):
    try:
        capitulo = get_object_or_404(Capitulo, id=capitulo_id)

        # Verifica se é um exercício
        if capitulo.tipo != Capitulo.TIPO_EXERCICIO:
            return redirect('cursos:assistir_aula', capitulo_id=capitulo_id)

        # Verifica aula relacionada
        aula_relacionada = capitulo.get_aula_relacionada()
        if not aula_relacionada:
            messages.error(request, "Exercício sem aula relacionada")
            return redirect('cursos:meus_cursos')

        # Verifica se a aula foi concluída
        progresso_aula = Progresso.objects.filter(
            aluno=request.user,
            capitulo=aula_relacionada,
            concluido=True
        ).exists()

        if not progresso_aula:
            messages.error(request, "Complete a aula antes de fazer o exercício")
            return redirect('cursos:assistir_aula', capitulo_id=aula_relacionada.id)

        return render(request, 'cursos/assistir_aula.html', {
            'capitulo': capitulo,
            'is_exercicio': True,
            'captivate_path': f"cursos/captivate_packages/{capitulo.curso.nome.replace(' ', '_')}/cap{capitulo.ordem}_ex/index.html",
            'minimo_aprovacao': 8
        })

    except Exception as e:
        messages.error(request, f"Erro: {str(e)}")
        return redirect('cursos:meus_cursos')


@login_required
@require_POST
def marcar_concluido(request, capitulo_id):
    try:
        capitulo = get_object_or_404(Capitulo, id=capitulo_id)
        user = request.user

        # Só permite marcar aulas como concluídas
        if capitulo.tipo != Capitulo.TIPO_AULA:
            return JsonResponse({
                'status': 'error',
                'message': 'Ação permitida apenas para aulas'
            }, status=400)

        # Marca a aula como concluída
        Progresso.objects.update_or_create(
            aluno=user,
            capitulo=capitulo,
            defaults={'concluido': True}
        )

        # Busca o exercício relacionado (ordem + 0.5)
        exercicio = capitulo.get_exercicio_relacionado()

        if exercicio:
            # Libera o exercício mesmo se não tiver concluído aulas anteriores
            Progresso.objects.get_or_create(
                aluno=user,
                capitulo=exercicio
            )
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('cursos:assistir_capitulo', args=[exercicio.id])
            })

        # Se não houver exercício, busca próxima aula (para cursos sem exercícios)
        proxima_aula = Capitulo.objects.filter(
            curso=capitulo.curso,
            ordem=capitulo.ordem + 1,
            tipo=Capitulo.TIPO_AULA
        ).first()

        if proxima_aula:
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('cursos:assistir_aula', args=[proxima_aula.id])
            })

        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('cursos:curso_detalhe', args=[capitulo.curso.id])
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def boletim_notas(request):
    aluno = request.user
    cursos_com_notas = {}

    # Buscar apenas exercícios pelo tipo (não pelo código)
    progressos = Progresso.objects.filter(
        aluno=aluno,
        capitulo__tipo='exercicio'
    ).select_related('capitulo__curso')

    for progresso in progressos:
        curso_nome = progresso.capitulo.curso.nome
        if curso_nome not in cursos_com_notas:
            cursos_com_notas[curso_nome] = []

        cursos_com_notas[curso_nome].append({
            'capitulo_ordem': progresso.capitulo.ordem,
            'capitulo_titulo': progresso.capitulo.titulo,
            'nota': progresso.nota
        })

    return render(request, 'cursos/boletim_notas.html', {
        'cursos_com_notas': cursos_com_notas
    })



def capitulo_exercicio(request, curso_slug, capitulo_url):
    return render(request, 'curso/capitulo_exercicio.html', {
        'curso_slug': curso_slug,
        'capitulo_url': capitulo_url,
    })

