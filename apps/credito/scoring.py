"""
Motor de scoring crediticio - FONDEINO
Implementación Python de las fórmulas del Excel Plantilla_Fondeino_V4
"""
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import math


# ─────────────────────────────────────────────
# BLOQUE 1 – INGRESOS
# ─────────────────────────────────────────────

def calcular_salario_neto(salario_bruto: float) -> dict:
    salud = salario_bruto * 0.04
    pension = salario_bruto * 0.04
    neto = salario_bruto - salud - pension
    return {'salud': salud, 'pension': pension, 'neto': neto}


# ─────────────────────────────────────────────
# BLOQUE 2 – MÍNIMO VITAL
# ─────────────────────────────────────────────

def calcular_minimo_vital(salario_neto: float, porcentaje_mv: float = 0.5) -> float:
    return salario_neto * porcentaje_mv


# ─────────────────────────────────────────────
# BLOQUE 3 – CUOTA ESTIMADA (PMT)
# ─────────────────────────────────────────────

def calcular_pmt(monto: float, tasa_mensual: float, n_cuotas: int) -> float:
    """Equivalente a la función PMT de Excel."""
    if n_cuotas <= 0:
        return 0
    if tasa_mensual == 0:
        return monto / n_cuotas
    return monto * tasa_mensual / (1 - (1 + tasa_mensual) ** -n_cuotas)


def calcular_seguro(monto: float) -> float:
    """Seguro mensual = 0.25% del monto."""
    return monto * 0.0025


def calcular_obligaciones(cuotas_otras: float, cuota_aporte: float, cuota_ahorro: float,
                           monto: float, tasa_mensual: float, n_cuotas: int) -> dict:
    cuota_nueva = calcular_pmt(monto, tasa_mensual, n_cuotas) + calcular_seguro(monto)
    cuotas_fondeino = cuota_aporte + cuota_ahorro
    total = cuotas_otras + cuotas_fondeino + cuota_nueva
    return {
        'cuota_nueva_estimada': cuota_nueva,
        'cuotas_fondeino_actuales': cuotas_fondeino,
        'total_cuotas': total,
    }


# ─────────────────────────────────────────────
# BLOQUE 4 – VALIDACIÓN
# ─────────────────────────────────────────────

def calcular_validacion(salario_neto: float, minimo_vital: float, total_cuotas: float) -> dict:
    disponible = minimo_vital - total_cuotas
    cumple = disponible >= 0
    pct_endeudamiento = total_cuotas / salario_neto if salario_neto > 0 else 0

    if disponible < 0:
        estado = 'BLOQUEADO - CUOTA > 50% NETO'
    elif pct_endeudamiento > 0.5:
        estado = 'RIESGO ALTO (>50%)'
    else:
        estado = 'OK'

    return {
        'disponible_final': disponible,
        'cumple_minimo_vital': cumple,
        'pct_endeudamiento': pct_endeudamiento,
        'estado': estado,
    }


# ─────────────────────────────────────────────
# GARANTÍAS
# ─────────────────────────────────────────────

def calcular_cobertura_garantias(aportes: float, ahorros: float, monto: float) -> dict:
    total = aportes + ahorros
    cobertura = total / monto if monto > 0 else 0
    return {'total_garantias': total, 'pct_cobertura': cobertura}


# ─────────────────────────────────────────────
# SCORING CREDITICIO (6 factores)
# ─────────────────────────────────────────────

def score_datacredito(puntaje: int, cfg: dict) -> int:
    """
    cfg keys: s_dc_excelente, s_dc_bueno, s_dc_regular, s_dc_malo,
              t_dc_excelente (700), t_dc_bueno (500), t_dc_regular (300)
    """
    if puntaje >= cfg.get('t_dc_excelente', 700):
        return cfg.get('s_dc_excelente', 25)
    elif puntaje >= cfg.get('t_dc_bueno', 500):
        return cfg.get('s_dc_bueno', 15)
    elif puntaje >= cfg.get('t_dc_regular', 300):
        return cfg.get('s_dc_regular', 8)
    else:
        return cfg.get('s_dc_malo', 0)


