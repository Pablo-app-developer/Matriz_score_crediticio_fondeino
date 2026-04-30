import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone

from .models import EvaluacionCredito, Configuracion, Modalidad, PrestamoHistorico
from .forms import EvaluacionForm, ConfiguracionForm, ModalidadForm, DecisionComiteForm
from .scoring import evaluar_credito
from apps.nomina.models import Empleado


@login_required
def dashboard(request):
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    qs_mes = EvaluacionCredito.objects.filter(fecha_evaluacion__gte=inicio_mes)
    qs_total = EvaluacionCredito.objects.all()

    total_mes = qs_mes.count()
    aprobadas_mes = qs_mes.filter(decision__icontains='APROBAR').count()
    rechazadas_mes = qs_mes.filter(decision__icontains='RECHAZAR').count()
    revisar_mes = qs_mes.filter(decision__icontains='REVISAR').count()

    # Monto aprobado del mes: evaluaciones + históricos del mes
    monto_aprobado_mes_ev = qs_mes.filter(decision__icontains='APROBAR').aggregate(
        t=Sum('monto_solicitado'))['t'] or 0
    monto_aprobado_mes_hist = PrestamoHistorico.objects.filter(
        fecha__gte=inicio_mes.date()).aggregate(t=Sum('monto'))['t'] or 0
    monto_aprobado_mes = monto_aprobado_mes_ev + monto_aprobado_mes_hist

    # Score promedio solo de evaluaciones formales (excluye históricos importados)
    score_promedio_mes = qs_mes.aggregate(a=Avg('score_total'))['a'] or 0

    # Totales históricos: evaluaciones + todos los históricos importados
    total_historico = qs_total.count() + PrestamoHistorico.objects.count()
    monto_historico_ev = qs_total.filter(decision__icontains='APROBAR').aggregate(
        t=Sum('monto_solicitado'))['t'] or 0
    monto_historico_hist = PrestamoHistorico.objects.aggregate(t=Sum('monto'))['t'] or 0
    monto_historico = monto_historico_ev + monto_historico_hist

    # Distribución por clasificación (solo evaluaciones formales)
    por_clasificacion = (qs_total.values('clasificacion')
                         .annotate(n=Count('id')).order_by('-n'))

    # Últimas 8 evaluaciones
    recientes = qs_total.select_related('evaluado_por', 'modalidad').order_by('-fecha_evaluacion')[:8]

    return render(request, 'credito/dashboard.html', {
        'total_mes': total_mes,
        'aprobadas_mes': aprobadas_mes,
        'rechazadas_mes': rechazadas_mes,
        'revisar_mes': revisar_mes,
        'monto_aprobado_mes': monto_aprobado_mes,
        'score_promedio_mes': round(score_promedio_mes, 1),
        'total_historico': total_historico,
        'monto_historico': monto_historico,
        'por_clasificacion': list(por_clasificacion),
        'recientes': recientes,
        'mes_nombre': hoy.strftime('%B %Y'),
    })


