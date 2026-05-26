"""
=============================================================================
ANÁLISIS ESTADÍSTICO — POLLA MUNDIALISTA FONDEINO 2026
=============================================================================
Hipótesis central:
  ¿Qué tan probable es que el líder de la FASE DE GRUPOS sea el ganador
  TOTAL de la polla al terminar todo el Mundial?

Metodologías:
  1. Modelo probabilístico de scoring (distribuciones discretas por fase)
  2. Simulación Monte Carlo (N_SIM torneos completos)
  3. Cadenas de Markov para transición de rangos entre fases
  4. Análisis de sensibilidad (N_jugadores, heterogeneidad de habilidades)
  5. Métricas de correlación de rangos (Kendall τ, Spearman ρ)
  6. Comparación con baseline aleatorio (hipótesis nula)

Estructura del Mundial 2026:
  - Fase de grupos : 12 grupos × 6 partidos = 72 partidos  (máx 3 pts/partido)
  - Ronda de 32   : 16 partidos                            (máx 6 pts/partido)
  - Octavos       :  8 partidos                            (máx 6 pts/partido)
  - Cuartos       :  4 partidos                            (máx 6 pts/partido)
  - Semifinales   :  2 partidos                            (máx 6 pts/partido)
  - Tercer puesto :  1 partido                             (máx 6 pts/partido)
  - Final         :  1 partido                             (máx 6 pts/partido)
  Total           : 72 (grupos) + 32 (elim) = 104 partidos
=============================================================================
"""

import sys
import io
# Forzar UTF-8 en stdout para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from scipy.stats import kendalltau, spearmanr
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 1. PARÁMETROS DEL MODELO
# ─────────────────────────────────────────────────────────────────────────────

N_SIM         = 50_000   # Simulaciones Monte Carlo
N_JUGADORES   = 80       # Jugadores típicos en la polla FONDEINO
N_GRUPOS      = 72       # Partidos fase de grupos
N_ELIMINACION = 32       # Partidos fase eliminatoria

# Puntos posibles por partido
PTS_G_EXACTO    = 3  # marcador exacto en grupos  (1 resultado + 2 marcador)
PTS_G_RESULTADO = 1  # solo resultado en grupos
PTS_E_EXACTO    = 6  # marcador exacto en eliminatoria (2 resultado + 4 marcador)
PTS_E_RESULTADO = 2  # solo resultado en eliminatoria

# ─────────────────────────────────────────────────────────────────────────────
# 2. MODELO DE HABILIDAD DEL JUGADOR
# ─────────────────────────────────────────────────────────────────────────────
# Cada jugador tiene habilidad θ ∈ [0, 1]:
#   - θ = 0: completamente aleatorio
#   - θ = 1: jugador perfecto
# La distribución Beta(α, β) captura que la mayoría son promedio,
# pocos son muy buenos o muy malos.

SKILL_ALPHA = 2.5
SKILL_BETA  = 4.0

# Funciones de probabilidad de acierto dada habilidad θ:
#   p_resultado(θ): probabilidad de acertar el resultado (G/E/P)
#     - Aleatoriamente: 1/3 ≈ 33%
#     - Jugador muy hábil: puede llegar a ~65%
#   p_exacto_dado_resultado(θ): P(marcador exacto | resultado correcto)
#     - Aleatoriamente: ~8% (muchos marcadores posibles)
#     - Jugador muy hábil: ~35%

def p_resultado(theta):
    """P(acertar resultado) en función de la habilidad θ."""
    return 0.33 + theta * 0.32   # rango: 33% → 65%

def p_exacto_cond(theta):
    """P(acertar marcador exacto | resultado correcto)."""
    return 0.06 + theta * 0.29   # rango: 6% → 35%

# ─────────────────────────────────────────────────────────────────────────────
# 3. GENERACIÓN DE PUNTOS POR PARTIDO
# ─────────────────────────────────────────────────────────────────────────────

