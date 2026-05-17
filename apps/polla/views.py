import json
import random
from collections import defaultdict

import pandas as pd
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_polla_required, afiliado_activo
from .forms import (
    AfiliadoManualForm,
    AsignarDoblePolla,
    ActivarCuentaForm,
    CampeonForm,
    CargarAfiliadosForm,
    PronosticoForm,
    RegistroPollaForm,
    ResultadoPartidoForm,
)
from .models import (
    Afiliado,
    ConfiguracionPolla,
    Equipo,
    FASE_CHOICES,
    InscripcionPolla,
    Partido,
    PronosticoCampeon,
    Pronostico,
)
from .scoring import recalcular_todo
from apps.nomina.models import Empleado, CargaNomina


# ─────────────────────────────────────────────
# Utilidades internas
# ─────────────────────────────────────────────

def _get_afiliado(user):
    try:
        return user.afiliado
    except Exception:
        return None


# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

@login_required
def api_empleado_por_cedula(request):
    """Devuelve datos del empleado en la nómina activa más reciente dado su cédula."""
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'encontrado': False})
    carga_activa = CargaNomina.objects.filter(activa=True).order_by('-fecha_carga').first()
    if not carga_activa:
        return JsonResponse({'encontrado': False})
    try:
        emp = Empleado.objects.filter(carga=carga_activa, cedula=cedula).first()
        if not emp:
            return JsonResponse({'encontrado': False})
        return JsonResponse({
            'encontrado': True,
            'nombre': emp.nombre,
            'area': emp.area or '',
            'telefono': '',
        })
    except Exception:
        return JsonResponse({'encontrado': False})


def registro_polla(request):
    """Auto-registro para participantes de la polla que no tienen cuenta Django."""
    if request.user.is_authenticated:
        return redirect('polla:index')

    config = ConfiguracionPolla.get()
    form = RegistroPollaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cedula = form.cleaned_data['cedula'].strip()
        password = form.cleaned_data['password1']
        Usuario = get_user_model()

        try:
            afiliado = Afiliado.objects.get(cedula=cedula, activo=True)
        except Afiliado.DoesNotExist:
            messages.error(
                request,
                f'La cédula {cedula} no está registrada en la lista de afiliados de FONDEINO. '
                'Si crees que es un error, contacta al administrador.'
            )
            return render(request, 'polla/registro.html', {'form': form, 'config': config})

        if afiliado.user is not None:
            messages.warning(
                request,
                'Esa cédula ya tiene una cuenta registrada. '
                'Si olvidaste tu contraseña, contacta al administrador.'
            )
            return render(request, 'polla/registro.html', {'form': form, 'config': config})

        if Usuario.objects.filter(username=cedula).exists():
            messages.error(request, 'Ya existe una cuenta con ese número de cédula.')
            return render(request, 'polla/registro.html', {'form': form, 'config': config})

        user = Usuario.objects.create_user(
            username=cedula,
            password=password,
            first_name=afiliado.nombre_completo.split()[0] if afiliado.nombre_completo else '',
            last_name=' '.join(afiliado.nombre_completo.split()[1:]) if afiliado.nombre_completo else '',
            rol=Usuario.ROL_POLLA,
        )
        afiliado.user = user
        afiliado.save()
        InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=1)
        if afiliado.cantidad_pollas == 2:
            InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=2)

        auth_login(request, user)
        messages.success(request, f'¡Bienvenido, {afiliado.nombre_completo}! Tu cuenta esta lista.')
        return redirect('polla:index')

    return render(request, 'polla/registro.html', {'form': form, 'config': config})


