from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal


class Curso(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    descricao = models.TextField()
    # Altere de ForeignKey para ManyToManyField
    escolas = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='cursos_da_escola',
        limit_choices_to={'tipo': 'escola'}
    )
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='cursos_lecionados',
        blank=True
    )
    alunos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='cursos_matriculados',
        blank=True
    )

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        return self.nome

    def get_capitulos_aula(self):
        """Retorna apenas capítulos do tipo aula, ordenados"""
        return self.capitulo_set.filter(tipo='aula').order_by('ordem')

    def get_progresso_aluno(self, aluno):
        """Retorna o progresso de um aluno neste curso"""
        return Progresso.objects.filter(
            aluno=aluno,
            capitulo__curso=self
        ).select_related('capitulo')

    def progresso_percentual(self, aluno):
        """Calcula o progresso baseado apenas em aulas, considerando exercícios relacionados"""
        capitulos_aula = self.get_capitulos_aula()
        total = capitulos_aula.count()
        if total == 0:
            return 0

        concluidos = 0

        for aula in capitulos_aula:
            exercicio = aula.get_exercicio_relacionado()

            if exercicio:
                # Para aulas com exercício: verifica se o exercício foi aprovado
                progresso_ex = Progresso.objects.filter(
                    aluno=aluno,
                    capitulo=exercicio,
                    nota__gte=8
                ).first()
                if progresso_ex:
                    concluidos += 1
            else:
                # Para aulas sem exercício: verifica se a aula foi concluída
                progresso_aula = Progresso.objects.filter(
                    aluno=aluno,
                    capitulo=aula,
                    concluido=True
                ).first()
                if progresso_aula:
                    concluidos += 1

        return int((concluidos / total) * 100)


class Capitulo(models.Model):
    TIPO_AULA = 'aula'
    TIPO_EXERCICIO = 'exercicio'
    TIPO_CHOICES = [
        (TIPO_AULA, 'Aula'),
        (TIPO_EXERCICIO, 'Exercício'),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    codigo = models.CharField(max_length=100, blank=True, null=True)
    ordem = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Use valores como 1.0 para aulas e 1.5 para exercícios relacionados"
    )
    url = models.CharField(max_length=200)
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default=TIPO_AULA
    )

    class Meta:
        ordering = ['curso', 'ordem', 'tipo']
        unique_together = ('curso', 'ordem', 'tipo')
        verbose_name = 'Capítulo'
        verbose_name_plural = 'Capítulos'

    def __str__(self):
        return f"{self.curso.nome} - {self.get_tipo_display()} {self.ordem}: {self.titulo}"

    def get_exercicio_relacionado(self):
        """Retorna o exercício exato para esta aula"""
        if self.tipo == self.TIPO_AULA:
            return self.curso.capitulo_set.filter(
                ordem=self.ordem + Decimal('0.5'),
                tipo=self.TIPO_EXERCICIO
            ).first()
        return None

    def get_aula_relacionada(self):
        """Retorna a aula exata para este exercício"""
        if self.tipo == self.TIPO_EXERCICIO:
            return self.curso.capitulo_set.filter(
                ordem=self.ordem - Decimal('0.5'),
                tipo=self.TIPO_AULA
            ).first()
        return None

    def clean(self):
        # Validação de ordem para exercícios
        if self.tipo == 'exercicio':
            parte_decimal = float(self.ordem) % 1
            if parte_decimal != 0.5:
                raise ValidationError({
                    'ordem': 'Exercícios devem ter ordem terminando em .5 (ex: 1.5, 2.5)'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Progresso(models.Model):
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'aluno'}
    )
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE)
    concluido = models.BooleanField(default=False)
    nota = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('aluno', 'capitulo')
        verbose_name = 'Progresso'
        verbose_name_plural = 'Progressos'

    def __str__(self):
        return f"{self.aluno.username} - {self.capitulo.titulo} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-liberação de capítulos
        if self.capitulo.tipo == Capitulo.TIPO_EXERCICIO:
            if self.nota and float(self.nota) >= 8:
                self.concluido = True
                # Libera próxima aula
                proxima_ordem = int(float(self.capitulo.ordem)) + 0.5
                proxima_aula = Capitulo.objects.filter(
                    curso=self.capitulo.curso,
                    ordem=proxima_ordem,
                    tipo=Capitulo.TIPO_AULA
                ).first()
                if proxima_aula:
                    Progresso.objects.get_or_create(
                        aluno=self.aluno,
                        capitulo=proxima_aula
                    )

        super().save(*args, **kwargs)

    @property
    def status(self):
        if self.capitulo.tipo == Capitulo.TIPO_EXERCICIO:
            return f"Nota: {self.nota}/10" if self.nota is not None else "Pendente"
        return "Concluído" if self.concluido else "Pendente"

    @property
    def aprovado(self):
        """Verifica se o progresso está aprovado"""
        if self.capitulo.tipo == Capitulo.TIPO_EXERCICIO:
            return self.nota is not None and float(self.nota) >= 8
        return self.concluido

    def save(self, *args, **kwargs):
        # Auto-marca como concluído se for exercício aprovado
        if self.capitulo.tipo == Capitulo.TIPO_EXERCICIO and self.aprovado:
            self.concluido = True
        super().save(*args, **kwargs)