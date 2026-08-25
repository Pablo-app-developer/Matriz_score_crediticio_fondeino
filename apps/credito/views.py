import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from .models import EvaluacionCredito, Configuracion, Modalidad, PrestamoHistorico
from .forms import EvaluacionForm, ConfiguracionForm, ModalidadForm, DecisionComiteForm
from .scoring import evaluar_credito
from apps.nomina.models import Empleado


@login_required
def dashboard(request):
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    qs_mes = EvaluacionCredito.objects.filter(fecha_evaluacion__gte=inicio_mes, anulado=False)
    qs_total = EvaluacionCredito.objects.filter(anulado=False)

    total_mes = qs_mes.count()
    aprobadas_mes = qs_mes.filter(decision__icontains='APROBAR').count()
    rechazadas_mes = qs_mes.filter(decision__icontains='NO APROBADO').count()
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

    # ── Datos para gráficas ───────────────────────────────────────────────────

    # 1. Tendencia mensual — últimos 12 meses (evaluaciones plataforma + histórico Excel)
    hace_12_meses = hoy - timedelta(days=365)
    MESES_ES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

    ev_raw = (
        EvaluacionCredito.objects.filter(fecha_evaluacion__gte=hace_12_meses, anulado=False)
        .annotate(mes=TruncMonth('fecha_evaluacion'))
        .values('mes').annotate(n=Count('id')).order_by('mes')
    )
    hist_raw = (
        PrestamoHistorico.objects.filter(fecha__gte=hace_12_meses.date())
        .annotate(mes=TruncMonth('fecha'))
        .values('mes').annotate(n=Count('id')).order_by('mes')
    )
    ev_map   = {item['mes'].date().replace(day=1): item['n'] for item in ev_raw}
    hist_map = {item['mes'].replace(day=1): item['n'] for item in hist_raw}

    tendencia_labels, tendencia_ev, tendencia_hist = [], [], []
    cursor = hace_12_meses.date().replace(day=1)
    while cursor <= hoy.date().replace(day=1):
        tendencia_labels.append(f"{MESES_ES[cursor.month - 1]} {cursor.year}")
        tendencia_ev.append(ev_map.get(cursor, 0))
        tendencia_hist.append(hist_map.get(cursor, 0))
        cursor = cursor.replace(month=cursor.month + 1) if cursor.month < 12 \
            else cursor.replace(year=cursor.year + 1, month=1)

    # 2. Por área — todo el histórico de la plataforma
    tipos_raw = (
        qs_total.values('area')
        .annotate(n=Count('id'))
        .order_by('-n')
    )
    tipos_labels   = [t['area'] or 'Sin especificar' for t in tipos_raw]
    tipos_cantidad = [t['n'] for t in tipos_raw]

    # 3. Distribución por decisión — todo el histórico de la plataforma
    decision_data = [
        qs_total.filter(decision__icontains='APROBAR').count(),
        qs_total.filter(decision__icontains='REVISAR').count(),
        qs_total.filter(decision__icontains='NO APROBADO').count(),
    ]

    # 4. Créditos por modalidad — todo el histórico de la plataforma
    score_modalidad_raw = (
        qs_total.values('modalidad__nombre')
        .annotate(n=Count('id'))
        .order_by('-n')
    )
    score_modal_labels = [s['modalidad__nombre'] for s in score_modalidad_raw]
    score_modal_data   = [s['n'] for s in score_modalidad_raw]

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
        # Gráficas
        'chart_tendencia_labels':   json.dumps(tendencia_labels),
        'chart_tendencia_ev':       json.dumps(tendencia_ev),
        'chart_tendencia_hist':     json.dumps(tendencia_hist),
        'chart_tipos_labels':       json.dumps(tipos_labels),
        'chart_tipos_cantidad':     json.dumps(tipos_cantidad),
        'chart_decision_data':      json.dumps(decision_data),
        'chart_score_modal_labels': json.dumps(score_modal_labels),
        'chart_score_modal_data':   json.dumps(score_modal_data),
        'total_plataforma':         qs_total.count(),
    })