def _procesar_excel_afiliados(df):
    """
    Procesa un DataFrame con datos de afiliados.
    Retorna dict con listas: creados, actualizados, nuevas_pollas, warnings, errores.
    """
    creados = []
    actualizados = []
    nuevas_pollas = []
    warnings = []
    errores = []

    col_map = {c.lower().strip(): c for c in df.columns}

    def get_col(row, *names):
        for n in names:
            if n in col_map:
                val = row.get(col_map[n], '')
                if pd.isna(val):
                    return ''
                return str(val).strip()
        return ''

    for idx, row in df.iterrows():
        fila = idx + 2

        cedula = get_col(row, 'cedula', 'cédula', 'documento', 'id')
        if not cedula:
            errores.append(f'Fila {fila}: cédula vacía, se omite.')
            continue

        nombre = get_col(row, 'nombre_completo', 'nombre', 'nombres')
        if not nombre:
            errores.append(f'Fila {fila}: nombre vacío para cédula {cedula}, se omite.')
            continue

        correo = get_col(row, 'correo', 'email', 'correo_electronico')
        telefono = get_col(row, 'telefono', 'teléfono', 'celular')
        area = get_col(row, 'area', 'área', 'departamento')

        raw_pollas = get_col(row, 'cantidad_pollas', 'pollas', 'num_pollas')
        try:
            cantidad_pollas = int(float(raw_pollas)) if raw_pollas else 1
            if cantidad_pollas not in (1, 2):
                cantidad_pollas = 1
        except (ValueError, TypeError):
            cantidad_pollas = 1

        motivo_raw = get_col(row, 'motivo_doble', 'motivo').upper()
        motivo_doble = motivo_raw if motivo_raw in ('NUEVO', 'AUMENTO') else None
        if cantidad_pollas == 2 and not motivo_doble:
            motivo_doble = 'NUEVO'

        try:
            afiliado = Afiliado.objects.get(cedula=cedula)

            # Actualizar datos básicos
            afiliado.nombre_completo = nombre
            if correo:
                afiliado.correo = correo
            if telefono:
                afiliado.telefono = telefono
            if area:
                afiliado.area = area

            # Lógica de pollas
            if cantidad_pollas == 2 and afiliado.cantidad_pollas == 1:
                afiliado.cantidad_pollas = 2
                afiliado.motivo_doble_polla = motivo_doble
                afiliado.save()
                InscripcionPolla.objects.get_or_create(
                    afiliado=afiliado, numero_polla=2
                )
                nuevas_pollas.append(f'{nombre} ({cedula}) — motivo: {motivo_doble}')
            elif cantidad_pollas == 1 and afiliado.cantidad_pollas == 2:
                warnings.append(
                    f'{nombre} ({cedula}): el Excel dice 1 polla pero ya tiene 2. '
                    'No se redujo. Cámbialo manualmente si es necesario.'
                )
                afiliado.save()
            else:
                afiliado.save()

            actualizados.append(f'{nombre} ({cedula})')

        except Afiliado.DoesNotExist:
            afiliado = Afiliado.objects.create(
                cedula=cedula,
                nombre_completo=nombre,
                correo=correo,
                telefono=telefono,
                area=area,
                cantidad_pollas=cantidad_pollas,
                motivo_doble_polla=motivo_doble if cantidad_pollas == 2 else None,
            )
            InscripcionPolla.objects.create(afiliado=afiliado, numero_polla=1)
            if cantidad_pollas == 2:
                InscripcionPolla.objects.create(afiliado=afiliado, numero_polla=2)
            creados.append(f'{nombre} ({cedula})')

        except Exception as e:
            errores.append(f'Fila {fila} ({cedula}): error inesperado — {e}')

    return {
        'creados': creados,
        'actualizados': actualizados,
        'nuevas_pollas': nuevas_pollas,
        'warnings': warnings,
        'errores': errores,
    }


# ─────────────────────────────────────────────
# Vistas públicas
# ─────────────────────────────────────────────

