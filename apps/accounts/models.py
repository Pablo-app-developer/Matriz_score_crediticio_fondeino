from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_ADMIN = 'admin'
    ROL_COMITE = 'comite'
    ROLES = [
        (ROL_ADMIN, 'Administrador'),
        (ROL_COMITE, 'Comité de Crédito'),
    ]

    rol = models.CharField(max_length=10, choices=ROLES, default=ROL_COMITE)
    telefono = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.ROL_ADMIN or self.is_superuser
