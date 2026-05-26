"""
Genera las 8 gráficas del análisis como archivos PNG independientes.
Destino: static/polla/img/analisis/
"""
import sys, io, os
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
from scipy.stats import kendalltau, spearmanr
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
rng = np.random.default_rng(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "polla", "img", "analisis")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Parámetros ────────────────────────────────────────────────────────────────
N_SIM         = 50_000
N_JUGADORES   = 80
N_GRUPOS      = 72
N_ELIMINACION = 32
PTS_G_EXACTO, PTS_G_RESULTADO = 3, 1
PTS_E_EXACTO, PTS_E_RESULTADO = 6, 2
SKILL_ALPHA, SKILL_BETA = 2.5, 4.0

VERDE  = '#2ecc71'
AZUL   = '#3498db'
ROJO   = '#e74c3c'
NARANJ = '#e67e22'
OSCURO = '#2c3e50'
GRIS   = '#95a5a6'

def p_resultado(theta): return 0.33 + theta * 0.32
def p_exacto_cond(theta): return 0.06 + theta * 0.29

def simular_puntos_jugador(theta, n_g, n_e, rng_):
    pr = p_resultado(theta)
    pe = p_exacto_cond(theta)
    p_ex = pr * pe
    p_res = pr * (1 - pe)
    u = rng_.random(n_g)
    pg = np.where(u < p_ex, PTS_G_EXACTO, np.where(u < p_ex + p_res, PTS_G_RESULTADO, 0)).sum()
    u = rng_.random(n_e)
    pe_ = np.where(u < p_ex, PTS_E_EXACTO, np.where(u < p_ex + p_res, PTS_E_RESULTADO, 0)).sum()
    return pg, pe_

def save(fig, nombre):
    path = os.path.join(OUT_DIR, nombre)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  OK  {nombre}")

# ── Simulación principal ──────────────────────────────────────────────────────
print("Simulando 50.000 torneos...")
pts_G = np.zeros((N_SIM, N_JUGADORES))
pts_E = np.zeros((N_SIM, N_JUGADORES))

for sim in range(N_SIM):
    th = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    for j, t in enumerate(th):
        pts_G[sim, j], pts_E[sim, j] = simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)

pts_T = pts_G + pts_E
rank_G = np.argsort(np.argsort(-pts_G, axis=1), axis=1) + 1
rank_T = np.argsort(np.argsort(-pts_T, axis=1), axis=1) + 1
lider_G = np.argmax(pts_G, axis=1)
lider_T = np.argmax(pts_T, axis=1)
es_mismo = (lider_G == lider_T)
p_lider  = es_mismo.mean()

top_k = {}
for k in [1, 3, 5, 10, 20]:
    top_k[k] = np.mean([rank_G[s, lider_T[s]] <= k for s in range(N_SIM)])

mu_g, mu_e   = pts_G.mean(), pts_E.mean()
sig_g, sig_e = pts_G.std(),  pts_E.std()

# ── Markov ────────────────────────────────────────────────────────────────────
bandas = {'Top 1':(1,1),'Top 2-5':(2,5),'Top 6-10':(6,10),'Top 11-20':(11,20),'Resto':(21,N_JUGADORES)}
n_b = len(bandas); bkeys = list(bandas.keys())

def get_b(r):
    for i,(_, (lo,hi)) in enumerate(bandas.items()):
        if lo <= r <= hi: return i
    return n_b - 1

trans = np.zeros((n_b, n_b))
for s in range(N_SIM):
    for j in range(N_JUGADORES):
        trans[get_b(rank_G[s,j]), get_b(rank_T[s,j])] += 1
trans_n = trans / trans.sum(axis=1, keepdims=True)

print("Generando gráficas individuales...")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 1 — Distribución del rango de grupos del ganador total
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))
ranks_lider = [rank_G[s, lider_T[s]] for s in range(N_SIM)]
counts = np.bincount(ranks_lider, minlength=N_JUGADORES+1)[1:]
probs  = counts / N_SIM
colors = [VERDE if i < 5 else AZUL for i in range(20)]
ax.bar(range(1, 21), probs[:20], color=colors, alpha=0.88, edgecolor='white', linewidth=0.8)
ax.axhline(1/N_JUGADORES, color=ROJO, linestyle='--', linewidth=1.8,
           label=f'Hipótesis nula (azar puro = 1/{N_JUGADORES} = {1/N_JUGADORES:.1%})')
