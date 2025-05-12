# cursos/migrations/0003_improve_models.py
from django.db import migrations, models
import django.core.validators


def set_tipo_from_codigo(apps, schema_editor):
    Capitulo = apps.get_model('cursos', 'Capitulo')
    # Atualiza capítulos com '_ex' no código para tipo 'exercicio'
    Capitulo.objects.filter(codigo__iendswith='_ex').update(tipo='exercicio')
    # Garante que os demais são 'aula'
    Capitulo.objects.exclude(codigo__iendswith='_ex').update(tipo='aula')


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0002_initial'),  # Depende da sua última migração
    ]

    operations = [
        # Adiciona o campo tipo se ainda não existir
        migrations.AlterField(
            model_name='capitulo',
            name='tipo',
            field=models.CharField(
                choices=[('aula', 'Aula'), ('exercicio', 'Exercício')],
                default='aula',
                max_length=10
            ),
        ),

        # Adiciona constraints
        migrations.AlterUniqueTogether(
            name='capitulo',
            unique_together={('curso', 'ordem', 'tipo')},
        ),

        # Atualiza os tipos baseados no código existente
        migrations.RunPython(set_tipo_from_codigo),

        # Adiciona métodos aos modelos via RunPython (opcional)
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # Nada a fazer para frente
            reverse_code=lambda apps, schema_editor: None  # Nada a fazer para trás
        ),
    ]