from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0009_modalidad_categoria'),
    ]

    operations = [
        migrations.RenameField(
            model_name='evaluacioncredito',
            old_name='valor_pagado_credito_activo',
            new_name='saldo_credito_activo',
        ),
    ]
