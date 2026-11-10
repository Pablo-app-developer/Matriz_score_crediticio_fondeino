from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0008_evaluacioncredito_valores_credito_activo'),
    ]

    operations = [
        migrations.AddField(
            model_name='modalidad',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('LIBRE_INVERSION', 'Libre Inversión'),
                    ('ANTICIPO_PRIMA', 'Anticipo de Prima'),
                    ('CALAMIDAD', 'Calamidad'),
                    ('VIVIENDA', 'Vivienda'),
                    ('OTRO', 'Otro'),
                ],
                default='LIBRE_INVERSION',
                max_length=30,
                verbose_name='Categoría',
                help_text='Define las reglas de evaluación aplicables a esta modalidad',
            ),
        ),
    ]
