from django import forms
from .models import Modalidad, Configuracion, EvaluacionCredito
from datetime import date


TIPO_DOCUMENTO_CHOICES = [('C.C.', 'Cédula de Ciudadanía'), ('C.E.', 'Cédula de Extranjería'), ('Pasaporte', 'Pasaporte')]
TIPO_VINCULACION_CHOICES = [('Indefinido', 'Contrato Indefinido'), ('A termino fijo', 'A término fijo'), ('Servicios', 'Prestación de servicios')]
SI_NO = [('NO', 'No'), ('SI', 'Sí')]

INPUT = 'form-control'
SELECT = 'form-select'


class EvaluacionForm(forms.Form):
    # Datos solicitante
    tipo_documento = forms.ChoiceField(choices=TIPO_DOCUMENTO_CHOICES,
                                       widget=forms.Select(attrs={'class': SELECT}))
    cedula = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={'class': INPUT, 'placeholder': 'Número de cédula', 'id': 'id_cedula'}))
    nombre_completo = forms.CharField(max_length=200, widget=forms.TextInput(
        attrs={'class': INPUT, 'id': 'id_nombre_completo'}))
    area = forms.CharField(max_length=100, required=False,
                           widget=forms.TextInput(attrs={'class': INPUT, 'id': 'id_area'}))
    cargo = forms.CharField(max_length=150, required=False,
                            widget=forms.TextInput(attrs={'class': INPUT, 'id': 'id_cargo'}))
    tipo_vinculacion = forms.ChoiceField(choices=TIPO_VINCULACION_CHOICES,
                                         widget=forms.Select(attrs={'class': SELECT, 'id': 'id_tipo_vinculacion'}))
    antiguedad_meses = forms.IntegerField(min_value=0, initial=0,
                                          widget=forms.NumberInput(attrs={'class': INPUT, 'id': 'id_antiguedad_meses'}))
    salario_bruto = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0,
                                       widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                       'id': 'id_salario_bruto'}))

    # Centrales de riesgo
    puntaje_datacredito = forms.IntegerField(min_value=150, max_value=950, initial=700,
                                             widget=forms.NumberInput(attrs={'class': INPUT,
                                                                             'id': 'id_puntaje_datacredito'}))
    tiene_credito_activo = forms.ChoiceField(choices=SI_NO,
                                             widget=forms.Select(attrs={'class': SELECT,
                                                                        'id': 'id_tiene_credito_activo'}))
    pct_capital_pagado = forms.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1,
                                            initial=0, required=False,
                                            widget=forms.NumberInput(
                                                attrs={'class': INPUT, 'step': 'any',
                                                       'placeholder': '0.00 a 1.00',
                                                       'id': 'id_pct_capital_pagado'}))
    cuotas_otras_entidades = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0,
                                                initial=0, required=False,
                                                widget=forms.NumberInput(attrs={'class': INPUT,
                                                                                'step': 'any',
                                                                                'id': 'id_cuotas_otras_entidades'}))

    # Descuentos FONDEINO
    cuota_aporte = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0, initial=0, required=False,
                                      widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                      'id': 'id_cuota_aporte'}))
    cuota_ahorro = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0, initial=0, required=False,
                                      widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                      'id': 'id_cuota_ahorro'}))

    # Garantías acumuladas
    saldo_aportes = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0, initial=0, required=False,
                                       widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                       'id': 'id_saldo_aportes'}))
    saldo_ahorros = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0, initial=0, required=False,
                                       widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                       'id': 'id_saldo_ahorros'}))

    # Condiciones del crédito
    modalidad = forms.ModelChoiceField(queryset=Modalidad.objects.filter(activa=True),
                                       widget=forms.Select(attrs={'class': SELECT, 'id': 'id_modalidad'}))
    fecha_desembolso = forms.DateField(initial=date.today,
                                       widget=forms.DateInput(attrs={'class': INPUT, 'type': 'date',
                                                                     'id': 'id_fecha_desembolso'}))
    monto_solicitado = forms.DecimalField(max_digits=14, decimal_places=2, min_value=1,
                                          widget=forms.NumberInput(attrs={'class': INPUT, 'step': 'any',
                                                                          'id': 'id_monto_solicitado'}))
    n_cuotas = forms.IntegerField(min_value=1, max_value=48, initial=12,
                                  widget=forms.NumberInput(attrs={'class': INPUT, 'id': 'id_n_cuotas'}))
    motivo = forms.CharField(max_length=200, required=False,
                             widget=forms.TextInput(attrs={'class': INPUT}))

    def clean(self):
        cd = super().clean()
        cd.setdefault('cuotas_otras_entidades', 0)
        cd.setdefault('cuota_aporte', 0)
        cd.setdefault('cuota_ahorro', 0)
        cd.setdefault('saldo_aportes', 0)
        cd.setdefault('saldo_ahorros', 0)
        cd.setdefault('pct_capital_pagado', 0)
        return cd


class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        exclude = ['fecha_actualizacion', 'actualizado_por']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ModalidadForm(forms.ModelForm):
    class Meta:
        model = Modalidad
        fields = ['nombre', 'tasa_mensual', 'pd_base', 'activa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['activa'].widget.attrs['class'] = 'form-check-input'


class DecisionComiteForm(forms.ModelForm):
    class Meta:
        model = EvaluacionCredito
        fields = ['decision_comite', 'observaciones']
        widgets = {
            'decision_comite': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
