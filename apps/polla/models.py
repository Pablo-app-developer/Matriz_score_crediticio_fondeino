from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


FASE_CHOICES = [
    ('GRUPOS', 'Fase de grupos'),
    ('TREINTA_DOS', 'Ronda de 32'),
    ('OCTAVOS', 'Octavos de final'),
    ('CUARTOS', 'Cuartos de final'),
    ('SEMIS', 'Semifinales'),
    ('TERCERO', 'Tercer puesto'),
    ('FINAL', 'Final'),
]

FASES_ELIMINATORIAS = ['TREINTA_DOS', 'OCTAVOS', 'CUARTOS', 'SEMIS', 'TERCERO', 'FINAL']


class Afiliado(models.Model):
    MOTIVO_DOBLE = [
        ('NUEVO', 'Nuevo asociado'),
        ('AUMENTO', 'Aumentó aportes'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='afiliado',
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cédula')
    nombre_completo = models.CharField(max_length=150, verbose_name='Nombre completo')
    correo = models.EmailField(blank=True, verbose_name='Correo electrónico')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    area = models.CharField(max_length=80, blank=True, verbose_name='Área')

    cantidad_pollas = models.IntegerField(
        default=1,
        choices=[(1, 'Una polla'), (2, 'Doble polla')],
        verbose_name='Cantidad de pollas',
    )
    motivo_doble_polla = models.CharField(
        max_length=10,
        choices=MOTIVO_DOBLE,
        null=True,
        blank=True,
        verbose_name='Motivo de doble polla',
    )

    acepto_reglamento = models.BooleanField(default=False, verbose_name='Aceptó el reglamento')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Afiliado'
        verbose_name_plural = 'Afiliados'
        ordering = ['nombre_completo']

    def __str__(self):
        sufijo = ' ⭐×2' if self.cantidad_pollas == 2 else ''
        return f'{self.nombre_completo} ({self.cedula}){sufijo}'

    @property
    def tiene_doble_polla(self):
        return self.cantidad_pollas == 2

    @property
    def motivo_doble_label(self):
        return dict(self.MOTIVO_DOBLE).get(self.motivo_doble_polla, '')


class Equipo(models.Model):
    nombre = models.CharField(max_length=60, verbose_name='Nombre')
    codigo_fifa = models.CharField(max_length=3, unique=True, verbose_name='Código FIFA')
    bandera_emoji = models.CharField(max_length=10, blank=True, verbose_name='Bandera')
    grupo = models.CharField(max_length=1, verbose_name='Grupo')

    class Meta:
        ordering = ['grupo', 'nombre']
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'

    def __str__(self):
        return f'{self.bandera_emoji} {self.nombre} ({self.codigo_fifa})'


class Partido(models.Model):
    numero = models.IntegerField(unique=True, verbose_name='Número FIFA')
    fase = models.CharField(max_length=12, choices=FASE_CHOICES, verbose_name='Fase')
    jornada = models.IntegerField(null=True, blank=True, verbose_name='Jornada')
    equipo_local = models.ForeignKey(
        Equipo, related_name='partidos_local', on_delete=models.PROTECT, verbose_name='Local'
    )
    equipo_visitante = models.ForeignKey(
        Equipo, related_name='partidos_visitante', on_delete=models.PROTECT, verbose_name='Visitante'
    )
    fecha_hora = models.DateTimeField(verbose_name='Fecha y hora (Colombia)')
    estadio = models.CharField(max_length=100, blank=True, verbose_name='Estadio')
    ciudad = models.CharField(max_length=60, blank=True, verbose_name='Ciudad')

    goles_local = models.IntegerField(null=True, blank=True, verbose_name='Goles local')
    goles_visitante = models.IntegerField(null=True, blank=True, verbose_name='Goles visitante')
    finalizado = models.BooleanField(default=False, verbose_name='Finalizado')

    class Meta:
        ordering = ['fecha_hora', 'numero']
        verbose_name = 'Partido'
        verbose_name_plural = 'Partidos'

    def __str__(self):
        return f'#{self.numero} {self.equipo_local} vs {self.equipo_visitante} ({self.get_fase_display()})'

    @property
    def es_eliminatoria(self):
        return self.fase in FASES_ELIMINATORIAS

    @property
    def cerrado_para_pronosticos(self):
        return timezone.now() >= self.fecha_hora

    @property
    def resultado_texto(self):
        if self.goles_local is None or self.goles_visitante is None:
            return None
        if self.goles_local > self.goles_visitante:
            return 'LOCAL'
        elif self.goles_local < self.goles_visitante:
            return 'VISITANTE'
        return 'EMPATE'


class InscripcionPolla(models.Model):
    afiliado = models.ForeignKey(
        Afiliado, on_delete=models.CASCADE, related_name='inscripciones'
    )
    numero_polla = models.IntegerField(
        choices=[(1, 'Polla A'), (2, 'Polla B')], default=1
    )
    activa = models.BooleanField(default=True)
    puntos_totales = models.IntegerField(default=0, db_index=True)
    aciertos_resultado = models.IntegerField(default=0)
    aciertos_marcador = models.IntegerField(default=0)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('afiliado', 'numero_polla')
        ordering = ['-puntos_totales', '-aciertos_marcador']
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'

    def __str__(self):
        label = 'A' if self.numero_polla == 1 else 'B'
        return f'{self.afiliado.nombre_completo} — Polla {label} ({self.puntos_totales} pts)'

    @property
    def label(self):
        return 'A' if self.numero_polla == 1 else 'B'


class Pronostico(models.Model):
    inscripcion = models.ForeignKey(
        InscripcionPolla, on_delete=models.CASCADE, related_name='pronosticos'
    )
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='pronosticos')
    goles_local = models.IntegerField(verbose_name='Goles local')
    goles_visitante = models.IntegerField(verbose_name='Goles visitante')
    puntos_obtenidos = models.IntegerField(default=0)
    acerto_resultado = models.BooleanField(default=False)
    acerto_marcador = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('inscripcion', 'partido')
        verbose_name = 'Pronóstico'
        verbose_name_plural = 'Pronósticos'

    def __str__(self):
        return f'{self.inscripcion} → {self.goles_local}-{self.goles_visitante}'

    @property
    def resultado_pronosticado(self):
        if self.goles_local > self.goles_visitante:
            return 'LOCAL'
        elif self.goles_local < self.goles_visitante:
            return 'VISITANTE'
        return 'EMPATE'

    def save(self, *args, **kwargs):
        if self.partido.cerrado_para_pronosticos and not self._state.adding:
            raise ValidationError('No se pueden modificar pronósticos después del inicio del partido.')
        if self.partido.cerrado_para_pronosticos and self._state.adding:
            raise ValidationError('No se pueden crear pronósticos después del inicio del partido.')
        super().save(*args, **kwargs)


class PronosticoCampeon(models.Model):
    inscripcion = models.OneToOneField(
        InscripcionPolla, on_delete=models.CASCADE, related_name='pronostico_campeon'
    )
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT, verbose_name='Equipo campeón')
    acerto = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pronóstico Campeón'
        verbose_name_plural = 'Pronósticos Campeón'

    def __str__(self):
        return f'{self.inscripcion} → {self.equipo.nombre}'


