import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q

from .models import EvaluacionCredito, Configuracion, Modalidad
from .forms import EvaluacionForm, ConfiguracionForm, ModalidadForm, DecisionComiteForm
from .scoring import evaluar_credito
from apps.nomina.models import Empleado


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
def get_modalidad_tasa(request):
    """API AJAX: devuelve tasa mensual de una modalidad."""
    pk = request.GET.get('pk')
    try:
        m = Modalidad.objects.get(pk=pk)
        return JsonResponse({'tasa_mensual': float(m.tasa_mensual), 'tasa_anual': float(m.tasa_mensual) * 12})
    except Modalidad.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


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
    from .scoring import generar_plan_pagos, calcular_seguro
    seguro = calcular_seguro(float(ev.monto_solicitado))
    plan = generar_plan_pagos(
        float(ev.monto_solicitado),
        float(ev.modalidad.tasa_mensual),
        ev.n_cuotas,
        ev.fecha_desembolso,
        seguro,
    )

    return render(request, 'credito/detalle.html', {
        'ev': ev,
        'plan': plan,
        'form_comite': form_comite,
        'seguro': seguro,
    })


@login_required
def historico(request):
    """Lista de todas las evaluaciones."""
    qs = EvaluacionCredito.objects.select_related('evaluado_por', 'modalidad')

    # Filtros
    q = request.GET.get('q', '')
    decision = request.GET.get('decision', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if q:
        qs = qs.filter(Q(cedula__icontains=q) | Q(nombre_completo__icontains=q))
    if decision:
        qs = qs.filter(decision__icontains=decision)
    if fecha_desde:
        qs = qs.filter(fecha_evaluacion__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_evaluacion__date__lte=fecha_hasta)

    return render(request, 'credito/historico.html', {
        'evaluaciones': qs[:200],
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
