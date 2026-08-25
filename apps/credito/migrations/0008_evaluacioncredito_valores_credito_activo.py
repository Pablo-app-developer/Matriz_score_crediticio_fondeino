from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0007_evaluacioncredito_anulacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='valor_inicial_credito_activo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='valor_pagado_credito_activo',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
