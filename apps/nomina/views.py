import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import CargaNomina, Empleado
from .forms import CargaNominaForm

# Mapeo de columnas del Excel de nómina a campos del modelo
# Basado en la estructura: Empleado, Nombre del empleado, Ndc, Descripcion estado,
# Descripcion C.O., Descripcion ccosto (area), Descripcion proyecto, Descripcion un,
# Fecha ingreso, Fecha retiro, Fecha contrato hasta, Descripcion del cargo, Salario
COL_CEDULA = 'Empleado'           # Col A
COL_NOMBRE = 'Nombre del empleado' # Col B
COL_ESTADO = 'Descripcion estado'  # Col D
COL_AREA   = 'Descripcion ccosto'  # Col F
COL_CARGO  = 'Descripcion del cargo'  # Col L
COL_FECHA_INGRESO = 'Fecha ingreso'    # Col I
COL_FECHA_RETIRO  = 'Fecha retiro'     # Col J
COL_FECHA_CONTRATO = 'Fecha contrato hasta'  # Col K
COL_SALARIO = 'Salario'            # Col M


def _parse_date(val):
    if pd.isna(val) or val == '' or val == 0:
        return None
    if isinstance(val, datetime):
        return val.date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


@login_required
def upload_nomina(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()

    form = CargaNominaForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            archivo = request.FILES['archivo']
            periodo = form.cleaned_data['periodo']

            df = pd.read_excel(archivo, dtype={COL_CEDULA: str})
            df.columns = [str(c).strip() for c in df.columns]

            # Validar columnas mínimas requeridas
            requeridas = [COL_CEDULA, COL_NOMBRE, COL_SALARIO]
            faltantes = [c for c in requeridas if c not in df.columns]
            if faltantes:
                messages.error(request, f'El archivo no tiene las columnas: {", ".join(faltantes)}. '
                               f'Columnas encontradas: {", ".join(df.columns[:8])}')
                return render(request, 'nomina/upload.html', {'form': form})

            # Desactivar cargas anteriores
            CargaNomina.objects.filter(activa=True).update(activa=False)
            # Borrar empleados de cargas viejas (mantenemos solo la última)
            Empleado.objects.all().delete()

            # No guardar el archivo en disco (Vercel tiene filesystem de solo lectura)
            # Solo registrar metadata de la carga
            carga = CargaNomina.objects.create(
                periodo=periodo,
                cargado_por=request.user,
            )

            empleados = []
            for _, row in df.iterrows():
                cedula = str(row.get(COL_CEDULA, '')).strip()
                if not cedula or cedula == 'nan':
                    continue
                # Salario
                sal = row.get(COL_SALARIO, 0)
                try:
                    sal = float(sal) if not pd.isna(sal) else 0
                except (TypeError, ValueError):
                    sal = 0

                empleados.append(Empleado(
                    carga=carga,
                    cedula=cedula,
                    nombre=str(row.get(COL_NOMBRE, '')).strip(),
                    estado=str(row.get(COL_ESTADO, '')).strip() if COL_ESTADO in df.columns else '',
                    area=str(row.get(COL_AREA, '')).strip() if COL_AREA in df.columns else '',
                    cargo=str(row.get(COL_CARGO, '')).strip() if COL_CARGO in df.columns else '',
                    fecha_ingreso=_parse_date(row.get(COL_FECHA_INGRESO)) if COL_FECHA_INGRESO in df.columns else None,
                    fecha_retiro=_parse_date(row.get(COL_FECHA_RETIRO)) if COL_FECHA_RETIRO in df.columns else None,
                    fecha_contrato_hasta=_parse_date(row.get(COL_FECHA_CONTRATO)) if COL_FECHA_CONTRATO in df.columns else None,
                    salario=sal,
                ))

            Empleado.objects.bulk_create(empleados, batch_size=500)
            carga.total_empleados = len(empleados)
            carga.save()

            messages.success(request, f'Nómina cargada exitosamente: {len(empleados)} empleados para el período {periodo}.')
            return redirect('nomina:lista')

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {e}')

    return render(request, 'nomina/upload.html', {'form': form})


@login_required
def lista_nomina(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    cargas = CargaNomina.objects.all()
    ultima = CargaNomina.objects.filter(activa=True).first()
    empleados_count = Empleado.objects.count()
    return render(request, 'nomina/lista.html', {
        'cargas': cargas,
        'ultima': ultima,
        'empleados_count': empleados_count,
    })