def simular_puntos_jugador(theta, n_grupos, n_elim, rng):
    """
    Simula los puntos de un jugador en todos los partidos del torneo.
    Retorna (pts_grupos, pts_eliminatoria).
    """
    pr = p_resultado(theta)
    pe = p_exacto_cond(theta)

    # Probabilidades discretas para cada partido
    p_exacto     = pr * pe
    p_solo_res   = pr * (1 - pe)
    # p_nada = 1 - pr   (implícito)

    # ── Grupos ──
    u = rng.random(n_grupos)
    pts_g = np.where(u < p_exacto, PTS_G_EXACTO,
            np.where(u < p_exacto + p_solo_res, PTS_G_RESULTADO, 0))
    pts_grupos = pts_g.sum()

    # ── Eliminatorias ──
    u = rng.random(n_elim)
    pts_e = np.where(u < p_exacto, PTS_E_EXACTO,
            np.where(u < p_exacto + p_solo_res, PTS_E_RESULTADO, 0))
    pts_elim = pts_e.sum()

    return pts_grupos, pts_elim


# ─────────────────────────────────────────────────────────────────────────────
# 4. SIMULACIÓN MONTE CARLO
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 65)
print("  ANÁLISIS POLLA MUNDIALISTA FONDEINO 2026")
print("  Hipótesis: ¿El líder de grupos gana el total?")
print("=" * 65)
print(f"\n[1] Corriendo {N_SIM:,} simulaciones con {N_JUGADORES} jugadores...\n")

rng = np.random.default_rng(42)

# Habilidades fijas para los N_JUGADORES (se mantienen entre grupos y elim)
thetas = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)

# Matrices resultado: [N_SIM, N_JUGADORES]
pts_grupos_todos  = np.zeros((N_SIM, N_JUGADORES))
pts_elim_todos    = np.zeros((N_SIM, N_JUGADORES))

for sim in range(N_SIM):
    # Resampleamos habilidades por simulación: heterogeneidad poblacional
    thetas_sim = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    for j, theta in enumerate(thetas_sim):
        pg, pe = simular_puntos_jugador(theta, N_GRUPOS, N_ELIMINACION, rng)
        pts_grupos_todos[sim, j] = pg
        pts_elim_todos[sim, j]   = pe

pts_total_todos = pts_grupos_todos + pts_elim_todos

# ─────────────────────────────────────────────────────────────────────────────
# 5. CÁLCULO DE LA HIPÓTESIS PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

# Ranking después de grupos (1 = mejor)
rank_grupos = np.argsort(np.argsort(-pts_grupos_todos, axis=1), axis=1) + 1
# Ranking total
rank_total  = np.argsort(np.argsort(-pts_total_todos, axis=1), axis=1) + 1

# ¿El jugador #1 en grupos es también #1 en total?
lider_grupos     = np.argmax(pts_grupos_todos, axis=1)  # índice del líder de grupos
lider_total      = np.argmax(pts_total_todos, axis=1)   # índice del ganador total
es_mismo_lider   = (lider_grupos == lider_total)

p_lider_grupos_gana_total = es_mismo_lider.mean()

# ¿El ganador total estaba en el Top-k de grupos?
top_k_resultados = {}
for k in [1, 3, 5, 10, 20]:
    en_topk = []
    for sim in range(N_SIM):
        pos_ganador_total_en_grupos = rank_grupos[sim, lider_total[sim]]
        en_topk.append(pos_ganador_total_en_grupos <= k)
    top_k_resultados[k] = np.mean(en_topk)

# Baseline aleatorio (hipótesis nula: habilidad no existe)
p_baseline = 1 / N_JUGADORES