ax.set_xlabel('Posición del ganador total en el ranking de la Fase de Grupos', fontsize=11)
ax.set_ylabel('Frecuencia relativa (probabilidad)', fontsize=11)
ax.set_title('Gráfica 1 — Distribución de posición del ganador total\nen la Fase de Grupos', fontsize=12, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
ax.set_xlim(0.3, 20.7)
ax.legend(fontsize=9)
# Anotación
ax.annotate(f'P(posición=1) = {probs[0]:.1%}', xy=(1, probs[0]),
            xytext=(4, probs[0]+0.02),
            arrowprops=dict(arrowstyle='->', color=OSCURO),
            fontsize=9, color=OSCURO, fontweight='bold')
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('white')
save(fig, 'g01_posicion_grupos.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 2 — Probabilidad acumulada Top-K
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))
ks  = list(top_k.keys())
pvs = list(top_k.values())
cols = [VERDE if k <= 5 else AZUL for k in ks]
bars = ax.bar([f'Top {k}' for k in ks], [p*100 for p in pvs],
              color=cols, alpha=0.88, edgecolor='white', linewidth=0.8)
for bar, pv in zip(bars, pvs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
            f'{pv:.1%}', ha='center', va='bottom', fontsize=12, fontweight='bold', color=OSCURO)
ax.set_xlabel('Banda del ranking de la Fase de Grupos', fontsize=11)
ax.set_ylabel('P(ganador total ∈ Top-K de grupos) %', fontsize=11)
ax.set_title('Gráfica 2 — Probabilidad acumulada de que el ganador total\nhaya estado en el Top-K de la Fase de Grupos', fontsize=12, fontweight='bold')
ax.set_ylim(0, 108)
ax.axhline(100/N_JUGADORES, color=ROJO, linestyle='--', linewidth=1.5,
           label=f'Azar puro Top-1 = {100/N_JUGADORES:.1f}%')
ax.legend(fontsize=9)
ax.set_facecolor('#f8f9fa')
save(fig, 'g02_probabilidad_topk.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 3 — Correlación puntos grupos → total
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 6))
idx_s = rng.integers(0, N_SIM, size=600)
pg_s  = pts_G[idx_s].flatten()
pt_s  = pts_T[idx_s].flatten()
ax.scatter(pg_s, pt_s, alpha=0.07, s=5, color=AZUL)
m, b, r, _, _ = stats.linregress(pg_s, pt_s)
xl = np.linspace(pg_s.min(), pg_s.max(), 200)
ax.plot(xl, m*xl + b, color=ROJO, linewidth=2.2,
        label=f'Regresión lineal  y = {m:.2f}x + {b:.1f}')
ax.set_xlabel('Puntos acumulados — Fase de Grupos', fontsize=11)
ax.set_ylabel('Puntos totales (Grupos + Eliminatorias)', fontsize=11)
ax.set_title(f'Gráfica 3 — Correlación lineal: puntaje de grupos → puntaje total\n'
             f'Pearson r = {r:.4f}   |   R² = {r**2:.2%}   |   n = {len(pg_s):,} observaciones',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.set_facecolor('#f8f9fa')
# Spearman
sample2k = rng.integers(0, N_SIM, size=1000)
tau_v, rho_v = [], []
for s in sample2k:
    tau, _ = kendalltau(rank_G[s], rank_T[s])
    rho, _ = spearmanr(rank_G[s], rank_T[s])
    tau_v.append(tau); rho_v.append(rho)
tau_m, rho_m = np.mean(tau_v), np.mean(rho_v)
ax.text(0.03, 0.95, f'Spearman ρ = {rho_m:.4f}\nKendall τ = {tau_m:.4f}',
        transform=ax.transAxes, fontsize=9, va='top',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor=GRIS, alpha=0.9))
