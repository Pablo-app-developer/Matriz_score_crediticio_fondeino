from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polla', '0010_configuracionpolla_campeon_habilitado'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscripcionpolla',
            name='posicion_anterior',
            field=models.IntegerField(
                blank=True,
                help_text='Posición global antes del último recálculo (para delta gamificado).',
                null=True,
            ),
        ),
    ]
