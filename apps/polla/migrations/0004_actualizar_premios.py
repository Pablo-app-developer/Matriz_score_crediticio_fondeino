from django.db import migrations


def actualizar_premios(apps, schema_editor):
    ConfiguracionPolla = apps.get_model('polla', 'ConfiguracionPolla')
    config = ConfiguracionPolla.objects.first()
    if config:
        config.premios_top5_general = (
            '1.° lugar: $150.000 | '
            '2.° lugar: Bono hamburguesa El Garaje | '
            '3.° lugar: Bono hamburguesa El Garaje'
        )
        config.premios_top5_grupos = '1.° lugar fase de grupos: $100.000'
        config.premio_campeon_sorteo = 'Bono hamburguesa El Garaje (sorteo entre quienes acierten el campeón)'
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0003_api_football_campos'),
    ]

    operations = [
        migrations.RunPython(actualizar_premios, migrations.RunPython.noop),
    ]