save(fig, 'g03_correlacion.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 4 — Cadena de Markov (heatmap)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(trans_n, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(n_b)); ax.set_yticks(range(n_b))
ax.set_xticklabels(bkeys, rotation=25, ha='right', fontsize=10)
ax.set_yticklabels(bkeys, fontsize=10)
ax.set_xlabel('Banda de ranking al FINAL del torneo', fontsize=11)
ax.set_ylabel('Banda de ranking al final de la FASE DE GRUPOS', fontsize=11)
ax.set_title('Gráfica 4 — Cadena de Markov: Matriz de transición de rangos\n'
             'P(banda final | banda en grupos)  —  N = {:,} simulaciones'.format(N_SIM),
             fontsize=12, fontweight='bold')
for i in range(n_b):
    for j in range(n_b):
        v = trans_n[i, j]
        diag = ' ◄' if i == j else ''
        ax.text(j, i, f'{v:.1%}{diag}', ha='center', va='center', fontsize=9,
                color='white' if v > 0.48 else OSCURO, fontweight='bold')
cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
cbar.set_label('Probabilidad de transición', fontsize=9)
cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
save(fig, 'g04_markov.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 5 — Sensibilidad por N jugadores
# ══════════════════════════════════════════════════════════════════════════════
N_SIM_S = 8_000
n_rango = [20, 40, 60, 80, 100, 120, 150, 200]
p_n, ci_n = [], []
for n in n_rango:
    hits = []
    for _ in range(N_SIM_S):
        th = rng.beta(SKILL_ALPHA, SKILL_BETA, size=n)
        pg = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0] for t in th])
        pe = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1] for t in th])
        hits.append(int(np.argmax(pg) == np.argmax(pg + pe)))
    h = np.array(hits)
    p_est = h.mean()
    se = np.sqrt(p_est*(1-p_est)/N_SIM_S)
    p_n.append(p_est)
    ci_n.append(1.96 * se)
    print(f"    N={n} → {p_est:.1%}")

p_rand = [1/n for n in n_rango]
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.errorbar(n_rango, [p*100 for p in p_n], yerr=[c*100 for c in ci_n],
            fmt='o-', color=VERDE, linewidth=2.2, markersize=8, capsize=5,
            label='Modelo (habilidad diferenciada)', zorder=5)
ax.plot(n_rango, [p*100 for p in p_rand], 's--', color=ROJO,
        linewidth=1.8, markersize=6, label='Hipótesis nula (azar puro = 1/N)')
ax.fill_between(n_rango, [p*100 for p in p_rand], [p*100 for p in p_n],
                alpha=0.12, color=VERDE, label='Ventaja sobre el azar')
for n, p in zip(n_rango, p_n):
    ax.annotate(f'{p:.0%}', (n, p*100), textcoords="offset points",
                xytext=(0, 9), ha='center', fontsize=8.5, color=OSCURO)
