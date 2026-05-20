from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0005_evaluacioncredito_edicion_desbloqueada'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='tipo_credito',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