print("─" * 65)
print("  RESULTADOS PRINCIPALES")
print("─" * 65)
print(f"\n  Jugadores simulados       : {N_JUGADORES}")
print(f"  Torneos simulados         : {N_SIM:,}")
print(f"  Partidos grupos           : {N_GRUPOS}  (máx {N_GRUPOS * PTS_G_EXACTO} pts)")
print(f"  Partidos eliminatorias    : {N_ELIMINACION}  (máx {N_ELIMINACION * PTS_E_EXACTO} pts)")
print()
print(f"  Baseline aleatorio (H₀)   : {p_baseline:.1%}  (1/{N_JUGADORES})")
print()
print(f"  P(líder grupos = ganador total): {p_lider_grupos_gana_total:.1%}")
print(f"  Factor vs. azar            : ×{p_lider_grupos_gana_total / p_baseline:.1f}")
print()
print("  P(ganador total estaba en top-k de grupos):")
for k, p in top_k_resultados.items():
    barra = "█" * int(p * 40)
    print(f"    Top-{k:2d}: {p:5.1%}  {barra}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. CORRELACIÓN DE RANKINGS (Kendall τ, Spearman ρ)
# ─────────────────────────────────────────────────────────────────────────────

print("\n─" * 65)
print("  CORRELACIÓN ENTRE RANKINGS (grupos → total)")
print("─" * 65)

# Muestra de 1000 simulaciones para correlación
sample_idx = rng.choice(N_SIM, size=1000, replace=False)
tau_vals, rho_vals = [], []

for sim in sample_idx:
    tau, _ = kendalltau(rank_grupos[sim], rank_total[sim])
    rho, _ = spearmanr(rank_grupos[sim], rank_total[sim])
    tau_vals.append(tau)
    rho_vals.append(rho)

tau_mean = np.mean(tau_vals)
rho_mean = np.mean(rho_vals)

print(f"\n  Kendall τ (rango grupos ↔ rango total) : {tau_mean:.3f}")
print(f"  Spearman ρ (rango grupos ↔ rango total): {rho_mean:.3f}")
print()
print("  Interpretación:")
print(f"    - τ={tau_mean:.2f}: concordancia moderada-alta entre el orden")
print(f"      de grupos y el orden final")
print(f"    - ρ={rho_mean:.2f}: los puntajes de grupos explican")
print(f"      ≈{rho_mean**2:.0%} de la varianza del ranking total")

# ─────────────────────────────────────────────────────────────────────────────
# 7. CADENA DE MARKOV — TRANSICIÓN DE RANGOS
# ─────────────────────────────────────────────────────────────────────────────

print("\n─" * 65)
print("  CADENA DE MARKOV: Transición de rangos entre fases")
print("─" * 65)

# Definir bandas de ranking
bandas = {
    'Top 1':    (1, 1),
    'Top 2-5':  (2, 5),
    'Top 6-10': (6, 10),
    'Top 11-20':(11, 20),
    'Resto':    (21, N_JUGADORES),
}
n_bandas = len(bandas)
bandas_keys = list(bandas.keys())

def get_banda(rango, bandas_def):
    for i, (nombre, (lo, hi)) in enumerate(bandas_def.items()):
        if lo <= rango <= hi:
            return i
    return n_bandas - 1

# Construir matriz de transición empírica
trans_matrix = np.zeros((n_bandas, n_bandas))

for sim in range(N_SIM):
    for j in range(N_JUGADORES):
        banda_g = get_banda(rank_grupos[sim, j], bandas)
        banda_t = get_banda(rank_total[sim, j], bandas)
        trans_matrix[banda_g, banda_t] += 1

# Normalizar filas (probabilidades de transición)
trans_matrix_norm = trans_matrix / trans_matrix.sum(axis=1, keepdims=True)

print("\n  Matriz de transición P(banda_final | banda_grupos):\n")
print(f"  {'Banda grupos':<15}", end="")
for k in bandas_keys:
    print(f"  {k:<12}", end="")
print()
print("  " + "─" * (15 + 14 * n_bandas))

for i, bi in enumerate(bandas_keys):
    print(f"  {bi:<15}", end="")
    for j in range(n_bandas):
        v = trans_matrix_norm[i, j]
        flag = " ◄" if i == j else ""
        print(f"  {v:6.1%}      ", end="")
    print()

print()
print("  ◄ = probabilidad de mantenerse en la misma banda")

# Distribución estacionaria (comportamiento a largo plazo)
eigenvalues, eigenvectors = np.linalg.eig(trans_matrix_norm.T)
stationary_idx = np.argmin(np.abs(eigenvalues - 1.0))
stationary = np.real(eigenvectors[:, stationary_idx])
stationary = stationary / stationary.sum()

print("\n  Distribución estacionaria (equilibrio de largo plazo):")
for i, k in enumerate(bandas_keys):
    print(f"    {k:<15}: {stationary[i]:.1%}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. ANÁLISIS TEÓRICO: DESCOMPOSICIÓN DE VARIANZA
# ─────────────────────────────────────────────────────────────────────────────

print("\n─" * 65)
print("  ANÁLISIS TEÓRICO: Estructura del riesgo por fase")
print("─" * 65)

pts_g_flat = pts_grupos_todos.flatten()
pts_e_flat = pts_elim_todos.flatten()
pts_t_flat = pts_total_todos.flatten()

mu_g   = pts_g_flat.mean()
mu_e   = pts_e_flat.mean()
sigma_g = pts_g_flat.std()
sigma_e = pts_e_flat.std()

print(f"\n  Puntos esperados — Grupos       : {mu_g:.1f} pts  (σ = {sigma_g:.1f})")
print(f"  Puntos esperados — Eliminatorias: {mu_e:.1f} pts  (σ = {sigma_e:.1f})")
print(f"  Puntos esperados — Total        : {(mu_g + mu_e):.1f} pts  (σ ≈ {(sigma_g**2 + sigma_e**2)**0.5:.1f})")
print(f"\n  % pts esperados de grupos  : {mu_g/(mu_g+mu_e):.0%}")
print(f"  % pts esperados de elim    : {mu_e/(mu_g+mu_e):.0%}")
print(f"\n  % varianza aportada grupos : {sigma_g**2/(sigma_g**2+sigma_e**2):.0%}")
print(f"  % varianza aportada elim   : {sigma_e**2/(sigma_g**2+sigma_e**2):.0%}")

ratio_var = sigma_e**2 / sigma_g**2
print(f"\n  Ratio Var(elim)/Var(grupos): {ratio_var:.2f}")
print()
print("  → Las eliminatorias generan más volatilidad por punto promedio")
print("    ya que hay menos partidos pero con mayor recompensa,")
print("    aumentando las posibilidades de que el ranking se reorganice.")

# ─────────────────────────────────────────────────────────────────────────────
# 9. ANÁLISIS DE SENSIBILIDAD
# ─────────────────────────────────────────────────────────────────────────────

print("\n─" * 65)
print("  ANÁLISIS DE SENSIBILIDAD")
print("─" * 65)

N_SIM_SENS = 10_000  # más rápido para el barrido

# 9a. Sensibilidad por número de jugadores
print("\n  9a. P(líder grupos = ganador total) según N° de jugadores:")
n_jugadores_rango = [20, 40, 60, 80, 100, 120, 150, 200]
p_por_n = []

for n in n_jugadores_rango:
    hits = 0
    for sim in range(N_SIM_SENS):
        th  = rng.beta(SKILL_ALPHA, SKILL_BETA, size=n)
        pg  = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0] for t in th])
        pe  = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1] for t in th])
        if np.argmax(pg) == np.argmax(pg + pe):
            hits += 1
    p_est = hits / N_SIM_SENS
    p_por_n.append(p_est)
    barra = "█" * int(p_est * 50)
    print(f"    N={n:3d}: {p_est:5.1%}  {barra}")