ax.set_xlabel('Número de participantes en la polla', fontsize=11)
ax.set_ylabel('P(líder grupos = ganador total) %', fontsize=11)
ax.set_title('Gráfica 5 — Análisis de sensibilidad: probabilidad del liderazgo\nen función del tamaño del grupo (IC 95%)', fontsize=12, fontweight='bold')
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
ax.set_facecolor('#f8f9fa')
save(fig, 'g05_sensibilidad_n.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 6 — Distribución de puntos por fase
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
ax_g, ax_e = axes

# Grupos
ax_g.hist(pts_G[:5000].flatten(), bins=50, color=AZUL, alpha=0.8,
          edgecolor='white', linewidth=0.5, density=True)
ax_g.axvline(mu_g, color=ROJO, linewidth=2, label=f'μ = {mu_g:.1f} pts')
ax_g.axvline(mu_g - sig_g, color=NARANJ, linewidth=1.5, linestyle='--', label=f'μ ± σ  (σ = {sig_g:.1f})')
ax_g.axvline(mu_g + sig_g, color=NARANJ, linewidth=1.5, linestyle='--')
ax_g.set_title('Fase de Grupos (72 partidos · máx 216 pts)', fontsize=11, fontweight='bold')
ax_g.set_xlabel('Puntos obtenidos', fontsize=10)
ax_g.set_ylabel('Densidad', fontsize=10)
ax_g.legend(fontsize=9)
ax_g.set_facecolor('#f8f9fa')

# Eliminatorias
ax_e.hist(pts_E[:5000].flatten(), bins=50, color=NARANJ, alpha=0.8,
          edgecolor='white', linewidth=0.5, density=True)
ax_e.axvline(mu_e, color=ROJO, linewidth=2, label=f'μ = {mu_e:.1f} pts')
ax_e.axvline(mu_e - sig_e, color=AZUL, linewidth=1.5, linestyle='--', label=f'μ ± σ  (σ = {sig_e:.1f})')
ax_e.axvline(mu_e + sig_e, color=AZUL, linewidth=1.5, linestyle='--')
ax_e.set_title('Eliminatorias (32 partidos · máx 192 pts)', fontsize=11, fontweight='bold')
ax_e.set_xlabel('Puntos obtenidos', fontsize=10)
ax_e.legend(fontsize=9)
ax_e.set_facecolor('#f8f9fa')

fig.suptitle('Gráfica 6 — Distribución empírica de puntos por fase\n'
             f'Ratio Var(Elim)/Var(Grupos) = {sig_e**2/sig_g**2:.2f}   |   '
             f'% varianza Grupos = {sig_g**2/(sig_g**2+sig_e**2):.0%}   '
             f'Elim = {sig_e**2/(sig_g**2+sig_e**2):.0%}',
             fontsize=12, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.93])
save(fig, 'g06_distribucion_puntos.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 7 — Sensibilidad por heterogeneidad de habilidad
# ══════════════════════════════════════════════════════════════════════════════
alphas_het = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 5.0]
p_alpha, ci_alpha = [], []
for alpha in alphas_het:
    hits = []
    for _ in range(N_SIM_S):
        th = rng.beta(alpha, SKILL_BETA, size=N_JUGADORES)
        pg = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0] for t in th])
        pe = np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1] for t in th])
        hits.append(int(np.argmax(pg) == np.argmax(pg + pe)))
    h = np.array(hits)
    p_est = h.mean()
    se = np.sqrt(p_est*(1-p_est)/N_SIM_S)
    p_alpha.append(p_est)
    ci_alpha.append(1.96 * se)
    print(f"    α={alpha} → {p_est:.1%}")

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.errorbar(alphas_het, [p*100 for p in p_alpha], yerr=[c*100 for c in ci_alpha],
            fmt='D-', color=OSCURO, linewidth=2.2, markersize=9, capsize=5,
            label='P(líder grupos = ganador total) ± IC 95%')
for a, p in zip(alphas_het, p_alpha):
    ax.annotate(f'{p:.1%}', (a, p*100), textcoords="offset points",
                xytext=(0, 10), ha='center', fontsize=9, fontweight='bold', color=OSCURO)
ax.set_xlabel('Parámetro α de la distribución Beta(α, 4)  '
              '[α bajo = alta heterogeneidad; α alto = habilidades similares]', fontsize=10)
ax.set_ylabel('P(líder grupos = ganador total) %', fontsize=11)
ax.set_title('Gráfica 7 — Análisis de sensibilidad: heterogeneidad de habilidad\n'
             'Distribución de skills modelada como Beta(α, 4)', fontsize=12, fontweight='bold')
ax.invert_xaxis()
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)
ax.set_facecolor('#f8f9fa')

# Añadir distribuciones Beta en el eje superior como insets
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.stats import beta as beta_dist
axins = inset_axes(ax, width="28%", height="45%", loc='lower left', borderpad=1.5)
x_b = np.linspace(0, 1, 200)
for a, col in zip([1.0, 2.5, 5.0], [ROJO, NARANJ, AZUL]):
    axins.plot(x_b, beta_dist.pdf(x_b, a, SKILL_BETA), color=col, linewidth=1.8, label=f'α={a}')
