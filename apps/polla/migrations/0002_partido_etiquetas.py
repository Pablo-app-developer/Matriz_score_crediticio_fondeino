from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='partido',
            name='etiqueta_local',
            field=models.CharField(blank=True, max_length=60, verbose_name='Etiqueta local'),
        ),
        migrations.AddField(
            model_name='partido',
            name='etiqueta_visitante',
            field=models.CharField(blank=True, max_length=60, verbose_name='Etiqueta visitante'),
        ),
    ]
