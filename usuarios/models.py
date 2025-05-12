# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('escola', 'Escola'),
        ('aluno', 'Aluno'),
        ('professor', 'Professor'),
    ]

    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='aluno'
    )

    # Adicionando campos necessários
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, blank=True)
    endereco = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    # Relação escola (apenas para alunos e professores)
    escola = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'tipo': 'escola'},
        related_name='membros'
    )

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'