@login_required
def evaluacion(request):
    """Formulario principal de evaluación de crédito."""
    form = EvaluacionForm(request.POST or None)
    resultado = None

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        cfg = Configuracion.get_config().as_dict()

        # Tasa mensual de la modalidad seleccionada
        modalidad = cd['modalidad']
        datos = {
            'salario_bruto': cd['salario_bruto'],
            'puntaje_datacredito': cd['puntaje_datacredito'],
            'antiguedad_meses': cd['antiguedad_meses'],
            'tipo_vinculacion': cd['tipo_vinculacion'],
            'tiene_credito_activo': cd['tiene_credito_activo'] == 'SI',
            'pct_capital_pagado': float(cd.get('pct_capital_pagado') or 0),
            'cuotas_otras_entidades': float(cd.get('cuotas_otras_entidades') or 0),
            'cuota_aporte': float(cd.get('cuota_aporte') or 0),
            'cuota_ahorro': float(cd.get('cuota_ahorro') or 0),
            'saldo_aportes': float(cd.get('saldo_aportes') or 0),
            'saldo_ahorros': float(cd.get('saldo_ahorros') or 0),
            'monto_solicitado': cd['monto_solicitado'],
            'n_cuotas': cd['n_cuotas'],
            'tasa_mensual': float(modalidad.tasa_mensual),
            'pd_base': float(modalidad.pd_base),
            'fecha_desembolso': cd['fecha_desembolso'],
        }

        resultado = evaluar_credito(datos, cfg)

        # Guardar en historial
        ev = EvaluacionCredito.objects.create(
            evaluado_por=request.user,
            tipo_documento=cd['tipo_documento'],
            cedula=cd['cedula'],
            nombre_completo=cd['nombre_completo'],
            area=cd.get('area', ''),
            cargo=cd.get('cargo', ''),
            tipo_vinculacion=cd['tipo_vinculacion'],
            antiguedad_meses=cd['antiguedad_meses'],
            salario_bruto=cd['salario_bruto'],
            puntaje_datacredito=cd['puntaje_datacredito'],
            tiene_credito_activo=(cd['tiene_credito_activo'] == 'SI'),
            pct_capital_pagado=float(cd.get('pct_capital_pagado') or 0),
            cuotas_otras_entidades=float(cd.get('cuotas_otras_entidades') or 0),
            cuota_aporte=float(cd.get('cuota_aporte') or 0),
            cuota_ahorro=float(cd.get('cuota_ahorro') or 0),
            saldo_aportes=float(cd.get('saldo_aportes') or 0),
            saldo_ahorros=float(cd.get('saldo_ahorros') or 0),
            modalidad=modalidad,
            fecha_desembolso=cd['fecha_desembolso'],
            monto_solicitado=cd['monto_solicitado'],
            n_cuotas=cd['n_cuotas'],
            motivo=cd.get('motivo', ''),
            salario_neto=resultado['salario_neto'],
            minimo_vital=resultado['minimo_vital'],
            total_cuotas=resultado['total_cuotas'],
            disponible_final=resultado['disponible_final'],
            estado_mv=resultado['estado_mv'],
            pct_endeudamiento=resultado['pct_endeudamiento'],
            score_datacredito=resultado['score_datacredito'],
            score_antiguedad=resultado['score_antiguedad'],
            score_vinculacion=resultado['score_vinculacion'],
            score_capacidad_pago=resultado['score_capacidad_pago'],
            score_garantias=resultado['score_garantias'],
            score_credito_activo=resultado['score_credito_activo'],
            score_total=resultado['score_total'],
            clasificacion=resultado['clasificacion'],
            decision=resultado['decision'],
        )
        return redirect('credito:detalle', pk=ev.pk)

    return render(request, 'credito/evaluacion.html', {'form': form})


@login_required
def buscar_empleado(request):
    """API AJAX: busca empleado por cédula en la BD de nómina."""
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'found': False})
    try:
        emp = Empleado.objects.get(cedula=cedula)
        return JsonResponse({
            'found': True,
            'nombre': emp.nombre,
            'area': emp.area,
            'cargo': emp.cargo,
            'tipo_vinculacion': emp.tipo_vinculacion,
            'antiguedad_meses': emp.antiguedad_meses,
            'salario_bruto': float(emp.salario),
        })
    except Empleado.DoesNotExist:
        return JsonResponse({'found': False})