def ranking(request):
    tipo = request.GET.get('tipo', 'general')
    config = ConfiguracionPolla.get()

    base_qs = InscripcionPolla.objects.filter(activa=True).select_related(
        'afiliado'
    )

    if tipo == 'grupos':
        ranking_qs = base_qs.annotate(
            puntos_fase=Sum(
                'pronosticos__puntos_obtenidos',
                filter=Q(pronosticos__partido__fase='GRUPOS'),
            ),
            marcadores_fase=Count(
                'pronosticos',
                filter=Q(pronosticos__partido__fase='GRUPOS', pronosticos__acerto_marcador=True),
            ),
            resultados_fase=Count(
                'pronosticos',
                filter=Q(pronosticos__partido__fase='GRUPOS', pronosticos__acerto_resultado=True),
            ),
        ).order_by(
            '-puntos_fase', '-marcadores_fase', '-resultados_fase', 'afiliado__nombre_completo'
        )
        titulo = 'Ranking — Fase de Grupos'
    elif tipo == 'campeon':
        pronosticos_campeon = PronosticoCampeon.objects.select_related(
            'inscripcion__afiliado', 'equipo'
        ).order_by('equipo__nombre', 'inscripcion__afiliado__nombre_completo')
        return render(request, 'polla/ranking.html', {
            'tipo': tipo,
            'pronosticos_campeon': pronosticos_campeon,
            'config': config,
            'titulo': 'Pronósticos de Campeón',
        })
    else:
        ranking_qs = base_qs.order_by(
            '-puntos_totales', '-aciertos_marcador', '-aciertos_resultado', 'afiliado__nombre_completo'
        )
        titulo = 'Ranking General'

    # Paginación manual (50 por página)
    pagina = int(request.GET.get('pagina', 1))
    por_pagina = 50
    total = ranking_qs.count()
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    ranking_pagina = ranking_qs[inicio:fin]
    total_paginas = (total + por_pagina - 1) // por_pagina

    afiliado_user = _get_afiliado(request.user) if request.user.is_authenticated else None

    return render(request, 'polla/ranking.html', {
        'tipo': tipo,
        'ranking': ranking_pagina,
        'titulo': titulo,
        'config': config,
        'pagina': pagina,
        'total_paginas': total_paginas,
        'total': total,
        'offset': inicio,
        'afiliado_user': afiliado_user,
    })


def reglamento(request):
    config = ConfiguracionPolla.get()
    return render(request, 'polla/reglamento.html', {'config': config})


# ─────────────────────────────────────────────
# Flujo de activación / index
# ─────────────────────────────────────────────

@login_required
def index(request):
    afiliado = _get_afiliado(request.user)
    config = ConfiguracionPolla.get()

    if afiliado and afiliado.activo:
        # Dashboard
        inscripciones = afiliado.inscripciones.filter(activa=True).order_by('numero_polla')

        # Ranking actual de las inscripciones del usuario
        ranking_qs = InscripcionPolla.objects.filter(activa=True).order_by(
            '-puntos_totales', '-aciertos_marcador', '-aciertos_resultado', 'afiliado__nombre_completo'
        )
        posiciones = {}
        for pos, insc in enumerate(ranking_qs, 1):
            posiciones[insc.pk] = pos

        # Próximos partidos abiertos
        ahora = timezone.now()
        proximos = Partido.objects.filter(
            fecha_hora__gt=ahora, finalizado=False
        ).order_by('fecha_hora')[:3]

        # Últimos 3 partidos finalizados con pronósticos
        ultimos = Partido.objects.filter(finalizado=True).order_by('-fecha_hora')[:3]

        # Conteo de pronósticos completados
        partidos_abiertos = Partido.objects.filter(fecha_hora__gt=ahora).count()
        pronosticos_hechos = Pronostico.objects.filter(
            inscripcion__in=inscripciones,
            partido__fecha_hora__gt=ahora,
        ).values('partido').distinct().count()

        return render(request, 'polla/dashboard.html', {
            'afiliado': afiliado,
            'inscripciones': inscripciones,
            'posiciones': posiciones,
            'proximos': proximos,
            'ultimos': ultimos,
            'config': config,
            'partidos_abiertos': partidos_abiertos,
            'pronosticos_hechos': pronosticos_hechos,
        })
    else:
        # Landing / Activar
        return render(request, 'polla/landing.html', {
            'config': config,
            'ranking_preview': InscripcionPolla.objects.filter(activa=True).select_related(
                'afiliado'
            ).order_by('-puntos_totales')[:10],
        })


