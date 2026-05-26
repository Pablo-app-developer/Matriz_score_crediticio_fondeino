from django.db import migrations


def corregir_premio_grupos(apps, schema_editor):
    ConfiguracionPolla = apps.get_model('polla', 'ConfiguracionPolla')
    config = ConfiguracionPolla.objects.first()
    if config:
        config.premios_top5_grupos = '$100.000'
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0004_actualizar_premios'),
    ]

    operations = [
        migrations.RunPython(corregir_premio_grupos, migrations.RunPython.noop),
    ]
