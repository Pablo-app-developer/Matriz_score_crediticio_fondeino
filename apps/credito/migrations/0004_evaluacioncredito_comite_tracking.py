from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('credito', '0003_evaluacioncredito_otras_obligaciones'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluacioncredito',
            name='fecha_decision_comite',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluacioncredito',
            name='registrado_por_comite',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='decisiones_comite',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