@login_required
def activar_cuenta(request):
    if _get_afiliado(request.user):
        return redirect('polla:index')

    config = ConfiguracionPolla.get()
    form = ActivarCuentaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cedula = form.cleaned_data['cedula'].strip()
        try:
            afiliado = Afiliado.objects.get(cedula=cedula)
            if afiliado.user is not None:
                if afiliado.user == request.user:
                    messages.info(request, 'Tu cuenta ya está activada.')
                    return redirect('polla:index')
                else:
                    messages.error(
                        request,
                        'Esa cédula ya está vinculada a otra cuenta. '
                        'Si crees que es un error, contacta al administrador.'
                    )
            else:
                afiliado.user = request.user
                afiliado.acepto_reglamento = True
                afiliado.save()
                # Crear inscripciones si no existen (por si acaso)
                InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=1)
                if afiliado.cantidad_pollas == 2:
                    InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=2)
                messages.success(
                    request,
                    f'¡Bienvenido, {afiliado.nombre_completo}! Tu cuenta de la Polla Mundialista está activa.'
                )
                return redirect('polla:index')
        except Afiliado.DoesNotExist:
            messages.error(
                request,
                f'La cédula {cedula} no está en la lista de afiliados de FONDEINO. '
                'Si crees que es un error, habla con el administrador del fondo.'
            )

    return render(request, 'polla/activar_cuenta.html', {'form': form, 'config': config})


# ─────────────────────────────────────────────
# Vistas de afiliado
# ─────────────────────────────────────────────

@afiliado_activo
def pronosticos(request):
    afiliado = request.user.afiliado
    config = ConfiguracionPolla.get()
    inscripciones = afiliado.inscripciones.filter(activa=True).order_by('numero_polla')

    polla_sel = int(request.GET.get('polla', 1))
    inscripcion_activa = next((i for i in inscripciones if i.numero_polla == polla_sel), inscripciones.first())

    # Partidos agrupados por fecha
    partidos = Partido.objects.select_related('equipo_local', 'equipo_visitante').order_by('fecha_hora')
    ahora = timezone.now()

    partidos_con_estado = []
    pronosticos_dict = {}
    if inscripcion_activa:
        pronosticos_dict = {
            p.partido_id: p
            for p in inscripcion_activa.pronosticos.select_related('partido').all()
        }

    partidos_por_fecha = defaultdict(list)
    for partido in partidos:
        pronostico = pronosticos_dict.get(partido.pk)
        partidos_por_fecha[partido.fecha_hora.date()].append({
            'partido': partido,
            'pronostico': pronostico,
            'cerrado': partido.cerrado_para_pronosticos,
        })

    partidos_por_fecha_ord = dict(sorted(partidos_por_fecha.items()))

    ORDEN_FASES = ['GRUPOS', 'TREINTA_DOS', 'OCTAVOS', 'CUARTOS', 'SEMIS', 'TERCERO', 'FINAL']
    FASE_LABEL = dict(FASE_CHOICES)
    _pend = {}
    for items in partidos_por_fecha_ord.values():
        for item in items:
            if not item['cerrado'] and not item['partido'].finalizado and not item['pronostico']:
                _pend[item['partido'].fase] = _pend.get(item['partido'].fase, 0) + 1
    pendientes_por_fase = {FASE_LABEL[f]: _pend[f] for f in ORDEN_FASES if f in _pend}
    pendientes = sum(pendientes_por_fase.values())

    return render(request, 'polla/pronosticos.html', {
        'afiliado': afiliado,
        'inscripciones': inscripciones,
        'inscripcion_activa': inscripcion_activa,
        'polla_sel': polla_sel,
        'partidos_por_fecha': partidos_por_fecha_ord,
        'config': config,
        'ahora': ahora,
        'pendientes': pendientes,
        'pendientes_por_fase': pendientes_por_fase,
    })


@login_required
def datos_partido_api(request, partido_id):
    from .api_service import get_datos_partido
    partido = get_object_or_404(Partido, pk=partido_id)
    datos = get_datos_partido(partido)
    if datos is None:
        return JsonResponse({'ok': False, 'error': 'Datos no disponibles'})
    return JsonResponse({'ok': True, 'datos': datos})


