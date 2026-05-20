from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0004_evaluacioncredito_comite_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='edicion_desbloqueada',
            field=models.BooleanField(
                default=False,
                help_text='Permite editar la evaluación aunque el comité ya tomó una decisión.'
            ),
        ),
    ]