def _parsear_otras_obligaciones(post):
    """Extrae las filas dinámicas de otras obligaciones del POST.
    Retorna (lista, total) donde lista = [{entidad, tipo, cuota}, ...]"""
    lista = []
    total = 0.0
    i = 1
    while f'cuota_otra_{i}' in post:
        try:
            cuota = float(post.get(f'cuota_otra_{i}') or 0)
        except ValueError:
            cuota = 0.0
        entidad = post.get(f'entidad_otra_{i}', '').strip()
        tipo = post.get(f'tipo_otra_{i}', '').strip()
        if cuota > 0 or entidad:
            lista.append({'entidad': entidad, 'tipo': tipo, 'cuota': cuota})
            total += cuota
        i += 1
    return lista, total


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

        # Parsear filas dinámicas de obligaciones con otras entidades
        otras_lista, total_otras = _parsear_otras_obligaciones(request.POST)
        datos['cuotas_otras_entidades'] = total_otras

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
            valor_inicial_credito_activo=float(cd.get('valor_inicial_credito_activo') or 0),
            valor_pagado_credito_activo=float(cd.get('valor_pagado_credito_activo') or 0),
            pct_capital_pagado=float(cd.get('pct_capital_pagado') or 0),
            cuotas_otras_entidades=total_otras,
            otras_obligaciones=otras_lista,
            cuota_aporte=float(cd.get('cuota_aporte') or 0),
            cuota_ahorro=float(cd.get('cuota_ahorro') or 0),
            saldo_aportes=float(cd.get('saldo_aportes') or 0),
            saldo_ahorros=float(cd.get('saldo_ahorros') or 0),
            modalidad=modalidad,
            fecha_desembolso=cd['fecha_desembolso'],
            monto_solicitado=cd['monto_solicitado'],
            n_cuotas=cd['n_cuotas'],
            tipo_credito=cd.get('tipo_credito', ''),
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
    from .scoring import generar_plan_pagos, calcular_seguro, calcular_pmt
    from django.utils.timezone import localdate
    monto_pdf = float(ev.monto_solicitado)
    tasa_pdf = float(ev.modalidad.tasa_mensual)
    seguro = calcular_seguro(monto_pdf)
    cuota_nueva = calcular_pmt(monto_pdf, tasa_pdf, ev.n_cuotas) + seguro
    plan = generar_plan_pagos(monto_pdf, tasa_pdf, ev.n_cuotas, ev.fecha_desembolso, seguro)
    total_garantias = float(ev.saldo_aportes) + float(ev.saldo_ahorros)
    return render(request, 'credito/evaluacion_pdf.html', {
        'ev': ev,
        'plan': plan,
        'cuota_nueva': cuota_nueva,
        'hoy': timezone.localtime().strftime('%d/%m/%Y %H:%M'),
        'total_garantias': total_garantias,
    })


@login_required
def evaluacion_pdf_lote(request):
    """PDF en lote: imprime varias evaluaciones por rango de # o por rango de fechas."""
    desde_pk   = request.GET.get('desde_pk', '').strip()
    hasta_pk   = request.GET.get('hasta_pk', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    pks = [p for p in request.GET.getlist('pks') if p.strip()]

    qs = EvaluacionCredito.objects.select_related('modalidad', 'evaluado_por').order_by('pk')

    if pks:
        try:
            qs = qs.filter(pk__in=[int(p) for p in pks])
        except ValueError:
            pass
    elif desde_pk and hasta_pk:
        try:
            qs = qs.filter(pk__gte=int(desde_pk), pk__lte=int(hasta_pk))
        except ValueError:
            pass
    if fecha_desde:
        qs = qs.filter(fecha_evaluacion__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_evaluacion__date__lte=fecha_hasta)

    from .scoring import generar_plan_pagos, calcular_seguro, calcular_pmt

    evaluaciones = []
    for ev in qs:
        monto  = float(ev.monto_solicitado)
        tasa   = float(ev.modalidad.tasa_mensual)
        seguro = calcular_seguro(monto)
        evaluaciones.append({
            'ev': ev,
            'cuota_nueva': calcular_pmt(monto, tasa, ev.n_cuotas) + seguro,
            'plan': generar_plan_pagos(monto, tasa, ev.n_cuotas, ev.fecha_desembolso, seguro),
            'total_garantias': float(ev.saldo_aportes) + float(ev.saldo_ahorros),
        })

    return render(request, 'credito/evaluacion_pdf_lote.html', {
        'evaluaciones': evaluaciones,
        'hoy': timezone.localtime().strftime('%d/%m/%Y %H:%M'),
        'total': len(evaluaciones),
    })


@login_required
def detalle(request, pk):
    """Vista de resultado / detalle de una evaluación."""
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    form_comite = DecisionComiteForm(request.POST or None, instance=ev)
    if request.method == 'POST':
        if ev.bloqueada:
            messages.error(request, 'Esta evaluación está bloqueada. El comité ya registró una decisión. Solicite al administrador que desbloquee la edición.')
            return redirect('credito:detalle', pk=pk)
        if form_comite.is_valid():
            obj = form_comite.save(commit=False)
            obj.fecha_decision_comite = timezone.now()
            obj.registrado_por_comite = request.user
            obj.edicion_desbloqueada = False
            obj.save()
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
        'puede_modificar': _puede_modificar(request.user, ev),
    })