@require_POST
@afiliado_activo
def guardar_pronostico(request):
    try:
        data = json.loads(request.body)
        partido_id = int(data.get('partido_id'))
        polla_num = int(data.get('polla_num', 1))
        goles_local = int(data.get('goles_local'))
        goles_visitante = int(data.get('goles_visitante'))
    except (TypeError, ValueError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    afiliado = request.user.afiliado
    partido = get_object_or_404(Partido, pk=partido_id)

    if partido.cerrado_para_pronosticos:
        return JsonResponse({'ok': False, 'error': 'Este partido ya cerró para pronósticos.'})

    if goles_local < 0 or goles_visitante < 0:
        return JsonResponse({'ok': False, 'error': 'Los goles no pueden ser negativos.'})

    inscripcion = get_object_or_404(InscripcionPolla, afiliado=afiliado, numero_polla=polla_num)

    pronostico, created = Pronostico.objects.get_or_create(
        inscripcion=inscripcion,
        partido=partido,
        defaults={'goles_local': goles_local, 'goles_visitante': goles_visitante},
    )
    if not created:
        pronostico.goles_local = goles_local
        pronostico.goles_visitante = goles_visitante
        try:
            pronostico.save()
        except ValidationError as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({
        'ok': True,
        'mensaje': f'Pronóstico guardado: {goles_local}–{goles_visitante}',
    })


@afiliado_activo
def campeon(request):
    afiliado = request.user.afiliado
    config = ConfiguracionPolla.get()
    inscripciones = afiliado.inscripciones.filter(activa=True).order_by('numero_polla')
    polla_sel = int(request.GET.get('polla', 1))
    inscripcion = get_object_or_404(InscripcionPolla, afiliado=afiliado, numero_polla=polla_sel)

    try:
        pronostico_campeon = inscripcion.pronostico_campeon
    except PronosticoCampeon.DoesNotExist:
        pronostico_campeon = None

    cerrado = config.campeon_cerrado

    if request.method == 'POST':
        if cerrado:
            messages.error(request, 'El plazo para elegir al campeón ya cerró.')
            return redirect('polla:campeon')
        form = CampeonForm(request.POST, instance=pronostico_campeon)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.inscripcion = inscripcion
            obj.save()
            messages.success(request, f'¡Campeón guardado: {obj.equipo}!')
            return redirect('polla:campeon')
    else:
        form = CampeonForm(instance=pronostico_campeon)

    return render(request, 'polla/campeon.html', {
        'afiliado': afiliado,
        'inscripciones': inscripciones,
        'inscripcion': inscripcion,
        'polla_sel': polla_sel,
        'form': form,
        'pronostico_campeon': pronostico_campeon,
        'cerrado': cerrado,
        'config': config,
    })


@afiliado_activo
def mis_pronosticos(request):
    afiliado = request.user.afiliado
    inscripciones = afiliado.inscripciones.filter(activa=True).order_by('numero_polla')
    polla_sel = int(request.GET.get('polla', 1))
    inscripcion = get_object_or_404(InscripcionPolla, afiliado=afiliado, numero_polla=polla_sel)

    pronosticos_qs = inscripcion.pronosticos.select_related(
        'partido__equipo_local', 'partido__equipo_visitante'
    ).order_by('partido__fecha_hora')

    return render(request, 'polla/mis_pronosticos.html', {
        'afiliado': afiliado,
        'inscripciones': inscripciones,
        'inscripcion': inscripcion,
        'polla_sel': polla_sel,
        'pronosticos': pronosticos_qs,
    })


@login_required
def perfil_afiliado(request, afiliado_id):
    afiliado = get_object_or_404(Afiliado, pk=afiliado_id, activo=True)
    inscripciones = afiliado.inscripciones.filter(activa=True).order_by('numero_polla')
    polla_sel = int(request.GET.get('polla', 1))
    inscripcion = get_object_or_404(InscripcionPolla, afiliado=afiliado, numero_polla=polla_sel)

    # Solo mostrar partidos que ya cerraron (transparencia post-partido)
    pronosticos_qs = inscripcion.pronosticos.select_related(
        'partido__equipo_local', 'partido__equipo_visitante'
    ).filter(
        partido__cerrado_para_pronosticos=True
    ).order_by('partido__fecha_hora')

    return render(request, 'polla/perfil_afiliado.html', {
        'afiliado': afiliado,
        'inscripciones': inscripciones,
        'inscripcion': inscripcion,
        'polla_sel': polla_sel,
        'pronosticos': pronosticos_qs,
    })


# ─────────────────────────────────────────────
# Vistas de administrador
# ─────────────────────────────────────────────

@admin_polla_required
def admin_afiliados(request):
    q = request.GET.get('q', '').strip()
    afiliados = Afiliado.objects.prefetch_related('inscripciones').order_by('nombre_completo')
    if q:
        afiliados = afiliados.filter(
            Q(cedula__icontains=q) | Q(nombre_completo__icontains=q) | Q(area__icontains=q)
        )

    stats = {
        'total': Afiliado.objects.filter(activo=True).count(),
        'doble_polla': Afiliado.objects.filter(activo=True, cantidad_pollas=2).count(),
        'nuevos': Afiliado.objects.filter(activo=True, motivo_doble_polla='NUEVO').count(),
        'aumento': Afiliado.objects.filter(activo=True, motivo_doble_polla='AUMENTO').count(),
        'vinculados': Afiliado.objects.filter(activo=True, user__isnull=False).count(),
    }

    return render(request, 'polla/admin/gestion_afiliados.html', {
        'afiliados': afiliados,
        'stats': stats,
        'q': q,
    })


@admin_polla_required
def admin_afiliado_nuevo(request):
    form = AfiliadoManualForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        afiliado = form.save()
        InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=1)
        if afiliado.cantidad_pollas == 2:
            InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=2)
        messages.success(request, f'Afiliado {afiliado.nombre_completo} creado correctamente.')
        return redirect('polla:admin_afiliados')
    return render(request, 'polla/admin/afiliado_form.html', {
        'form': form,
        'titulo': 'Nuevo afiliado',
        'accion': 'Crear',
    })


