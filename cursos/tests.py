from django.test import TestCase
from cursos.models import Curso, Capitulo
from usuarios.models import Usuario  # Adicione esta importação


class CapituloModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Configura dados iniciais corretamente"""
        # 1. Cria um usuário escola primeiro
        cls.escola = Usuario.objects.create_user(
            username='escola_teste',
            password='senha123',
            tipo='escola'  # Certifique-se que este campo existe
        )

        # 2. Agora cria o curso vinculado à escola
        cls.curso = Curso.objects.create(
            nome="Matemática Básica",
            escola=cls.escola  # Vincula ao usuário escola criado
        )

    def test_ordens_duplicadas_para_tipos_diferentes(self):
        """Testa se permite aula e exercício com mesma ordem"""
        aula = Capitulo.objects.create(
            curso=self.curso,
            ordem=1,
            tipo='aula',
            titulo="Introdução"
        )
        exercicio = Capitulo.objects.create(
            curso=self.curso,
            ordem=1,
            tipo='exercicio',
            titulo="Exercícios 1"
        )
        self.assertEqual(aula.ordem, exercicio.ordem)

    def test_ordens_duplicadas_mesmo_tipo(self):
        """Testa se bloqueia dois capítulos do mesmo tipo com mesma ordem"""
        # Cria o primeiro
        Capitulo.objects.create(
            curso=self.curso,
            ordem=1,
            tipo='aula',
            titulo="Aula 1"
        ).full_clean()

        # Tentativa duplicada deve falhar
        with self.assertRaises(ValidationError):
            cap = Capitulo(
                curso=self.curso,
                ordem=1,
                tipo='aula',
                titulo="Aula 1 Duplicada"
            )
            cap.full_clean()
            cap.save()