def score_antiguedad(meses: int, cfg: dict) -> int:
    """
    cfg keys: s_ant_*, t_ant_* (thresholds: 24, 12, 6, 3 meses)
    """
    if meses >= cfg.get('t_ant_1', 24):
        return cfg.get('s_ant_1', 15)
    elif meses >= cfg.get('t_ant_2', 12):
        return cfg.get('s_ant_2', 12)
    elif meses >= cfg.get('t_ant_3', 6):
        return cfg.get('s_ant_3', 8)
    elif meses >= cfg.get('t_ant_4', 3):
        return cfg.get('s_ant_4', 4)
    else:
        return cfg.get('s_ant_5', 0)


def score_vinculacion(tipo: str, cfg: dict) -> int:
    """
    cfg keys: s_vinc_indefinido, s_vinc_fijo, s_vinc_servicios
    """
    t = tipo.lower()
    if 'indefinido' in t:
        return cfg.get('s_vinc_indefinido', 10)
    elif 'fijo' in t:
        return cfg.get('s_vinc_fijo', 7)
    else:
        return cfg.get('s_vinc_servicios', 4)


def score_capacidad_pago(disponible: float, pct_endeudamiento: float, cfg: dict) -> int:
    """
    cfg keys: s_cap_excelente, s_cap_bueno, s_cap_regular, s_cap_malo,
              t_cap_bueno (0.30), t_cap_regular (0.50)
    """
    if disponible < 0:
        return cfg.get('s_cap_bloqueado', 0)
    elif pct_endeudamiento > cfg.get('t_cap_regular', 0.50):
        return cfg.get('s_cap_malo', 5)
    elif pct_endeudamiento > cfg.get('t_cap_bueno', 0.30):
        return cfg.get('s_cap_regular', 15)
    else:
        return cfg.get('s_cap_excelente', 25)


def score_garantias(total_garantias: float, monto: float, cfg: dict) -> int:
    """
    cfg keys: s_gar_*, t_gar_* (thresholds: 1.0, 0.5, 0.25)
    """
    cobertura = total_garantias / monto if monto > 0 else 0
    if cobertura >= cfg.get('t_gar_alta', 1.0):
        return cfg.get('s_gar_alta', 15)
    elif cobertura >= cfg.get('t_gar_media', 0.5):
        return cfg.get('s_gar_media', 10)
    elif cobertura >= cfg.get('t_gar_baja', 0.25):
        return cfg.get('s_gar_baja', 5)
    else:
        return cfg.get('s_gar_nula', 0)


def score_credito_activo(tiene_credito: bool, pct_capital_pagado: float, cfg: dict) -> int:
    """
    cfg keys: s_hist_sin, s_hist_bueno, s_hist_malo, t_hist_bueno (0.30)
    """
    if not tiene_credito:
        return cfg.get('s_hist_sin', 10)
    elif pct_capital_pagado >= cfg.get('t_hist_bueno', 0.30):
        return cfg.get('s_hist_bueno', 7)
    else:
        return cfg.get('s_hist_malo', 3)


def clasificar_score(score: int, cfg: dict) -> str:
    """
    cfg keys: t_cls_excelente (80), t_cls_bueno (60), t_cls_regular (40)
    """
    if score >= cfg.get('t_cls_excelente', 80):
        return 'EXCELENTE'
    elif score >= cfg.get('t_cls_bueno', 60):
        return 'BUENO'
    elif score >= cfg.get('t_cls_regular', 40):
        return 'REGULAR'
    else:
        return 'ALTO RIESGO'


def calcular_decision(score: int, estado_mv: str, cfg: dict) -> str:
    if 'BLOQUEADO' in estado_mv:
        return 'RECHAZAR - CUOTA EXCEDE LÍMITE'
    elif score >= cfg.get('t_cls_bueno', 60) and estado_mv == 'OK':
        return 'APROBAR'
    elif score >= cfg.get('t_cls_regular', 40):
        return 'REVISAR / SOLICITAR CODEUDOR'
    else:
        return 'RECHAZAR'