@admin_polla_required
def admin_afiliado_editar(request, afiliado_id):
    afiliado = get_object_or_404(Afiliado, pk=afiliado_id)
    cantidad_pollas_anterior = afiliado.cantidad_pollas
    form = AfiliadoManualForm(request.POST or None, instance=afiliado)

    if request.method == 'POST' and form.is_valid():
        afiliado_guardado = form.save()
        nueva_cantidad = afiliado_guardado.cantidad_pollas

        if nueva_cantidad == 2 and cantidad_pollas_anterior == 1:
            InscripcionPolla.objects.get_or_create(afiliado=afiliado_guardado, numero_polla=2)
            messages.success(request, 'Afiliado actualizado. Se creó la Polla B.')
        elif nueva_cantidad == 1 and cantidad_pollas_anterior == 2:
            tiene_pronosticos_b = Pronostico.objects.filter(
                inscripcion__afiliado=afiliado_guardado, inscripcion__numero_polla=2
            ).exists()
            if tiene_pronosticos_b:
                messages.warning(
                    request,
                    'No se puede reducir a 1 polla porque ya hay pronósticos en la Polla B. '
                    'Desactiva la inscripción manualmente si es necesario.'
                )
                afiliado_guardado.cantidad_pollas = 2
                afiliado_guardado.save(update_fields=['cantidad_pollas'])
            else:
                InscripcionPolla.objects.filter(
                    afiliado=afiliado_guardado, numero_polla=2
                ).delete()
                messages.success(request, 'Afiliado actualizado. Se eliminó la Polla B (sin pronósticos).')
        else:
            messages.success(request, 'Afiliado actualizado correctamente.')
        return redirect('polla:admin_afiliados')

    return render(request, 'polla/admin/afiliado_form.html', {
        'form': form,
        'afiliado': afiliado,
        'titulo': f'Editar: {afiliado.nombre_completo}',
        'accion': 'Guardar cambios',
    })


