from django import forms


class CargaNominaForm(forms.Form):
    periodo = forms.CharField(
        max_length=20,
        label='Período',
        help_text='Formato: AAAA-MM (Ej: 2026-04)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2026-04'})
    )
    archivo = forms.FileField(
        label='Archivo Excel de Nómina (.xlsx)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    notas = forms.CharField(
        required=False,
        label='Notas',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
