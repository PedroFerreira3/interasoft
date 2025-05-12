from .models import Certificado
from django.utils import timezone

def gerar_certificado(aluno, curso):
    certificado, criado = Certificado.objects.get_or_create(
        aluno=aluno,
        curso=curso,
        defaults={'criado_em': timezone.now()}
    )
    return certificado