@admin_polla_required
@require_POST
def admin_inscripcion_eliminar(request, inscripcion_id):
    inscripcion = get_object_or_404(InscripcionPolla, pk=inscripcion_id)
    afiliado = inscripcion.afiliado
    numero = inscripcion.numero_polla

    tiene_pronosticos = Pronostico.objects.filter(inscripcion=inscripcion).exists()
    if tiene_pronosticos:
        messages.warning(
            request,
            f'No se puede eliminar la Polla {"A" if numero == 1 else "B"} de {afiliado.nombre_completo} '
            'porque ya tiene pronósticos registrados.'
        )
        return redirect('polla:admin_afiliados')

    inscripcion.delete()
    # Actualizar cantidad_pollas si se eliminó la polla B
    if numero == 2:
        afiliado.cantidad_pollas = 1
        afiliado.motivo_doble_polla = None
        afiliado.save(update_fields=['cantidad_pollas', 'motivo_doble_polla'])
    messages.success(
        request,
        f'Polla {"A" if numero == 1 else "B"} de {afiliado.nombre_completo} eliminada.'
    )
    return redirect('polla:admin_afiliados')


@admin_polla_required
@require_POST
def admin_afiliado_eliminar(request, afiliado_id):
    afiliado = get_object_or_404(Afiliado, pk=afiliado_id)
    nombre = afiliado.nombre_completo
    # Desvincula el usuario Django si existe (no lo elimina, solo rompe el enlace)
    if afiliado.user:
        user = afiliado.user
        afiliado.user = None
        afiliado.save(update_fields=['user'])
        user.delete()
    afiliado.delete()
    messages.success(request, f'Afiliado "{nombre}" eliminado correctamente.')
    return redirect('polla:admin_afiliados')