# 9b. Sensibilidad por heterogeneidad de habilidad (skill_alpha varía)
print("\n  9b. P(líder grupos = ganador total) según dispersión de habilidad:")
print("      (Beta(α, β): menor α = más jugadores malos, más heterogeneidad)")
alphas = [1.0, 1.5, 2.0, 2.5, 3.5, 5.0]
p_por_alpha = []

for alpha in alphas:
    hits = 0
    for sim in range(N_SIM_SENS):
        th = rng.beta(alpha, SKILL_BETA, size=N_JUGADORES)
        pg = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0] for t in th])
        pe = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1] for t in th])
        if np.argmax(pg) == np.argmax(pg + pe):
            hits += 1
    p_est = hits / N_SIM_SENS
    p_por_alpha.append(p_est)
    het = "alta heterogeneidad" if alpha < 2 else "media" if alpha < 4 else "baja heterogeneidad"
    print(f"    α={alpha:.1f} ({het:18s}): {p_est:5.1%}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. CONCLUSIONES
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 65)
print("  CONCLUSIONES")
print("=" * 65)
print(f"""
  H₀ (azar puro): P = {p_baseline:.1%}  (1 en {N_JUGADORES})
  H₁ (modelo):   P = {p_lider_grupos_gana_total:.1%}  (factor ×{p_lider_grupos_gana_total/p_baseline:.1f} vs azar)

  1. LIDERAR LA FASE DE GRUPOS ES PREDICTIVO pero NO determinante.
     El líder de grupos gana la polla total en ≈{p_lider_grupos_gana_total:.0%} de los torneos
     simulados, muy superior al {p_baseline:.0%} que esperaríamos por puro azar.

  2. PERO... el ganador total tiene ≈{top_k_resultados[5]:.0%} de probabilidad
     de haber estado en el Top-5 de grupos. Es decir, mirar al Top-5
     de grupos al final de la fase es una señal fuerte.

  3. LA VOLATILIDAD DE LAS ELIMINATORIAS es el principal disruptor.
     Con solo 32 partidos pero puntos dobles (máx 6 pts vs 3 pts),
     la varianza por partido es ≈4× mayor. Un jugador que acierta
     varios marcadores exactos en octavos/cuartos puede remontar.

  4. LA CADENA DE MARKOV muestra que ≈{trans_matrix_norm[0,0]:.0%} de quienes
     lideran solos al final de grupos mantienen el Top-1 al final.
     El 'riesgo de descenso' es real pero moderado.

  5. DISEÑO DE LA POLLA: Los premios separados (Top 5 grupos + Top 5
     total) son un acierto — reconocen dos skills distintos. Si solo
     hubiera premio total, el {p_lider_grupos_gana_total:.0%} de probabilidad haría
     que ser líder de grupos fuese relevante pero no concluyente.

  RECOMENDACIÓN: La polla tiene un diseño balanceado. Para mejorar
  la predictibilidad del ganador se podría aumentar el peso de las
  eliminatorias (ej: 3 pts resultado / 6 pts exacto en lugar de 2/4),
  pero esto también haría el torneo más 'volátil' en las últimas rondas.
""")

