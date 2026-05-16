from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_usuario_es_admin_polla_alter_usuario_rol'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='debe_cambiar_password',
            field=models.BooleanField(default=False, verbose_name='Debe cambiar contraseña'),
        ),
    ]