@admin_polla_required
def admin_asignar_doble_polla(request, afiliado_id):
    afiliado = get_object_or_404(Afiliado, pk=afiliado_id, activo=True)
    if afiliado.cantidad_pollas == 2:
        messages.info(request, f'{afiliado.nombre_completo} ya tiene doble polla.')
        return redirect('polla:admin_afiliados')

    form = AsignarDoblePolla(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        motivo = form.cleaned_data['motivo']
        afiliado.cantidad_pollas = 2
        afiliado.motivo_doble_polla = motivo
        afiliado.save()
        InscripcionPolla.objects.get_or_create(afiliado=afiliado, numero_polla=2)
        messages.success(
            request,
            f'Doble polla asignada a {afiliado.nombre_completo} (motivo: {motivo}).'
        )
        return redirect('polla:admin_afiliados')

    return render(request, 'polla/admin/asignar_pollas.html', {
        'afiliado': afiliado,
        'form': form,
    })


@admin_polla_required
def admin_cargar_afiliados(request):
    resultado = None
    form = CargarAfiliadosForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        archivo = request.FILES['archivo']
        try:
            df = pd.read_excel(archivo)
            resultado = _procesar_excel_afiliados(df)
        except Exception as e:
            messages.error(request, f'Error al leer el archivo: {e}')

    return render(request, 'polla/admin/cargar_afiliados.html', {
        'form': form,
        'resultado': resultado,
    })


@admin_polla_required
def admin_cargar_resultados(request):
    config = ConfiguracionPolla.get()
    if config.polla_cerrada:
        messages.error(request, 'La polla está cerrada. No se pueden cargar más resultados.')
        return redirect('polla:admin_reporte')

    # Partidos sin finalizar, agrupados por fecha
    partidos = Partido.objects.filter(finalizado=False).select_related(
        'equipo_local', 'equipo_visitante'
    ).order_by('fecha_hora')

    if request.method == 'POST':
        actualizados = 0
        for partido in Partido.objects.select_related('equipo_local', 'equipo_visitante').all():
            key_local = f'goles_local_{partido.pk}'
            key_visitante = f'goles_visitante_{partido.pk}'
            key_fin = f'finalizado_{partido.pk}'

            if key_local in request.POST and key_visitante in request.POST:
                try:
                    gl = int(request.POST[key_local])
                    gv = int(request.POST[key_visitante])
                    fin = key_fin in request.POST
                    if 0 <= gl <= 20 and 0 <= gv <= 20:
                        partido.goles_local = gl
                        partido.goles_visitante = gv
                        partido.finalizado = fin
                        partido.save(update_fields=['goles_local', 'goles_visitante', 'finalizado'])
                        actualizados += 1
                except (ValueError, TypeError):
                    pass

        if actualizados:
            total = recalcular_todo(config)
            messages.success(
                request,
                f'Se actualizaron {actualizados} partido(s) y se recalcularon los puntos de {total} inscripciones.'
            )
        return redirect('polla:admin_cargar_resultados')

    # También mostrar partidos ya finalizados para corrección
    partidos_fin = Partido.objects.filter(finalizado=True).select_related(
        'equipo_local', 'equipo_visitante'
    ).order_by('-fecha_hora')[:20]

    return render(request, 'polla/admin/cargar_resultados.html', {
        'partidos': partidos,
        'partidos_fin': partidos_fin,
        'config': config,
    })


@admin_polla_required
def admin_reporte(request):
    config = ConfiguracionPolla.get()

    stats = {
        'afiliados': Afiliado.objects.filter(activo=True).count(),
        'doble_polla': Afiliado.objects.filter(activo=True, cantidad_pollas=2).count(),
        'vinculados': Afiliado.objects.filter(activo=True, user__isnull=False).count(),
        'inscripciones': InscripcionPolla.objects.filter(activa=True).count(),
        'pronosticos': Pronostico.objects.count(),
        'partidos_jugados': Partido.objects.filter(finalizado=True).count(),
        'partidos_total': Partido.objects.count(),
    }

    top5_general = InscripcionPolla.objects.filter(activa=True).select_related('afiliado').order_by(
        '-puntos_totales', '-aciertos_marcador', '-aciertos_resultado', 'afiliado__nombre_completo'
    )[:5]

    top5_grupos = InscripcionPolla.objects.filter(activa=True).select_related('afiliado').annotate(
        puntos_grupos=Sum(
            'pronosticos__puntos_obtenidos',
            filter=Q(pronosticos__partido__fase='GRUPOS')
        )
    ).order_by('-puntos_grupos', 'afiliado__nombre_completo')[:5]

    pronosticos_campeon = PronosticoCampeon.objects.select_related(
        'equipo', 'inscripcion__afiliado'
    ).order_by('equipo__nombre')

    return render(request, 'polla/admin/reporte.html', {
        'config': config,
        'stats': stats,
        'top5_general': top5_general,
        'top5_grupos': top5_grupos,
        'pronosticos_campeon': pronosticos_campeon,
    })


@admin_polla_required
def admin_cerrar_polla(request):
    config = ConfiguracionPolla.get()

    if request.method == 'POST' and request.POST.get('confirmar') == 'SI_CERRAR':
        if config.polla_cerrada:
            messages.error(request, 'La polla ya está cerrada.')
            return redirect('polla:admin_reporte')

        # Cálculo final
        recalcular_todo(config)

        # Sorteo del campeón
        ganadores_campeon = list(PronosticoCampeon.objects.filter(acerto=True).select_related(
            'inscripcion__afiliado', 'equipo'
        ))
        ganador_sorteo = None
        seed_sorteo = None
        if ganadores_campeon:
            seed_sorteo = random.randint(100000, 999999)
            rng = random.Random(seed_sorteo)
            ganador_sorteo = rng.choice(ganadores_campeon)

        # Cerrar
        config.polla_cerrada = True
        config.save()

        top5_general = InscripcionPolla.objects.filter(activa=True).select_related('afiliado').order_by(
            '-puntos_totales', '-aciertos_marcador', '-aciertos_resultado', 'afiliado__nombre_completo'
        )[:5]

        top5_grupos = InscripcionPolla.objects.filter(activa=True).select_related('afiliado').annotate(
            puntos_grupos=Sum('pronosticos__puntos_obtenidos', filter=Q(pronosticos__partido__fase='GRUPOS'))
        ).order_by('-puntos_grupos')[:5]

        messages.success(request, '¡La Polla Mundialista ha sido cerrada oficialmente!')

        return render(request, 'polla/admin/cierre_final.html', {
            'config': config,
            'top5_general': top5_general,
            'top5_grupos': top5_grupos,
            'ganadores_campeon': ganadores_campeon,
            'ganador_sorteo': ganador_sorteo,
            'seed_sorteo': seed_sorteo,
        })

    return render(request, 'polla/admin/cerrar_polla.html', {
        'config': config,
        'total_inscripciones': InscripcionPolla.objects.filter(activa=True).count(),
        'partidos_sin_resultado': Partido.objects.filter(finalizado=False).count(),
    })
