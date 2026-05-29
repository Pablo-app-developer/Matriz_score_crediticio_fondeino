from django.db import migrations


def actualizar_premios(apps, schema_editor):
    ConfiguracionPolla = apps.get_model('polla', 'ConfiguracionPolla')
    config, _ = ConfiguracionPolla.objects.get_or_create(pk=1)
    config.premios_top5_general = '$150.000'
    config.premio_campeon_sorteo = '$100.000 — sorteo entre quienes acierten al campeón'
    config.premios_top5_grupos = 'Hamburguesa + gaseosa'
    config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0006_autorizacion_descuento'),
    ]

    operations = [
        migrations.RunPython(actualizar_premios, migrations.RunPython.noop),
    ]
