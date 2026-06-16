from django.db import migrations


def actualizar_premio(apps, schema_editor):
    ConfiguracionPolla = apps.get_model('polla', 'ConfiguracionPolla')
    config, _ = ConfiguracionPolla.objects.get_or_create(pk=1)
    config.premios_top5_general = '$1.000.000'
    config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0012_snapshot_inicial_posiciones'),
    ]

    operations = [
        migrations.RunPython(actualizar_premio, migrations.RunPython.noop),
    ]
