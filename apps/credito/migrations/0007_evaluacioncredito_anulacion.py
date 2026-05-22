from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0006_evaluacioncredito_tipo_credito'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='anulado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='fecha_anulacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='anulado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='evaluaciones_anuladas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='motivo_anulacion',
            field=models.TextField(blank=True),
        ),
    ]
