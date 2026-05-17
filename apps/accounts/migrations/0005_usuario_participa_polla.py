from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_usuario_debe_cambiar_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='participa_polla',
            field=models.BooleanField(
                default=False,
                verbose_name='Participa en la Polla',
                help_text='Miembro del comité que también juega la Polla Mundialista con su propia cuenta.',
            ),
        ),
    ]
