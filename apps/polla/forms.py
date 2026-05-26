from django import forms
from .models import Afiliado, Pronostico, PronosticoCampeon, Equipo


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
    class Meta:
        model = PronosticoCampeon
        fields = ['equipo']
        widgets = {
            'equipo': forms.Select(attrs={'class': 'form-select form-select-lg'}),
        }
        labels = {'equipo': 'Selecciona el campeón del Mundial'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipo'].queryset = Equipo.objects.order_by('nombre')


class CargarAfiliadosForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel (.xlsx)',
        help_text='Columnas requeridas: cedula, nombre_completo. Opcionales: correo, telefono, area, cantidad_pollas, motivo_doble. Máximo 5 MB.',
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
        fields = ['cedula', 'nombre_completo', 'correo', 'telefono', 'area',
                  'cantidad_pollas', 'motivo_doble_polla', 'activo']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1098765432'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez López'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3167522664'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Contabilidad'}),
            'cantidad_pollas': forms.Select(attrs={'class': 'form-select'}),
            'motivo_doble_polla': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'cantidad_pollas': 'Nuevos asociados o quienes aumentaron aportes reciben 2 pollas.',
            'motivo_doble_polla': 'Solo obligatorio si cantidad de pollas es 2.',
            'cedula': 'Identificador único del afiliado. No se puede cambiar después.',
        }


class AsignarDoblePolla(forms.Form):
    MOTIVO_CHOICES = [('NUEVO', 'Nuevo asociado'), ('AUMENTO', 'Aumentó aportes')]
    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label='Motivo',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


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
