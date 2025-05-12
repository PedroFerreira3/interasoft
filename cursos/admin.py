from django.contrib import admin
from .models import Curso, Capitulo, Progresso
from django import forms
from django.core.exceptions import ValidationError
from usuarios.models import Usuario
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Max
import os
from django.conf import settings
from django.contrib import messages
from pathlib import Path

class CursoAdminForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = '__all__'
        widgets = {
            'escolas': forms.SelectMultiple(),  # Para melhor visualização
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra usuários por tipo
        self.fields['alunos'].queryset = Usuario.objects.filter(tipo='aluno')
        self.fields['professores'].queryset = Usuario.objects.filter(tipo='professor')
        self.fields['escolas'].queryset = Usuario.objects.filter(tipo='escola')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('escolas')


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    form = CursoAdminForm
    list_display = ('nome', 'listar_escolas', 'ativo', 'contagem_alunos')
    list_filter = ('ativo', 'escolas')
    search_fields = ('nome', 'descricao')
    filter_horizontal = ('professores', 'alunos')
    actions = ['importar_capitulos_automaticamente',
               'disponibilizar_para_todas_escolas']  # Todas ações em uma única lista

    def contagem_alunos(self, obj):
        return obj.alunos.count()

    contagem_alunos.short_description = 'Alunos'

    def listar_escolas(self, obj):
        return ", ".join([e.username for e in obj.escolas.all()])

    listar_escolas.short_description = 'Escolas'


    @admin.action(description="Importar capítulos automaticamente da pasta static")
    def importar_capitulos_automaticamente(self, request, queryset):
        for curso in queryset:
            try:
                # Caminho base no diretório static
                curso_path = curso.nome.replace(' ', '_')
                base_path = Path(settings.BASE_DIR) / 'static' / 'cursos' / 'captivate_packages' / curso_path

                if not base_path.exists():
                    self.message_user(request, f"Pasta não encontrada para o curso {curso.nome} em {base_path}",
                                      level=messages.ERROR)
                    continue

                created_count = 0
                updated_count = 0

                # Processa tanto capítulos quanto exercícios
                for dir_name in os.listdir(base_path):
                    dir_path = base_path / dir_name
                    if not dir_path.is_dir() or not dir_name.startswith('cap'):
                        continue

                    try:
                        # Determina se é exercício
                        is_exercicio = '_ex' in dir_name.lower()

                        # Extrai o número do capítulo (cap01 -> 1, cap02_ex -> 2)
                        cap_num = ''.join(filter(str.isdigit, dir_name.split('_')[0][3:]))
                        if not cap_num:
                            continue

                        ordem = float(cap_num)
                        if is_exercicio:
                            ordem += 0.5  # Exercícios ficam com ordem X.5

                        # Monta a URL correta
                        url = f"cursos/captivate_packages/{curso_path}/{dir_name}/index.html"

                        # Título amigável
                        tipo = 'exercicio' if is_exercicio else 'aula'
                        titulo = f"Capítulo {int(ordem) if not is_exercicio else int(ordem)} ({'Exercício' if is_exercicio else 'Aula'})"

                        # Cria/atualiza o capítulo
                        capitulo, created = Capitulo.objects.update_or_create(
                            curso=curso,
                            ordem=ordem,
                            tipo=tipo,
                            defaults={
                                'titulo': titulo,
                                'url': url,
                                'codigo': dir_name
                            }
                        )

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        self.message_user(request, f"Erro ao processar {dir_name}: {str(e)}", level=messages.WARNING)
                        continue

                self.message_user(request,
                                  f"Curso {curso.nome}: {created_count} capítulos criados, {updated_count} atualizados",
                                  level=messages.SUCCESS)

            except Exception as e:
                self.message_user(request, f"Erro ao processar curso {curso.nome}: {str(e)}", level=messages.ERROR)

    @admin.action(description="▶ Disponibilizar curso para TODAS as escolas")
    def disponibilizar_para_todas_escolas(self, request, queryset):
        # Obtém todas as escolas
        todas_escolas = Usuario.objects.filter(tipo='escola')

        cursos_atualizados = 0
        relacoes_criadas = 0

        for curso in queryset:
            # Verifica quais escolas ainda não estão associadas ao curso
            escolas_atuais = curso.escolas.all()
            escolas_a_adicionar = todas_escolas.exclude(pk__in=escolas_atuais.values_list('pk', flat=True))

            # Adiciona as novas relações
            if escolas_a_adicionar.exists():
                curso.escolas.add(*escolas_a_adicionar)
                relacoes_criadas += escolas_a_adicionar.count()
                cursos_atualizados += 1

        if relacoes_criadas > 0:
            self.message_user(
                request,
                f"Sucesso! {cursos_atualizados} curso(s) vinculados a {relacoes_criadas} nova(s) escola(s).",
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "Nenhum novo vínculo criado - os cursos selecionados já estão disponíveis para todas as escolas.",
                level=messages.INFO
            )




class CapituloAdminForm(forms.ModelForm):
    class Meta:
        model = Capitulo
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        curso = cleaned_data.get('curso')
        ordem = cleaned_data.get('ordem')
        tipo = cleaned_data.get('tipo')

        if not all([curso, ordem, tipo]):
            return

        # Verifica conflitos
        conflitos = Capitulo.objects.filter(
            curso=curso,
            ordem=ordem,
            tipo=tipo
        )

        if self.instance and self.instance.pk:
            conflitos = conflitos.exclude(pk=self.instance.pk)

        if conflitos.exists():
            tipo_display = dict(Capitulo._meta.get_field('tipo').choices).get(tipo)
            raise ValidationError(
                f"Já existe um {tipo_display} com ordem {ordem} neste curso. "
                f"Escolha uma ordem diferente ou altere o tipo."
            )


@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    form = CapituloAdminForm
    list_display = ('titulo', 'curso', 'tipo', 'ordem', 'codigo', 'url')
    list_editable = ('ordem', 'tipo')
    list_filter = ('curso', 'tipo')
    search_fields = ('titulo', 'codigo', 'curso__nome')
    ordering = ('curso', 'ordem')
    actions = ['reordenar_capitulos']

    def get_changelist_form(self, request, **kwargs):
        return CapituloAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Apenas para criação de novo capítulo
            curso_id = request.GET.get('curso')
            tipo = request.GET.get('tipo', 'aula')

            if curso_id and tipo:
                ultima_ordem = Capitulo.objects.filter(
                    curso_id=curso_id,
                    tipo=tipo
                ).aggregate(Max('ordem'))['ordem__max'] or 0

                form.base_fields['ordem'].initial = ultima_ordem + 1
        return form

    def save_model(self, request, obj, form, change):
        if 'ordem' in form.changed_data or 'tipo' in form.changed_data:
            try:
                with transaction.atomic():
                    # Primeiro verifica se a nova ordem/tipo já existe
                    conflito = Capitulo.objects.filter(
                        curso=obj.curso,
                        ordem=obj.ordem,
                        tipo=obj.tipo
                    ).exclude(pk=obj.pk).exists()

                    if conflito:
                        # Se houver conflito, primeiro reordena os capítulos existentes
                        self.reordenar_capitulos_apos_mudanca(obj)

                    super().save_model(request, obj, form, change)

            except IntegrityError as e:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"Não foi possível salvar. Já existe um capítulo com esta ordem e tipo neste curso. "
                    f"Por favor, escolha uma ordem diferente ou altere o tipo."
                )
        else:
            super().save_model(request, obj, form, change)

    def reordenar_capitulos_apos_mudanca(self, obj):
        """
        Reorganiza os capítulos após mudança de ordem ou tipo
        """
        # Capítulos do mesmo curso e tipo (exceto o atual)
        capitulos = Capitulo.objects.filter(
            curso=obj.curso,
            tipo=obj.tipo
        ).exclude(pk=obj.pk).order_by('ordem')

        nova_lista = []
        ordem_atual = 1

        # Reorganiza todos os capítulos
        for cap in capitulos:
            if ordem_atual == obj.ordem:
                ordem_atual += 1  # Pula a ordem do novo capítulo

            if cap.ordem != ordem_atual:
                cap.ordem = ordem_atual
                nova_lista.append(cap)

            ordem_atual += 1

        # Salva todos de uma vez
        Capitulo.objects.bulk_update(nova_lista, ['ordem'])

    @admin.action(description="Reordenar capítulos automaticamente")
    def reordenar_capitulos(self, request, queryset):
        """
        Ação para reordenar todos os capítulos selecionados
        """
        cursos_afetados = set()

        for curso in queryset.values_list('curso', flat=True).distinct():
            for tipo in ['aula', 'exercicio']:
                capitulos = Capitulo.objects.filter(
                    curso_id=curso,
                    tipo=tipo
                ).order_by('ordem', 'id')

                for index, cap in enumerate(capitulos, start=1):
                    if cap.ordem != index:
                        cap.ordem = index
                        cap.save()
                cursos_afetados.add(curso)

        self.message_user(
            request,
            f"Capítulos reordenados com sucesso para {len(cursos_afetados)} curso(s)."
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('curso')

@admin.register(Progresso)
class ProgressoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'get_curso', 'capitulo', 'nota', 'concluido', 'atualizado_em')
    list_filter = ('capitulo__curso', 'aluno', 'concluido')
    search_fields = ('aluno__username', 'capitulo__titulo')
    readonly_fields = ('atualizado_em',)
    list_select_related = ('aluno', 'capitulo', 'capitulo__curso')

    def get_curso(self, obj):
        return obj.capitulo.curso.nome
    get_curso.short_description = 'Curso'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'capitulo__curso', 'aluno'
        )