# ─────────────────────────────────────────────────────────────────────────────
# 11. VISUALIZACIONES
# ─────────────────────────────────────────────────────────────────────────────

print("[2] Generando visualizaciones...\n")

fig = plt.figure(figsize=(18, 14))
fig.suptitle('Análisis Estadístico — Polla Mundialista FONDEINO 2026\n'
             'Hipótesis: ¿El líder de grupos gana el total?',
             fontsize=14, fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

VERDE  = '#2ecc71'
AZUL   = '#3498db'
ROJO   = '#e74c3c'
NARANJ = '#e67e22'
GRIS   = '#95a5a6'
OSCURO = '#2c3e50'

# ── Gráfica 1: Distribución de probabilidad por rank de grupos ──────────────
ax1 = fig.add_subplot(gs[0, 0])
ranks_lider_total_en_grupos = []
for sim in range(N_SIM):
    pos = rank_grupos[sim, lider_total[sim]]
    ranks_lider_total_en_grupos.append(pos)

counts = np.bincount(ranks_lider_total_en_grupos, minlength=N_JUGADORES+1)[1:]
probs  = counts / N_SIM
ax1.bar(range(1, min(21, N_JUGADORES+1)), probs[:20], color=AZUL, alpha=0.8, edgecolor='white')
ax1.axhline(p_baseline, color=ROJO, linestyle='--', linewidth=1.5, label=f'Azar ({p_baseline:.1%})')
ax1.set_xlabel('Posición del ganador total en ranking de grupos', fontsize=9)
ax1.set_ylabel('Probabilidad', fontsize=9)
ax1.set_title('¿En qué posición de grupos\nestaba el ganador total?', fontsize=10, fontweight='bold')
ax1.legend(fontsize=8)
ax1.set_xlim(0.5, 20.5)
ax1.tick_params(labelsize=8)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))

# Marcar top-5
for i in range(min(5, len(probs))):
    ax1.bar(i+1, probs[i], color=VERDE, alpha=0.9, edgecolor='white')

# ── Gráfica 2: Probabilidades Top-K ─────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ks   = list(top_k_resultados.keys())
pvs  = list(top_k_resultados.values())
colores_k = [VERDE if k <= 5 else AZUL for k in ks]
bars = ax2.bar([str(k) for k in ks], pvs, color=colores_k, alpha=0.85, edgecolor='white')
for bar, pv in zip(bars, pvs):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f'{pv:.0%}', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_xlabel('Top-K de la fase de grupos', fontsize=9)
ax2.set_ylabel('P(ganador total ∈ Top-K grupos)', fontsize=9)
ax2.set_title('Probabilidad acumulada\n(ganador total en Top-K de grupos)', fontsize=10, fontweight='bold')
ax2.set_ylim(0, 1.05)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
ax2.tick_params(labelsize=8)