# ─────────────────────────────────────────────
# MÉTRICAS DE RIESGO
# ─────────────────────────────────────────────

def calcular_metricas_riesgo(pd_base: float, score: int, total_garantias: float, monto: float) -> dict:
    pd_ajustada = pd_base * (1 + (100 - score) / 100)
    cobertura = total_garantias / monto if monto > 0 else 0
    if cobertura >= 1.0:
        lgd = 0.10
    elif cobertura >= 0.5:
        lgd = 0.20
    else:
        lgd = 0.45
    perdida_esperada = pd_ajustada * lgd * monto
    return {
        'pd_base': pd_base,
        'pd_ajustada': pd_ajustada,
        'lgd': lgd,
        'perdida_esperada': perdida_esperada,
    }


# ─────────────────────────────────────────────
# PLAN DE PAGOS (Amortización)
# ─────────────────────────────────────────────

def _days360(start: date, end: date) -> int:
    """Implementación de DAYS360 (método europeo simplificado)."""
    d1 = min(start.day, 30)
    d2 = min(end.day, 30)
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)


def _fin_de_mes(d: date) -> date:
    """Último día del mes de la fecha d."""
    if d.month == 12:
        return d.replace(day=31)
    return (d.replace(month=d.month + 1, day=1)) - relativedelta(days=1)


def generar_plan_pagos(monto: float, tasa_mensual: float, n_cuotas: int,
                       fecha_desembolso: date, seguro_mensual: float) -> list:
    """
    Genera el plan de pagos con lógica idéntica al Excel:
    - Primera cuota: fin del mes actual si desembolso <= día 15, si no fin del mes siguiente
    - Interés exacto usando DAYS360
    - Cuota fija PMT, última cuota cierra exactamente el saldo
    """
    cuota_fija = calcular_pmt(monto, tasa_mensual, n_cuotas)
    saldo = monto
    cuotas = []

    # Fecha primera cuota
    if fecha_desembolso.day <= 15:
        fecha_pago = _fin_de_mes(fecha_desembolso)
    else:
        proximo = fecha_desembolso.replace(day=1) + relativedelta(months=1)
        fecha_pago = _fin_de_mes(proximo)

    fecha_anterior = fecha_desembolso

    for i in range(1, n_cuotas + 1):
        dias = _days360(fecha_anterior, fecha_pago)
        interes = saldo * (tasa_mensual / 30) * dias

        if i == n_cuotas:
            capital = saldo  # cierra exacto
        else:
            capital = cuota_fija - interes

        saldo_final = max(saldo - capital, 0)
        cuota_total = interes + capital + seguro_mensual

        cuotas.append({
            'numero': i,
            'fecha_pago': fecha_pago,
            'dias': dias,
            'saldo_inicial': round(saldo, 2),
            'interes': round(interes, 2),
            'capital': round(capital, 2),
            'saldo_final': round(saldo_final, 2),
            'seguro': round(seguro_mensual, 2),
            'cuota_total': round(cuota_total, 2),
        })

        fecha_anterior = fecha_pago
        fecha_pago = _fin_de_mes(fecha_pago + relativedelta(months=1))
        saldo = saldo_final

    return cuotas


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL: evaluar crédito completo
# ─────────────────────────────────────────────

