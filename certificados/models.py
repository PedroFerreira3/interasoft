from django.db import models
from usuarios.models import Usuario
from cursos.models import Curso
from django.utils import timezone
import uuid

class Certificado(models.Model):
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'tipo': 'aluno'})
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    codigo = models.CharField(max_length=20, unique=True, editable=False, default='TEMPORARIO')

    class Meta:
        unique_together = ('aluno', 'curso')

    def __str__(self):
        return f'Certificado de {self.aluno.username} - {self.curso.nome}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            import uuid
            self.codigo = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

def gerar_certificado(aluno, curso):
    # Verifica se já existe um certificado para este aluno e curso
    if not Certificado.objects.filter(aluno=aluno, curso=curso).exists():
        codigo = str(uuid.uuid4()).replace('-', '')[:10]  # Gera código único de 10 caracteres
        Certificado.objects.create(
            aluno=aluno,
            curso=curso,
            criado_em=timezone.now(),
            codigo=codigo
        )