@login_required
def buscar_empleado_nombre(request):
    """API AJAX: autocompletado de empleados por nombre o cédula."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    empleados = Empleado.objects.filter(
        Q(nombre__icontains=q) | Q(cedula__icontains=q)
    )[:10]
    results = [
        {
            'cedula': emp.cedula,
            'nombre': emp.nombre,
            'area': emp.area,
            'cargo': emp.cargo,
            'tipo_vinculacion': emp.tipo_vinculacion,
            'antiguedad_meses': emp.antiguedad_meses,
            'salario_bruto': float(emp.salario),
        }
        for emp in empleados
    ]
    return JsonResponse({'results': results})


@login_required
def get_modalidad_tasa(request):
    """API AJAX: devuelve tasa mensual de una modalidad."""
    pk = request.GET.get('pk')
    try:
        m = Modalidad.objects.get(pk=pk)
        return JsonResponse({'tasa_mensual': float(m.tasa_mensual), 'tasa_anual': float(m.tasa_mensual) * 12})
    except Modalidad.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


@login_required
def evaluacion_pdf(request, pk):
    """Página de impresión / exportación PDF de una evaluación."""
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    from .scoring import generar_plan_pagos, calcular_seguro
    from django.utils.timezone import localdate
    seguro = calcular_seguro(float(ev.monto_solicitado))
    plan = generar_plan_pagos(
        float(ev.monto_solicitado),
        float(ev.modalidad.tasa_mensual),
        ev.n_cuotas,
        ev.fecha_desembolso,
        seguro,
    )
    return render(request, 'credito/evaluacion_pdf.html', {
        'ev': ev,
        'plan': plan,
        'hoy': localdate().strftime('%d/%m/%Y'),
    })


@login_required
def detalle(request, pk):
    """Vista de resultado / detalle de una evaluación."""
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    form_comite = DecisionComiteForm(request.POST or None, instance=ev)
    if request.method == 'POST' and request.user.es_admin and form_comite.is_valid():
        form_comite.save()
        messages.success(request, 'Decisión del comité registrada.')
        return redirect('credito:detalle', pk=pk)

    # Regenerar plan de pagos para mostrar
    from .scoring import generar_plan_pagos, calcular_seguro, calcular_pmt
    monto = float(ev.monto_solicitado)
    tasa = float(ev.modalidad.tasa_mensual)
    seguro = calcular_seguro(monto)
    cuota_nueva = calcular_pmt(monto, tasa, ev.n_cuotas) + seguro
    plan = generar_plan_pagos(monto, tasa, ev.n_cuotas, ev.fecha_desembolso, seguro)

    return render(request, 'credito/detalle.html', {
        'ev': ev,
        'plan': plan,
        'form_comite': form_comite,
        'seguro': seguro,
        'cuota_nueva': cuota_nueva,
    })


@login_required
def historico(request):
    """Lista unificada: evaluaciones formales + préstamos históricos importados."""
    q = request.GET.get('q', '').strip()
    decision = request.GET.get('decision', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    # ── Evaluaciones formales ──────────────────────────────────────────────
    qs_ev = EvaluacionCredito.objects.select_related('evaluado_por', 'modalidad')
    if q:
        qs_ev = qs_ev.filter(Q(cedula__icontains=q) | Q(nombre_completo__icontains=q))
    if decision:
        qs_ev = qs_ev.filter(decision__icontains=decision)
    if fecha_desde:
        qs_ev = qs_ev.filter(fecha_evaluacion__date__gte=fecha_desde)
    if fecha_hasta:
        qs_ev = qs_ev.filter(fecha_evaluacion__date__lte=fecha_hasta)

    filas = []
    for ev in qs_ev:
        filas.append({
            'fecha': ev.fecha_evaluacion.date(),
            'cedula': ev.cedula,
            'nombre_completo': ev.nombre_completo,
            'modalidad': ev.modalidad.nombre,
            'proceso': ev.area,
            'monto': ev.monto_solicitado,
            'score': ev.score_total,
            'clasificacion': ev.clasificacion,
            'clasificacion_color': ev.clasificacion_color,
            'decision': ev.decision,
            'decision_color': ev.decision_color,
            'usuario': ev.evaluado_por.get_full_name() or ev.evaluado_por.username,
            'pk': ev.pk,
            'es_historico': False,
        })

    # ── Préstamos históricos importados (solo si no se filtra por RECHAZAR/REVISAR) ──
    incluir_historicos = not decision or 'APROBAR' in decision.upper()
    if incluir_historicos:
        qs_hist = PrestamoHistorico.objects.all()
        if q:
            qs_hist = qs_hist.filter(Q(cedula__icontains=q) | Q(nombre_completo__icontains=q))
        if fecha_desde:
            qs_hist = qs_hist.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs_hist = qs_hist.filter(fecha__lte=fecha_hasta)

        for p in qs_hist:
            filas.append({
                'fecha': p.fecha,
                'cedula': p.cedula,
                'nombre_completo': p.nombre_completo,
                'modalidad': p.concepto_prestamo,
                'proceso': p.proceso,
                'monto': p.monto,
                'score': None,
                'clasificacion': None,
                'clasificacion_color': None,
                'decision': 'APROBADO',
                'decision_color': 'success',
                'usuario': 'Administrador',
                'pk': None,
                'es_historico': True,
            })

    # Ordenar por fecha descendente y limitar
    filas.sort(key=lambda x: x['fecha'], reverse=True)

    return render(request, 'credito/historico.html', {
        'filas': filas[:300],
        'q': q,
        'decision': decision,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })


# ─────────────────────────────────────────────
# ADMIN: Configuración
# ─────────────────────────────────────────────

@login_required
def configuracion(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    cfg = Configuracion.get_config()
    form = ConfiguracionForm(request.POST or None, instance=cfg)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.actualizado_por = request.user
        obj.save()
        messages.success(request, 'Configuración guardada.')
        return redirect('credito:configuracion')
    return render(request, 'admin_extra/configuracion.html', {'form': form})


@login_required
def modalidades_lista(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    modalidades = Modalidad.objects.all()
    return render(request, 'admin_extra/modalidades.html', {'modalidades': modalidades})


@login_required
def modalidad_crear(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    form = ModalidadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Modalidad creada.')
        return redirect('credito:modalidades')
    return render(request, 'admin_extra/modalidad_form.html', {'form': form, 'titulo': 'Nueva Modalidad'})


@login_required
def modalidad_editar(request, pk):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    m = get_object_or_404(Modalidad, pk=pk)
    form = ModalidadForm(request.POST or None, instance=m)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Modalidad actualizada.')
        return redirect('credito:modalidades')
    return render(request, 'admin_extra/modalidad_form.html', {'form': form, 'titulo': 'Editar Modalidad', 'm': m})


# ─────────────────────────────────────────────
# Editar / Eliminar evaluaciones
# ─────────────────────────────────────────────

def _puede_modificar(user, ev):
    """Admin puede modificar cualquiera; comité solo las propias."""
    return user.es_admin or ev.evaluado_por == user


@login_required
def evaluacion_editar(request, pk):
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    if not _puede_modificar(request.user, ev):
        return HttpResponseForbidden()

    form = EvaluacionForm(request.POST or None, initial={
        'tipo_documento': ev.tipo_documento,
        'cedula': ev.cedula,
        'nombre_completo': ev.nombre_completo,
        'area': ev.area,
        'cargo': ev.cargo,
        'tipo_vinculacion': ev.tipo_vinculacion,
        'antiguedad_meses': ev.antiguedad_meses,
        'salario_bruto': ev.salario_bruto,
        'puntaje_datacredito': ev.puntaje_datacredito,
        'tiene_credito_activo': 'SI' if ev.tiene_credito_activo else 'NO',
        'pct_capital_pagado': ev.pct_capital_pagado,
        'cuotas_otras_entidades': ev.cuotas_otras_entidades,
        'cuota_aporte': ev.cuota_aporte,
        'cuota_ahorro': ev.cuota_ahorro,
        'saldo_aportes': ev.saldo_aportes,
        'saldo_ahorros': ev.saldo_ahorros,
        'modalidad': ev.modalidad,
        'fecha_desembolso': ev.fecha_desembolso,
        'monto_solicitado': ev.monto_solicitado,
        'n_cuotas': ev.n_cuotas,
        'motivo': ev.motivo,
    })

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        cfg = Configuracion.get_config().as_dict()
        modalidad = cd['modalidad']

        datos = {
            'salario_bruto': cd['salario_bruto'],
            'puntaje_datacredito': cd['puntaje_datacredito'],
            'antiguedad_meses': cd['antiguedad_meses'],
            'tipo_vinculacion': cd['tipo_vinculacion'],
            'tiene_credito_activo': cd['tiene_credito_activo'] == 'SI',
            'pct_capital_pagado': float(cd.get('pct_capital_pagado') or 0),
            'cuotas_otras_entidades': float(cd.get('cuotas_otras_entidades') or 0),
            'cuota_aporte': float(cd.get('cuota_aporte') or 0),
            'cuota_ahorro': float(cd.get('cuota_ahorro') or 0),
            'saldo_aportes': float(cd.get('saldo_aportes') or 0),
            'saldo_ahorros': float(cd.get('saldo_ahorros') or 0),
            'monto_solicitado': cd['monto_solicitado'],
            'n_cuotas': cd['n_cuotas'],
            'tasa_mensual': float(modalidad.tasa_mensual),
            'pd_base': float(modalidad.pd_base),
            'fecha_desembolso': cd['fecha_desembolso'],
        }
        resultado = evaluar_credito(datos, cfg)

        # Actualizar todos los campos de la evaluación existente
        ev.tipo_documento = cd['tipo_documento']
        ev.cedula = cd['cedula']
        ev.nombre_completo = cd['nombre_completo']
        ev.area = cd.get('area', '')
        ev.cargo = cd.get('cargo', '')
        ev.tipo_vinculacion = cd['tipo_vinculacion']
        ev.antiguedad_meses = cd['antiguedad_meses']
        ev.salario_bruto = cd['salario_bruto']
        ev.puntaje_datacredito = cd['puntaje_datacredito']
        ev.tiene_credito_activo = (cd['tiene_credito_activo'] == 'SI')
        ev.pct_capital_pagado = float(cd.get('pct_capital_pagado') or 0)
        ev.cuotas_otras_entidades = float(cd.get('cuotas_otras_entidades') or 0)
        ev.cuota_aporte = float(cd.get('cuota_aporte') or 0)
        ev.cuota_ahorro = float(cd.get('cuota_ahorro') or 0)
        ev.saldo_aportes = float(cd.get('saldo_aportes') or 0)
        ev.saldo_ahorros = float(cd.get('saldo_ahorros') or 0)
        ev.modalidad = modalidad
        ev.fecha_desembolso = cd['fecha_desembolso']
        ev.monto_solicitado = cd['monto_solicitado']
        ev.n_cuotas = cd['n_cuotas']
        ev.motivo = cd.get('motivo', '')
        ev.salario_neto = resultado['salario_neto']
        ev.minimo_vital = resultado['minimo_vital']
        ev.total_cuotas = resultado['total_cuotas']
        ev.disponible_final = resultado['disponible_final']
        ev.estado_mv = resultado['estado_mv']
        ev.pct_endeudamiento = resultado['pct_endeudamiento']
        ev.score_datacredito = resultado['score_datacredito']
        ev.score_antiguedad = resultado['score_antiguedad']
        ev.score_vinculacion = resultado['score_vinculacion']
        ev.score_capacidad_pago = resultado['score_capacidad_pago']
        ev.score_garantias = resultado['score_garantias']
        ev.score_credito_activo = resultado['score_credito_activo']
        ev.score_total = resultado['score_total']
        ev.clasificacion = resultado['clasificacion']
        ev.decision = resultado['decision']
        ev.save()

        messages.success(request, 'Evaluación actualizada y recalculada correctamente.')
        return redirect('credito:detalle', pk=ev.pk)

    return render(request, 'credito/evaluacion_editar.html', {'form': form, 'ev': ev})


@login_required
def evaluacion_eliminar(request, pk):
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    if not _puede_modificar(request.user, ev):
        return HttpResponseForbidden()

    if request.method == 'POST':
        nombre = ev.nombre_completo
        ev.delete()
        messages.success(request, f'Evaluación de {nombre} eliminada.')
        return redirect('credito:historico')

    return render(request, 'credito/evaluacion_confirmar_eliminar.html', {'ev': ev})


# ─── Histórico de Préstamos Aprobados ────────────────────────────────────────

@login_required
def historico_aprobados(request):
    """Lista de préstamos aprobados cargados desde Excel."""
    qs = PrestamoHistorico.objects.all()

    q = request.GET.get('q', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    concepto = request.GET.get('concepto', '').strip()

    if q:
        qs = qs.filter(Q(cedula__icontains=q) | Q(nombre_completo__icontains=q))
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if concepto:
        qs = qs.filter(concepto_prestamo__icontains=concepto)

    total_registros = qs.count()
    total_monto = qs.aggregate(t=Sum('monto'))['t'] or 0
    conceptos = PrestamoHistorico.objects.values_list('concepto_prestamo', flat=True).distinct().order_by('concepto_prestamo')

    return render(request, 'credito/historico_aprobados.html', {
        'prestamos': qs,
        'q': q,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'concepto': concepto,
        'total_registros': total_registros,
        'total_monto': total_monto,
        'conceptos': conceptos,
    })


@login_required
def cargar_historico_aprobados(request):
    """Carga masiva de préstamos aprobados desde un archivo Excel."""
    if not request.user.es_admin:
        return HttpResponseForbidden()

    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        reemplazar = request.POST.get('reemplazar') == '1'

        if not archivo:
            messages.error(request, 'Debe seleccionar un archivo Excel.')
            return render(request, 'credito/cargar_historico.html')

        try:
            import pandas as pd
            from datetime import datetime as dt

            df = pd.read_excel(archivo, header=5)  # fila 6 = índice 5
            df.columns = [str(c).strip() for c in df.columns]

            # Limpiar sufijos _x0000_ que Excel agrega por bytes nulos
            def limpiar(val):
                if pd.isna(val):
                    return ''
                return str(val).replace('_x0000_', '').strip()

            def parse_fecha(val):
                if pd.isna(val):
                    return None
                if isinstance(val, dt):
                    return val.date()
                try:
                    return pd.to_datetime(val, dayfirst=True).date()
                except Exception:
                    return None

            if reemplazar:
                PrestamoHistorico.objects.all().delete()

            registros = []
            errores = 0
            for _, row in df.iterrows():
                fecha = parse_fecha(row.get('Fecha'))
                cedula = limpiar(row.get('Cédula') or row.get('Cedula') or row.get('C\u00e9dula'))
                monto_raw = row.get('Monto del Crédito') or row.get('Monto del Credito') or 0
                if not cedula or not fecha:
                    errores += 1
                    continue
                try:
                    monto = float(monto_raw) if not pd.isna(monto_raw) else 0
                except (TypeError, ValueError):
                    monto = 0

                registros.append(PrestamoHistorico(
                    fecha=fecha,
                    cedula=cedula,
                    nombre_completo=limpiar(row.get('Nombre Completo')),
                    cargo=limpiar(row.get('Cargo')),
                    proceso=limpiar(row.get('Proceso')),
                    concepto_prestamo=limpiar(row.get('Concepto de Prestamo') or row.get('Concepto de Préstamo')),
                    monto=monto,
                    cargado_por=request.user,
                ))

            PrestamoHistorico.objects.bulk_create(registros, batch_size=500)
            msg = f'{len(registros)} préstamos cargados exitosamente.'
            if errores:
                msg += f' ({errores} filas omitidas por datos incompletos)'
            messages.success(request, msg)
            return redirect('credito:aprobados')

        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {e}')

    return render(request, 'credito/cargar_historico.html')
