from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Progresso, Capitulo
from usuarios.models import Usuario
from django.core.exceptions import PermissionDenied
from django.urls import reverse

# Constantes
NOTA_MINIMA = 0
NOTA_MAXIMA = 10
NOTA_APROVACAO = 8


@csrf_exempt
def registrar_nota(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            capitulo_id = data.get('capitulo_id')
            nota = float(data.get('nota', 0))

            # Validações básicas
            if not all([user_id, capitulo_id, nota is not None]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Dados incompletos'
                }, status=400)

            if not NOTA_MINIMA <= nota <= NOTA_MAXIMA:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Nota deve estar entre {NOTA_MINIMA} e {NOTA_MAXIMA}'
                }, status=400)

            aluno = Usuario.objects.get(id=user_id)
            capitulo = Capitulo.objects.select_related('curso').get(id=capitulo_id)

            # Verifica matrícula
            if aluno not in capitulo.curso.alunos.all():
                raise PermissionDenied("Aluno não matriculado neste curso")

            is_exercicio = capitulo.tipo == 'exercicio'

            # Atualiza progresso
            progresso, created = Progresso.objects.update_or_create(
                aluno=aluno,
                capitulo=capitulo,
                defaults={
                    'nota': nota,
                    'concluido': is_exercicio and nota >= NOTA_APROVACAO
                }
            )

            response_data = {
                'status': 'success',
                'message': 'Nota registrada com sucesso',
                'data': {
                    'nota': nota,
                    'aprovado': nota >= NOTA_APROVACAO,
                    'tipo_capitulo': capitulo.tipo
                }
            }

            # Lógica de redirecionamento aprimorada
            if is_exercicio and nota >= NOTA_APROVACAO:
                aula_relacionada = capitulo.get_aula_relacionada()

                if aula_relacionada:
                    Progresso.objects.update_or_create(
                        aluno=aluno,
                        capitulo=aula_relacionada,
                        defaults={'concluido': True}
                    )

                # Encontra próxima aula liberada
                proxima_aula = Capitulo.objects.filter(
                    curso=capitulo.curso,
                    ordem__gt=capitulo.ordem,
                    tipo='aula'
                ).order_by('ordem').first()

                response_data = {
                    'status': 'success',
                    'message': 'Nota registrada com sucesso',
                    'data': {
                        'nota': nota,
                        'aprovado': True,
                        'tipo_capitulo': capitulo.tipo
                    }
                }

                if proxima_aula:
                    response_data['redirect_url'] = reverse(
                        'cursos:assistir_aula',
                        args=[proxima_aula.id]
                    )
                else:
                    response_data['redirect_url'] = reverse(
                        'cursos:curso_detalhe',
                        args=[capitulo.curso.id]
                    )

                return JsonResponse(response_data)

        except Usuario.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Usuário não encontrado'
            }, status=404)
        except Capitulo.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Capítulo não encontrado'
            }, status=404)
        except PermissionDenied as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=403)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro interno: {str(e)}'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    }, status=405)

@csrf_exempt
def concluir_capitulo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            capitulo_id = data.get('capitulo_id')

            if not all([user_id, capitulo_id]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Dados incompletos'
                }, status=400)

            usuario = Usuario.objects.get(id=user_id)
            capitulo = Capitulo.objects.select_related('curso').get(id=capitulo_id)

            # Verifica se o usuário está matriculado
            if usuario not in capitulo.curso.alunos.all():
                raise PermissionDenied("Usuário não matriculado neste curso")

            # Não permite marcar exercícios como concluídos diretamente
            if capitulo.tipo == 'exercicio':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Exercícios devem ser aprovados via registro de nota'
                }, status=400)

            progresso, created = Progresso.objects.update_or_create(
                aluno=usuario,
                capitulo=capitulo,
                defaults={'concluido': True}
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Capítulo marcado como concluído'
            })

        except (Usuario.DoesNotExist, Capitulo.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': 'Usuário ou capítulo não encontrado'
            }, status=404)
        except PermissionDenied as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=403)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro interno: {str(e)}'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Método não permitido'
    }, status=405)

