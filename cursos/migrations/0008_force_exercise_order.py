# cursos/migrations/0008_force_exercise_order.py
from django.db import migrations


def force_proper_order(apps, schema_editor):
    Capitulo = apps.get_model('cursos', 'Capitulo')

    for exercicio in Capitulo.objects.filter(tipo='exercicio'):
        aula = exercicio.get_aula_relacionada()
        if aula:
            exercicio.ordem = float(aula.ordem) + 0.5
            exercicio.save()


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0007_fix_exercicio_relationships'),  # Ajuste para sua última migração
    ]

    operations = [
        migrations.RunPython(force_proper_order),
    ]