class ConfiguracionPolla(models.Model):
    nombre_torneo = models.CharField(max_length=100, default='Copa Mundial FIFA 2026')

    pts_resultado_grupos = models.IntegerField(default=1)
    pts_marcador_grupos = models.IntegerField(default=2)
    pts_resultado_eliminatoria = models.IntegerField(default=2)
    pts_marcador_eliminatoria = models.IntegerField(default=4)

    premio_campeon_sorteo = models.TextField(
        default='Camiseta original de la Selección Colombia'
    )
    premios_top5_grupos = models.TextField(
        default='Premios para el Top 5 de la fase de grupos (por definir)'
    )
    premios_top5_general = models.TextField(
        default='Premios mejorados para el Top 5 general (por definir)'
    )

    fecha_inicio_inscripciones = models.DateTimeField(null=True, blank=True)
    fecha_cierre_inscripciones = models.DateTimeField(null=True, blank=True)
    fecha_cierre_pronostico_campeon = models.DateTimeField(null=True, blank=True)

    mensaje_no_afiliado = models.TextField(
        default='¡Afíliate a FONDEINO y participa en la Polla Mundialista! '
                'Los nuevos asociados reciben DOBLE POLLA como beneficio de bienvenida.'
    )
    enlace_afiliacion = models.URLField(default='https://www.fondeino.com/')

    polla_cerrada = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Configuración de la Polla'
        verbose_name_plural = 'Configuración de la Polla'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.nombre_torneo

    @property
    def campeon_cerrado(self):
        if self.fecha_cierre_pronostico_campeon is None:
            return False
        return timezone.now() >= self.fecha_cierre_pronostico_campeon
