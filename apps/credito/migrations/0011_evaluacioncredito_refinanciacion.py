from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0010_rename_valor_pagado_saldo_credito_activo'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='es_refinanciacion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='cuota_credito_refinanciar',
            field=models.DecimalField(max_digits=14, decimal_places=2, default=0),
        ),
    ]