# ── Gráfica 3: Scatter puntos grupos vs total (muestra 1000 sims) ───────────
ax3 = fig.add_subplot(gs[0, 2])
sample = 500
idx_s  = rng.integers(0, N_SIM, size=sample)
pg_s   = pts_grupos_todos[idx_s].flatten()
pt_s   = pts_total_todos[idx_s].flatten()
ax3.scatter(pg_s, pt_s, alpha=0.05, s=3, color=AZUL)
m, b, r, p_val, _ = stats.linregress(pg_s, pt_s)
x_line = np.linspace(pg_s.min(), pg_s.max(), 100)
ax3.plot(x_line, m*x_line + b, color=ROJO, linewidth=2, label=f'r={r:.3f}')
ax3.set_xlabel('Puntos fase de grupos', fontsize=9)
ax3.set_ylabel('Puntos totales', fontsize=9)
ax3.set_title(f'Correlación lineal grupos → total\n(Pearson r = {r:.3f})', fontsize=10, fontweight='bold')
ax3.legend(fontsize=8)
ax3.tick_params(labelsize=8)

# ── Gráfica 4: Matriz de Markov (heatmap) ───────────────────────────────────
ax4 = fig.add_subplot(gs[1, :2])
im = ax4.imshow(trans_matrix_norm, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
ax4.set_xticks(range(n_bandas))
ax4.set_yticks(range(n_bandas))
ax4.set_xticklabels(bandas_keys, rotation=30, ha='right', fontsize=8)
ax4.set_yticklabels(bandas_keys, fontsize=8)
ax4.set_xlabel('Banda al final del torneo', fontsize=9)
ax4.set_ylabel('Banda al final de grupos', fontsize=9)
ax4.set_title('Cadena de Markov: Transición de bandas de ranking\n(grupos → final)', fontsize=10, fontweight='bold')
for i in range(n_bandas):
    for j in range(n_bandas):
        v = trans_matrix_norm[i, j]
        color = 'white' if v > 0.5 else 'black'
        ax4.text(j, i, f'{v:.0%}', ha='center', va='center', fontsize=8.5,
                 color=color, fontweight='bold')
plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)

# ── Gráfica 5: Sensibilidad por N jugadores ──────────────────────────────────
ax5 = fig.add_subplot(gs[1, 2])
p_random_n = [1/n for n in n_jugadores_rango]
ax5.plot(n_jugadores_rango, [p*100 for p in p_por_n], 'o-', color=VERDE,
         linewidth=2, markersize=7, label='Modelo (con habilidad)')
ax5.plot(n_jugadores_rango, [p*100 for p in p_random_n], 's--', color=ROJO,
         linewidth=1.5, markersize=5, label='Azar puro (1/N)')
ax5.fill_between(n_jugadores_rango,
                 [p*100 for p in p_random_n],
                 [p*100 for p in p_por_n],
                 alpha=0.15, color=VERDE, label='Ventaja del liderazgo')
ax5.set_xlabel('N° de jugadores en la polla', fontsize=9)
ax5.set_ylabel('P(líder grupos = ganador total) %', fontsize=9)
ax5.set_title('Sensibilidad: Probabilidad vs\nN° de jugadores', fontsize=10, fontweight='bold')
ax5.legend(fontsize=7.5)
ax5.tick_params(labelsize=8)
ax5.grid(True, alpha=0.3)

# ── Gráfica 6: Distribución de puntos grupos y eliminatorias ─────────────────
ax6 = fig.add_subplot(gs[2, 0])
sample_g = pts_grupos_todos[:2000].flatten()
sample_e = pts_elim_todos[:2000].flatten()
ax6.hist(sample_g, bins=40, alpha=0.6, color=AZUL, label=f'Grupos (μ={mu_g:.0f}, σ={sigma_g:.0f})',
         density=True)
ax6.hist(sample_e, bins=40, alpha=0.6, color=NARANJ, label=f'Elim (μ={mu_e:.0f}, σ={sigma_e:.0f})',
         density=True)
ax6.set_xlabel('Puntos obtenidos', fontsize=9)
ax6.set_ylabel('Densidad', fontsize=9)
ax6.set_title('Distribución de puntos\npor fase', fontsize=10, fontweight='bold')
ax6.legend(fontsize=8)
ax6.tick_params(labelsize=8)

# ── Gráfica 7: Sensibilidad por heterogeneidad de habilidad ──────────────────
ax7 = fig.add_subplot(gs[2, 1])
ax7.plot(alphas, [p*100 for p in p_por_alpha], 'D-', color=OSCURO,
         linewidth=2, markersize=8)