@login_required
def historico(request):
    """Lista unificada: evaluaciones formales + préstamos históricos importados."""
    q = request.GET.get('q', '').strip()
    decision = request.GET.get('decision', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    # ── Evaluaciones formales ──────────────────────────────────────────────
    qs_ev = EvaluacionCredito.objects.select_related('evaluado_por', 'modalidad', 'anulado_por')
    # Admin ve anuladas (para trazabilidad de consecutivos); otros usuarios no las ven
    if not request.user.es_admin:
        qs_ev = qs_ev.filter(anulado=False)
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
            'n_cuotas': ev.n_cuotas,
            'score': ev.score_total,
            'clasificacion': ev.clasificacion,
            'clasificacion_color': ev.clasificacion_color,
            'decision': ev.decision,
            'decision_color': ev.decision_color,
            'decision_comite': ev.decision_comite,
            'decision_comite_color': ev.decision_comite_color,
            'usuario': ev.evaluado_por.get_full_name() or ev.evaluado_por.username,
            'pk': ev.pk,
            'es_historico': False,
            'anulado': ev.anulado,
            'motivo_anulacion': ev.motivo_anulacion,
            'anulado_por_nombre': (ev.anulado_por.get_full_name() or ev.anulado_por.username) if ev.anulado_por else '',
            'fecha_anulacion': ev.fecha_anulacion,
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
                'n_cuotas': None,
                'score': None,
                'clasificacion': None,
                'clasificacion_color': None,
                'decision': 'APROBADO',
                'decision_color': 'success',
                'decision_comite': '',
                'decision_comite_color': None,
                'usuario': 'Administrador',
                'pk': None,
                'es_historico': True,
                'anulado': False,
                'motivo_anulacion': '',
                'anulado_por_nombre': '',
                'fecha_anulacion': None,
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
    """Cualquier usuario autenticado puede modificar mientras no haya decisión del comité.
    Una vez tomada la decisión, solo el admin puede desbloquear."""
    return True


@login_required
def evaluacion_desbloquear(request, pk):
    """Solo el admin puede desbloquear la edición de una evaluación con decisión del comité."""
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    if not request.user.es_admin:
        return HttpResponseForbidden()
    if not ev.decision_comite:
        messages.info(request, 'Esta evaluación no tiene decisión del comité registrada.')
        return redirect('credito:detalle', pk=pk)
    ev.edicion_desbloqueada = True
    ev.save(update_fields=['edicion_desbloqueada'])
    messages.warning(request, f'Edición desbloqueada para "{ev.nombre_completo}". Se volverá a bloquear automáticamente al guardar cambios.')
    return redirect('credito:detalle', pk=pk)


@login_required
def evaluacion_editar(request, pk):
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    if not _puede_modificar(request.user, ev):
        return HttpResponseForbidden()
    if ev.bloqueada:
        messages.error(request, 'Esta evaluación está bloqueada. El comité ya registró una decisión. Solicite al administrador que desbloquee la edición.')
        return redirect('credito:detalle', pk=pk)

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
        'valor_inicial_credito_activo': ev.valor_inicial_credito_activo,
        'valor_pagado_credito_activo': ev.valor_pagado_credito_activo,
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
        'tipo_credito': ev.tipo_credito,
        'motivo': ev.motivo,
    })

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        cfg = Configuracion.get_config().as_dict()
        modalidad = cd['modalidad']

        otras_lista, total_otras = _parsear_otras_obligaciones(request.POST)
        datos = {
            'salario_bruto': cd['salario_bruto'],
            'puntaje_datacredito': cd['puntaje_datacredito'],
            'antiguedad_meses': cd['antiguedad_meses'],
            'tipo_vinculacion': cd['tipo_vinculacion'],
            'tiene_credito_activo': cd['tiene_credito_activo'] == 'SI',
            'pct_capital_pagado': float(cd.get('pct_capital_pagado') or 0),
            'cuotas_otras_entidades': total_otras,
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
        ev.valor_inicial_credito_activo = float(cd.get('valor_inicial_credito_activo') or 0)
        ev.valor_pagado_credito_activo = float(cd.get('valor_pagado_credito_activo') or 0)
        ev.pct_capital_pagado = float(cd.get('pct_capital_pagado') or 0)
        ev.cuotas_otras_entidades = total_otras
        ev.otras_obligaciones = otras_lista
        ev.cuota_aporte = float(cd.get('cuota_aporte') or 0)
        ev.cuota_ahorro = float(cd.get('cuota_ahorro') or 0)
        ev.saldo_aportes = float(cd.get('saldo_aportes') or 0)
        ev.saldo_ahorros = float(cd.get('saldo_ahorros') or 0)
        ev.modalidad = modalidad
        ev.fecha_desembolso = cd['fecha_desembolso']
        ev.monto_solicitado = cd['monto_solicitado']
        ev.n_cuotas = cd['n_cuotas']
        ev.tipo_credito = cd.get('tipo_credito', '')
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
        ev.edicion_desbloqueada = False
        ev.save()

        messages.success(request, 'Evaluación actualizada y recalculada correctamente.')
        return redirect('credito:detalle', pk=ev.pk)

    anterior = EvaluacionCredito.objects.filter(pk__lt=pk).order_by('-pk').values_list('pk', flat=True).first()
    siguiente = EvaluacionCredito.objects.filter(pk__gt=pk).order_by('pk').values_list('pk', flat=True).first()

    import json as _json
    return render(request, 'credito/evaluacion_editar.html', {
        'form': form,
        'ev': ev,
        'otras_obligaciones_json': _json.dumps(ev.otras_obligaciones or []),
        'pk_anterior': anterior,
        'pk_siguiente': siguiente,
    })


@login_required
def evaluacion_eliminar(request, pk):
    ev = get_object_or_404(EvaluacionCredito, pk=pk)
    if not _puede_modificar(request.user, ev):
        return HttpResponseForbidden()

    if request.method == 'POST':
        motivo = request.POST.get('motivo_anulacion', '').strip()
        if not motivo:
            messages.error(request, 'Debe indicar el motivo de anulación.')
            return render(request, 'credito/evaluacion_confirmar_eliminar.html', {'ev': ev})
        ev.anulado = True
        ev.fecha_anulacion = timezone.now()
        ev.anulado_por = request.user
        ev.motivo_anulacion = motivo
        ev.save(update_fields=['anulado', 'fecha_anulacion', 'anulado_por', 'motivo_anulacion'])
        messages.success(request, f'Evaluación #{ev.pk} de {ev.nombre_completo} anulada. El consecutivo queda registrado.')
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


# ─── Generador de Actas ───────────────────────────────────────────────────────

ROLES_COMITE = {
    'PabloR':      ('Pablo Andrés Ramírez Meneses',      'Presidente'),
    'AlejandraM':  ('Mayra Alejandra Montenegro Mateus', 'Secretaria'),
    'LilibethM':   ('Lilibeth Mora Toncel',              'Miembro'),
    'MayraO':      ('Mayra Alejandra Ortiz Pinilla',     'Miembro'),
    'FernandoS':   ('Luis Fernando Santos Serrano',      'Miembro'),
    'EileenV':     ('Eileen Yelipsa Vega Silva',         'Miembro'),
}


@login_required
def acta_form(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    from apps.accounts.models import Usuario
    miembros = []
    for uname, (nombre, cargo) in ROLES_COMITE.items():
        try:
            u = Usuario.objects.get(username=uname)
            uid = u.id
        except Usuario.DoesNotExist:
            uid = uname
        miembros.append({'id': uid, 'nombre': nombre, 'cargo': cargo})
    return render(request, 'credito/acta_form.html', {'miembros': miembros})


@login_required
def acta_imprimir(request):
    if not request.user.es_admin:
        return HttpResponseForbidden()
    if request.method != 'POST':
        return redirect('credito:acta_form')
    from apps.accounts.models import Usuario
    from django.utils.timezone import localdate
    from datetime import datetime as _dt

    no_acta       = request.POST.get('no_acta', '').strip()
    fecha_reunion = request.POST.get('fecha_reunion', '')
    fecha_desde   = request.POST.get('fecha_desde', '')
    fecha_hasta   = request.POST.get('fecha_hasta', '')
    asistentes    = set(request.POST.getlist('asistentes'))

    qs = EvaluacionCredito.objects.select_related('modalidad').order_by('nombre_completo')
    if fecha_desde:
        qs = qs.filter(fecha_evaluacion__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_evaluacion__date__lte=fecha_hasta)

    MESES = ['enero','febrero','marzo','abril','mayo','junio',
             'julio','agosto','septiembre','octubre','noviembre','diciembre']
    try:
        d = _dt.strptime(fecha_reunion, '%Y-%m-%d')
        fecha_fmt = f"{d.day} de {MESES[d.month-1]} de {d.year}"
    except Exception:
        fecha_fmt = fecha_reunion

    participantes = []
    for uname, (nombre, cargo) in ROLES_COMITE.items():
        try:
            u = Usuario.objects.get(username=uname)
            uid = str(u.id)
        except Usuario.DoesNotExist:
            uid = uname
        participantes.append({'nombre': nombre, 'cargo': cargo, 'asistio': uid in asistentes})

    return render(request, 'credito/acta_impresion.html', {
        'no_acta':      no_acta,
        'fecha_fmt':    fecha_fmt,
        'evaluaciones': qs,
        'participantes': participantes,
        'hoy':          localdate().strftime('%d/%m/%Y'),
        'presidente':   next((p for p in participantes if p['cargo'] == 'Presidente'), None),
        'secretaria':   next((p for p in participantes if p['cargo'] == 'Secretaria'), None),
    })
