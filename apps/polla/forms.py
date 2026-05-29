from django import forms
from .models import Afiliado, Pronostico, PronosticoCampeon, Equipo


def _iso2_to_flag(iso2):
    """Convierte código ISO2 a emoji de bandera (Regional Indicator letters)."""
    if not iso2:
        return ''
    # Subdivisiones como gb-eng, gb-sct — usar bandera negra genérica
    if '-' in iso2:
        return '🏴'
    try:
        return ''.join(chr(0x1F1E6 + ord(c.upper()) - ord('A')) for c in iso2[:2])
    except Exception:
        return ''


class EquipoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        flag = _iso2_to_flag(obj.iso2)
        return f'{flag} {obj.nombre}' if flag else obj.nombre


class RegistroPollaForm(forms.Form):
    cedula = forms.CharField(
        max_length=20,
        label='Número de cédula',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: 1098765432',
            'autofocus': True,
        }),
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Crea una contraseña',
        }),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Repite la contraseña',
        }),
    )

    def clean_password1(self):
        pwd = self.cleaned_data.get('password1')
        if pwd and len(pwd) < 4:
            raise forms.ValidationError('La contraseña debe tener al menos 4 caracteres.')
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned


class ActivarCuentaForm(forms.Form):
    cedula = forms.CharField(
        max_length=20,
        label='Número de cédula',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: 1098765432',
            'autofocus': True,
        }),
    )
    acepto_reglamento = forms.BooleanField(
        label='He leído y acepto el reglamento de la Polla Mundialista FONDEINO 2026.',
        error_messages={'required': 'Debes aceptar el reglamento para participar.'},
    )


class PronosticoForm(forms.ModelForm):
    class Meta:
        model = Pronostico
        fields = ['goles_local', 'goles_visitante']
        widgets = {
            'goles_local': forms.NumberInput(attrs={
                'class': 'form-control text-center fw-bold',
                'min': 0, 'max': 20, 'style': 'width:70px',
            }),
            'goles_visitante': forms.NumberInput(attrs={
                'class': 'form-control text-center fw-bold',
                'min': 0, 'max': 20, 'style': 'width:70px',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        gl = cleaned.get('goles_local')
        gv = cleaned.get('goles_visitante')
        if gl is not None and gl < 0:
            raise forms.ValidationError('Los goles no pueden ser negativos.')
        if gv is not None and gv < 0:
            raise forms.ValidationError('Los goles no pueden ser negativos.')
        return cleaned


class CampeonForm(forms.ModelForm):
    equipo = EquipoChoiceField(
        queryset=Equipo.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label='Selecciona el campeón del Mundial',
        empty_label='— Selecciona un equipo —',
    )

    class Meta:
        model = PronosticoCampeon
        fields = ['equipo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Partido
        ids = set()
        for lid, vid in Partido.objects.filter(fase='GRUPOS').values_list('equipo_local_id', 'equipo_visitante_id'):
            ids.add(lid)
            ids.add(vid)
        self.fields['equipo'].queryset = Equipo.objects.filter(pk__in=ids).order_by('grupo', 'nombre')


class CargarAfiliadosForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        help_text='Columnas requeridas: cedula, nombre_completo. Opcionales: correo, telefono, area. Máximo 5 MB.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
    )

    def clean_archivo(self):
        f = self.cleaned_data['archivo']
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError('El archivo supera el límite de 5 MB.')
        ext = f.name.rsplit('.', 1)[-1].lower()
        if ext not in ('xlsx', 'xls'):
            raise forms.ValidationError('Solo se permiten archivos .xlsx o .xls.')
        return f


class AfiliadoManualForm(forms.ModelForm):
    class Meta:
        model = Afiliado
        fields = ['cedula', 'nombre_completo', 'correo', 'telefono', 'area', 'activo']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1098765432'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez López'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3167522664'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Contabilidad'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'cedula': 'Identificador único del afiliado. No se puede cambiar después.',
        }


class ConfiguracionPollaForm(forms.ModelForm):
    class Meta:
        from .models import ConfiguracionPolla
        model = ConfiguracionPolla
        fields = [
            'nombre_torneo',
            'pts_resultado_grupos', 'pts_marcador_grupos',
            'pts_resultado_eliminatoria', 'pts_marcador_eliminatoria',
            'minutos_cierre_pronosticos',
            'premios_top5_general', 'premio_campeon_sorteo', 'premios_top5_grupos',
            'fecha_cierre_pronostico_campeon',
            'mensaje_no_afiliado', 'enlace_afiliacion',
            'polla_cerrada',
        ]
        widgets = {
            'nombre_torneo': forms.TextInput(attrs={'class': 'form-control'}),
            'pts_resultado_grupos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'pts_marcador_grupos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'pts_resultado_eliminatoria': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'pts_marcador_eliminatoria': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minutos_cierre_pronosticos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 60}),
            'premios_top5_general': forms.TextInput(attrs={'class': 'form-control'}),
            'premio_campeon_sorteo': forms.TextInput(attrs={'class': 'form-control'}),
            'premios_top5_grupos': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_cierre_pronostico_campeon': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'mensaje_no_afiliado': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enlace_afiliacion': forms.URLInput(attrs={'class': 'form-control'}),
            'polla_cerrada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre_torneo': 'Nombre del torneo',
            'pts_resultado_grupos': 'Puntos por resultado (grupos)',
            'pts_marcador_grupos': 'Puntos adicionales por marcador exacto (grupos)',
            'pts_resultado_eliminatoria': 'Puntos por resultado (eliminatorias)',
            'pts_marcador_eliminatoria': 'Puntos adicionales por marcador exacto (eliminatorias)',
            'minutos_cierre_pronosticos': 'Minutos de cierre antes del partido',
            'premios_top5_general': 'Premio 1 — Campeón general',
            'premio_campeon_sorteo': 'Premio 2 — Acierto al campeón',
            'premios_top5_grupos': 'Premios 3-5 — Partidos Colombia (fase de grupos)',
            'fecha_cierre_pronostico_campeon': 'Cierre pronóstico de campeón',
            'mensaje_no_afiliado': 'Mensaje para no afiliados',
            'enlace_afiliacion': 'Enlace de afiliación',
            'polla_cerrada': 'Polla cerrada (bloquea toda participación)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.fecha_cierre_pronostico_campeon:
            self.initial['fecha_cierre_pronostico_campeon'] = (
                self.instance.fecha_cierre_pronostico_campeon.strftime('%Y-%m-%dT%H:%M')
            )


class PartidoEditarForm(forms.ModelForm):
    class Meta:
        from .models import Partido
        model = Partido
        fields = ['fecha_hora', 'estadio', 'ciudad']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'estadio': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha_hora': 'Fecha y hora (hora Colombia UTC-5)',
            'estadio': 'Estadio',
            'ciudad': 'Ciudad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.fecha_hora:
            from django.utils import timezone
            import pytz
            bogota = pytz.timezone('America/Bogota')
            local_dt = self.instance.fecha_hora.astimezone(bogota)
            self.initial['fecha_hora'] = local_dt.strftime('%Y-%m-%dT%H:%M')


class ResultadoPartidoForm(forms.Form):
    goles_local = forms.IntegerField(
        min_value=0, max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm text-center',
            'min': 0, 'max': 20, 'style': 'width:65px',
        }),
    )
    goles_visitante = forms.IntegerField(
        min_value=0, max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm text-center',
            'min': 0, 'max': 20, 'style': 'width:65px',
        }),
    )
    finalizado = forms.BooleanField(
        required=False,
        label='Marcar como finalizado',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