for a, p in zip(alphas, p_por_alpha):
    ax7.annotate(f'{p:.0%}', (a, p*100), textcoords="offset points",
                 xytext=(0, 6), ha='center', fontsize=8)
ax7.set_xlabel('Parámetro α de distribución Beta(α, 4)', fontsize=9)
ax7.set_ylabel('P(líder grupos = ganador total) %', fontsize=9)
ax7.set_title('Sensibilidad: mayor α = habilidades\nmás similares entre jugadores', fontsize=10, fontweight='bold')
ax7.tick_params(labelsize=8)
ax7.grid(True, alpha=0.3)
ax7.invert_xaxis()

# ── Gráfica 8: Curva de remontada — posición del líder de grupos en cada fase ─
ax8 = fig.add_subplot(gs[2, 2])
# Simular el ranking del líder de grupos partido a partido
N_TRACE = 2000
pos_lider_trace = []

for sim in range(N_TRACE):
    thetas_sim = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    # Acumular puntos partido a partido
    checkpoints = []
    pts_acum = np.zeros(N_JUGADORES)

    # Grupos: 72 partidos → registrar al final
    for j, th in enumerate(thetas_sim):
        pr = p_resultado(th)
        pe = p_exacto_cond(th)
        p_ex = pr * pe
        p_res = pr * (1 - pe)
        u = rng.random(N_GRUPOS)
        pts_acum[j] += np.sum(np.where(u < p_ex, PTS_G_EXACTO,
                              np.where(u < p_ex + p_res, PTS_G_RESULTADO, 0)))

    lider_g_sim = np.argmax(pts_acum)
    checkpoints.append(np.argsort(np.argsort(-pts_acum))[lider_g_sim] + 1)

    # Eliminatorias: 32 partidos → registrar en intervals
    intervals = [16, 8, 4, 2, 1, 1]  # R32, R16, QF, SF, 3ero, Final
    for n_elim_round in intervals:
        for j, th in enumerate(thetas_sim):
            pr = p_resultado(th)
            pe = p_exacto_cond(th)
            p_ex = pr * pe
            p_res = pr * (1 - pe)
            u = rng.random(n_elim_round)
            pts_acum[j] += np.sum(np.where(u < p_ex, PTS_E_EXACTO,
                                  np.where(u < p_ex + p_res, PTS_E_RESULTADO, 0)))
        rank_lider = np.argsort(np.argsort(-pts_acum))[lider_g_sim] + 1
        checkpoints.append(rank_lider)

    pos_lider_trace.append(checkpoints)

pos_lider_trace = np.array(pos_lider_trace)  # (N_TRACE, 8)
etapas = ['Fin\nGrupos', 'R32', 'R16', 'QF', 'SF', '3°', 'Final']

mean_pos = pos_lider_trace.mean(axis=0)
p10_pos  = np.percentile(pos_lider_trace, 10, axis=0)
p25_pos  = np.percentile(pos_lider_trace, 25, axis=0)
p75_pos  = np.percentile(pos_lider_trace, 75, axis=0)
p90_pos  = np.percentile(pos_lider_trace, 90, axis=0)

x = range(len(etapas))
ax8.plot(x, mean_pos, 'o-', color=VERDE, linewidth=2.5, markersize=7, label='Media', zorder=5)
ax8.fill_between(x, p25_pos, p75_pos, alpha=0.25, color=VERDE, label='IQR (25-75%)')
ax8.fill_between(x, p10_pos, p90_pos, alpha=0.12, color=VERDE, label='P10-P90')
ax8.axhline(1, color=ROJO, linestyle=':', linewidth=1.5, label='Posición #1')
ax8.set_xticks(x)
ax8.set_xticklabels(etapas, fontsize=8)
ax8.set_ylabel('Posición del líder de grupos', fontsize=9)
ax8.set_title('Trayectoria del líder de grupos\na través de las fases', fontsize=10, fontweight='bold')
ax8.invert_yaxis()
ax8.legend(fontsize=7.5)
ax8.tick_params(labelsize=8)
ax8.grid(True, alpha=0.3)
ax8.set_ylim(ax8.get_ylim()[0], 0.5)

plt.savefig('analisis_polla_fondeino_2026.png', dpi=150, bbox_inches='tight',
            facecolor='white')
print("  → Guardado: analisis_polla_fondeino_2026.png")

plt.show()
print("\n[ANÁLISIS COMPLETO]\n")
