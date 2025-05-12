# cursos/migrations/0005_fix_exercicio_relationships.py
from django.db import migrations


def fix_exercises(apps, schema_editor):
    Capitulo = apps.get_model('cursos', 'Capitulo')

    for exercicio in Capitulo.objects.filter(tipo='exercicio'):
        if exercicio.codigo and exercicio.codigo.endswith('_ex'):
            codigo_aula = exercicio.codigo[:-3]
            aula = Capitulo.objects.filter(
                curso=exercicio.curso,
                codigo=codigo_aula,
                tipo='aula'
            ).first()

            if aula:
                exercicio.ordem = float(aula.ordem) + 0.5
                exercicio.save()


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0006_alter_capitulo_ordem'),
    ]

    operations = [
        migrations.RunPython(fix_exercises),
    ]