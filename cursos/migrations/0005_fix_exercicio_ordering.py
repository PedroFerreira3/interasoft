# cursos/migrations/0005_fix_exercicio_ordering.py
from django.db import migrations


def set_correct_order_for_exercises(apps, schema_editor):
    Capitulo = apps.get_model('cursos', 'Capitulo')

    # Para cada curso no sistema
    for curso_id in Capitulo.objects.values_list('curso_id', flat=True).distinct():
        # Pega todas as aulas do curso, ordenadas
        aulas = Capitulo.objects.filter(
            curso_id=curso_id,
            tipo='aula'
        ).order_by('ordem')

        # Atualiza a ordem das aulas primeiro (1, 2, 3...)
        for index, aula in enumerate(aulas, start=1):
            if aula.ordem != index:
                aula.ordem = index
                aula.save()

            # Encontra o exercício relacionado
            exercicio = Capitulo.objects.filter(
                curso_id=curso_id,
                codigo=f"{aula.codigo}_ex",
                tipo='exercicio'
            ).first()

            if exercicio:
                # Define a ordem do exercício como ordem da aula + 0.5
                exercicio.ordem = index + 0.5
                exercicio.save()


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0004_alter_capitulo_options_alter_curso_options_and_more'),
    ]

    operations = [
        migrations.RunPython(set_correct_order_for_exercises),
    ]