def evaluar_credito(datos: dict, cfg: dict) -> dict:
    """
    Recibe todos los datos del formulario y la configuración del sistema.
    Retorna un dict con todos los resultados calculados.
    """
    sb = float(datos['salario_bruto'])
    ingresos = calcular_salario_neto(sb)
    sn = ingresos['neto']

    pct_mv = float(cfg.get('porcentaje_minimo_vital', 0.5))
    mv = calcular_minimo_vital(sn, pct_mv)

    monto = float(datos['monto_solicitado'])
    n_cuotas = int(datos['n_cuotas'])
    tasa_mensual = float(datos['tasa_mensual'])
    seguro = calcular_seguro(monto)
    cuotas_otras = float(datos.get('cuotas_otras_entidades', 0))
    cuota_aporte = float(datos.get('cuota_aporte', 0))
    cuota_ahorro = float(datos.get('cuota_ahorro', 0))

    oblig = calcular_obligaciones(cuotas_otras, cuota_aporte, cuota_ahorro,
                                  monto, tasa_mensual, n_cuotas)

    validacion = calcular_validacion(sn, mv, oblig['total_cuotas'])

    aportes_ac = float(datos.get('saldo_aportes', 0))
    ahorros_ac = float(datos.get('saldo_ahorros', 0))
    garantias = calcular_cobertura_garantias(aportes_ac, ahorros_ac, monto)

    # Scores
    puntaje_dc = int(datos['puntaje_datacredito'])
    meses_ant = int(datos['antiguedad_meses'])
    tipo_vinc = datos['tipo_vinculacion']
    tiene_credito = datos.get('tiene_credito_activo', False)
    if isinstance(tiene_credito, str):
        tiene_credito = tiene_credito.upper() == 'SI'
    pct_capital = float(datos.get('pct_capital_pagado', 0))

    s_dc = score_datacredito(puntaje_dc, cfg)
    s_ant = score_antiguedad(meses_ant, cfg)
    s_vinc = score_vinculacion(tipo_vinc, cfg)
    s_cap = score_capacidad_pago(validacion['disponible_final'], validacion['pct_endeudamiento'], cfg)
    s_gar = score_garantias(garantias['total_garantias'], monto, cfg)
    s_hist = score_credito_activo(tiene_credito, pct_capital, cfg)

    score_total = s_dc + s_ant + s_vinc + s_cap + s_gar + s_hist
    clasificacion = clasificar_score(score_total, cfg)
    decision = calcular_decision(score_total, validacion['estado'], cfg)

    # Métricas de riesgo
    pd_base = float(datos.get('pd_base', 0.015))
    metricas = calcular_metricas_riesgo(pd_base, score_total, garantias['total_garantias'], monto)

    # Plan de pagos
    fecha_desembolso = datos.get('fecha_desembolso', date.today())
    if isinstance(fecha_desembolso, str):
        fecha_desembolso = date.fromisoformat(fecha_desembolso)

    plan = generar_plan_pagos(monto, tasa_mensual, n_cuotas, fecha_desembolso, seguro)

    return {
        # Ingresos
        'salario_bruto': sb,
        'descuento_salud': ingresos['salud'],
        'descuento_pension': ingresos['pension'],
        'salario_neto': sn,
        # Mínimo vital
        'porcentaje_mv': pct_mv,
        'minimo_vital': mv,
        # Obligaciones
        'cuotas_otras_entidades': cuotas_otras,
        'cuotas_fondeino_actuales': oblig['cuotas_fondeino_actuales'],
        'cuota_nueva_estimada': oblig['cuota_nueva_estimada'],
        'seguro_mensual': seguro,
        'total_cuotas': oblig['total_cuotas'],
        # Validación
        'disponible_final': validacion['disponible_final'],
        'cumple_minimo_vital': validacion['cumple_minimo_vital'],
        'pct_endeudamiento': validacion['pct_endeudamiento'],
        'estado_mv': validacion['estado'],
        # Garantías
        'total_garantias': garantias['total_garantias'],
        'pct_cobertura': garantias['pct_cobertura'],
        # Scoring
        'score_datacredito': s_dc,
        'score_antiguedad': s_ant,
        'score_vinculacion': s_vinc,
        'score_capacidad_pago': s_cap,
        'score_garantias': s_gar,
        'score_credito_activo': s_hist,
        'score_total': score_total,
        'clasificacion': clasificacion,
        'decision': decision,
        # Métricas
        'pd_base': metricas['pd_base'],
        'pd_ajustada': metricas['pd_ajustada'],
        'lgd': metricas['lgd'],
        'perdida_esperada': metricas['perdida_esperada'],
        # Plan
        'plan_pagos': plan,
        'tasa_nominal_anual': tasa_mensual * 12,
    }