axins.set_title('Dist. habilidades', fontsize=7)
axins.legend(fontsize=6.5); axins.set_xlim(0,1)
axins.tick_params(labelsize=6)
save(fig, 'g07_sensibilidad_heterogeneidad.png')

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICA 8 — Trayectoria del líder de grupos ronda a ronda
# ══════════════════════════════════════════════════════════════════════════════
N_TRACE = 3000
pos_trace = []
for sim in range(N_TRACE):
    th = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    pts_acum = np.zeros(N_JUGADORES)
    checkpoints = []
    for j, t in enumerate(th):
        pr = p_resultado(t); pe = p_exacto_cond(t)
        p_ex = pr*pe; p_res = pr*(1-pe)
        u = rng.random(N_GRUPOS)
        pts_acum[j] += np.sum(np.where(u<p_ex, PTS_G_EXACTO, np.where(u<p_ex+p_res, PTS_G_RESULTADO, 0)))
    lider = np.argmax(pts_acum)
    checkpoints.append(np.argsort(np.argsort(-pts_acum))[lider]+1)
    for n_round in [16, 8, 4, 2, 1, 1]:
        for j, t in enumerate(th):
            pr = p_resultado(t); pe = p_exacto_cond(t)
            p_ex = pr*pe; p_res = pr*(1-pe)
            u = rng.random(n_round)
            pts_acum[j] += np.sum(np.where(u<p_ex, PTS_E_EXACTO, np.where(u<p_ex+p_res, PTS_E_RESULTADO, 0)))
        checkpoints.append(np.argsort(np.argsort(-pts_acum))[lider]+1)
    pos_trace.append(checkpoints)

pos_trace = np.array(pos_trace)
etapas = ['Fin\nGrupos', 'Ronda\nde 32', 'Octavos', 'Cuartos', 'Semis', '3er\nPuesto', 'Final']

mean_p = pos_trace.mean(axis=0)
p5  = np.percentile(pos_trace,  5, axis=0)
p25 = np.percentile(pos_trace, 25, axis=0)
p50 = np.percentile(pos_trace, 50, axis=0)
p75 = np.percentile(pos_trace, 75, axis=0)
p95 = np.percentile(pos_trace, 95, axis=0)

x = np.arange(len(etapas))
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(x, mean_p, 'o-', color=VERDE, linewidth=2.5, markersize=9,
        label=f'Media (n={N_TRACE:,} simulaciones)', zorder=6)
ax.plot(x, p50, 's--', color=AZUL, linewidth=1.8, markersize=7,
        label='Mediana (P50)', zorder=5)
ax.fill_between(x, p25, p75, alpha=0.28, color=VERDE, label='IQR P25–P75')
ax.fill_between(x, p5,  p95, alpha=0.10, color=VERDE, label='P5–P95')
ax.axhline(1, color=ROJO, linestyle=':', linewidth=2, label='Posición #1 (objetivo)')
ax.axhline(5, color=NARANJ, linestyle=':', linewidth=1.5, label='Posición #5 (Top-5)')

# Anotar media en cada punto
for xi, mp in zip(x, mean_p):
    ax.annotate(f'{mp:.1f}', (xi, mp), textcoords="offset points",
                xytext=(0, 11), ha='center', fontsize=9, color=OSCURO, fontweight='bold')

ax.set_xticks(x); ax.set_xticklabels(etapas, fontsize=10)
ax.set_ylabel('Posición en el ranking general', fontsize=11)
ax.invert_yaxis()
ax.set_ylim(bottom=max(p95)+1, top=0.3)
ax.set_title(f'Gráfica 8 — Evolución del ranking del líder de grupos a lo largo del torneo\n'
             f'Seguimiento ronda a ronda  |  N = {N_TRACE:,} simulaciones  |  '
             f'P(mantiene #1 hasta Final) = {p_lider:.1%}',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='lower right')
ax.grid(True, alpha=0.3, axis='y')
ax.set_facecolor('#f8f9fa')
save(fig, 'g08_trayectoria_lider.png')

print(f"\nListo. 8 gráficas guardadas en: {OUT_DIR}")
print(f"\n  RESULTADO PRINCIPAL:")
print(f"  P(lider grupos = ganador total) = {p_lider:.2%}")
print(f"  Factor vs azar = x{p_lider/(1/N_JUGADORES):.1f}")
print(f"  Spearman rho   = {rho_m:.4f}")
print(f"  Kendall tau    = {tau_m:.4f}")
