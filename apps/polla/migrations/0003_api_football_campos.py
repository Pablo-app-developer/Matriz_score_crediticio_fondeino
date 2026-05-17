from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0002_partido_etiquetas'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='api_football_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID api-football.com'),
        ),
        migrations.AddField(
            model_name='partido',
            name='datos_previos',
            field=models.JSONField(blank=True, null=True, verbose_name='Datos API (caché)'),
        ),
        migrations.AddField(
            model_name='partido',
            name='datos_previos_ts',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Timestamp caché API'),
        ),
    ]
