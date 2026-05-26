"""
Genera las visualizaciones del análisis de la polla con los resultados ya conocidos.
Ejecutar después de analisis_polla_ganador_fase_grupos.py
"""
import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
rng = np.random.default_rng(42)

# ─── Parámetros del modelo (idénticos al script principal) ────────────────────
N_SIM         = 50_000
N_JUGADORES   = 80
N_GRUPOS      = 72
N_ELIMINACION = 32
PTS_G_EXACTO, PTS_G_RESULTADO = 3, 1
PTS_E_EXACTO, PTS_E_RESULTADO = 6, 2
SKILL_ALPHA, SKILL_BETA = 2.5, 4.0

def p_resultado(theta): return 0.33 + theta * 0.32
def p_exacto_cond(theta): return 0.06 + theta * 0.29

def simular_puntos_jugador(theta, n_g, n_e, rng):
    pr = p_resultado(theta)
    pe = p_exacto_cond(theta)
    p_ex = pr * pe
    p_res = pr * (1 - pe)
    u = rng.random(n_g)
    pg = np.where(u < p_ex, PTS_G_EXACTO, np.where(u < p_ex + p_res, PTS_G_RESULTADO, 0)).sum()
    u = rng.random(n_e)
    pe_ = np.where(u < p_ex, PTS_E_EXACTO, np.where(u < p_ex + p_res, PTS_E_RESULTADO, 0)).sum()
    return pg, pe_

# ─── Re-simular (usa misma semilla → mismos resultados) ───────────────────────
print("Simulando torneos para graficas...")
pts_grupos_todos = np.zeros((N_SIM, N_JUGADORES))
pts_elim_todos   = np.zeros((N_SIM, N_JUGADORES))

for sim in range(N_SIM):
    thetas_sim = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    for j, theta in enumerate(thetas_sim):
        pg, pe = simular_puntos_jugador(theta, N_GRUPOS, N_ELIMINACION, rng)
        pts_grupos_todos[sim, j] = pg
        pts_elim_todos[sim, j]   = pe

pts_total_todos = pts_grupos_todos + pts_elim_todos
rank_grupos = np.argsort(np.argsort(-pts_grupos_todos, axis=1), axis=1) + 1
rank_total  = np.argsort(np.argsort(-pts_total_todos, axis=1), axis=1) + 1
lider_grupos = np.argmax(pts_grupos_todos, axis=1)
lider_total  = np.argmax(pts_total_todos, axis=1)
es_mismo_lider = (lider_grupos == lider_total)
p_lider = es_mismo_lider.mean()

top_k_res = {}
for k in [1, 3, 5, 10, 20]:
    en_topk = [rank_grupos[sim, lider_total[sim]] <= k for sim in range(N_SIM)]
    top_k_res[k] = np.mean(en_topk)

# Markov
bandas = {
    'Top 1':     (1, 1),
    'Top 2-5':   (2, 5),
    'Top 6-10':  (6, 10),
    'Top 11-20': (11, 20),
    'Resto':     (21, N_JUGADORES),
}
n_bandas = len(bandas)
bandas_keys = list(bandas.keys())

def get_banda(rango):
    for i, (_, (lo, hi)) in enumerate(bandas.items()):
        if lo <= rango <= hi:
            return i
    return n_bandas - 1

trans_matrix = np.zeros((n_bandas, n_bandas))
for sim in range(N_SIM):
    for j in range(N_JUGADORES):
        trans_matrix[get_banda(rank_grupos[sim, j]), get_banda(rank_total[sim, j])] += 1
trans_norm = trans_matrix / trans_matrix.sum(axis=1, keepdims=True)

mu_g   = pts_grupos_todos.mean()
mu_e   = pts_elim_todos.mean()
sigma_g = pts_grupos_todos.std()
sigma_e = pts_elim_todos.std()

# Sensibilidad N jugadores
N_SIM_S = 5_000
n_jug_range = [20, 40, 60, 80, 100, 120, 150, 200]
p_por_n = []
for n in n_jug_range:
    hits = sum(
        np.argmax(pg := np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0]
                                   for t in rng.beta(SKILL_ALPHA, SKILL_BETA, n)])) ==
        np.argmax(pg + np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1]
                                  for t in rng.beta(SKILL_ALPHA, SKILL_BETA, n)]))
        for _ in range(N_SIM_S)
    )
    p_por_n.append(hits / N_SIM_S)
    print(f"  N={n} -> {hits/N_SIM_S:.1%}")

# Sensibilidad heterogeneidad
alphas = [1.0, 1.5, 2.0, 2.5, 3.5, 5.0]
p_por_alpha = []
for alpha in alphas:
    hits = sum(
        np.argmax(pg := np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[0]
                                   for t in rng.beta(alpha, SKILL_BETA, N_JUGADORES)])) ==
        np.argmax(pg + np.array([simular_puntos_jugador(t, N_GRUPOS, N_ELIMINACION, rng)[1]
                                  for t in rng.beta(alpha, SKILL_BETA, N_JUGADORES)]))
        for _ in range(N_SIM_S)
    )
    p_por_alpha.append(hits / N_SIM_S)
    print(f"  alpha={alpha} -> {hits/N_SIM_S:.1%}")

# Trayectoria del líder de grupos
N_TRACE = 2000
pos_lider_trace = []
for sim in range(N_TRACE):
    thetas_sim = rng.beta(SKILL_ALPHA, SKILL_BETA, size=N_JUGADORES)
    checkpoints = []
    pts_acum = np.zeros(N_JUGADORES)
    for j, th in enumerate(thetas_sim):
        pr = p_resultado(th); pe = p_exacto_cond(th)
        p_ex = pr * pe; p_res = pr * (1 - pe)
        u = rng.random(N_GRUPOS)
        pts_acum[j] += np.sum(np.where(u < p_ex, PTS_G_EXACTO, np.where(u < p_ex + p_res, PTS_G_RESULTADO, 0)))
    lider_g_sim = np.argmax(pts_acum)
    checkpoints.append(np.argsort(np.argsort(-pts_acum))[lider_g_sim] + 1)
    for n_round in [16, 8, 4, 2, 1, 1]:
        for j, th in enumerate(thetas_sim):
            pr = p_resultado(th); pe = p_exacto_cond(th)
            p_ex = pr * pe; p_res = pr * (1 - pe)
            u = rng.random(n_round)
            pts_acum[j] += np.sum(np.where(u < p_ex, PTS_E_EXACTO, np.where(u < p_ex + p_res, PTS_E_RESULTADO, 0)))
        checkpoints.append(np.argsort(np.argsort(-pts_acum))[lider_g_sim] + 1)
    pos_lider_trace.append(checkpoints)

pos_lider_trace = np.array(pos_lider_trace)
etapas = ['Fin\nGrupos', 'R32', 'R16', 'QF', 'SF', '3°', 'Final']
mean_pos = pos_lider_trace.mean(axis=0)
p10_pos  = np.percentile(pos_lider_trace, 10, axis=0)
p25_pos  = np.percentile(pos_lider_trace, 25, axis=0)
p75_pos  = np.percentile(pos_lider_trace, 75, axis=0)
p90_pos  = np.percentile(pos_lider_trace, 90, axis=0)

print("Graficando...")

# ─── FIGURA ───────────────────────────────────────────────────────────────────
VERDE  = '#2ecc71'
AZUL   = '#3498db'
ROJO   = '#e74c3c'
NARANJ = '#e67e22'
OSCURO = '#2c3e50'

fig = plt.figure(figsize=(18, 14))
fig.suptitle(
    'Análisis Estadístico — Polla Mundialista FONDEINO 2026\n'
    'Hipótesis: ¿Qué tan probable es que el líder de grupos gane la polla total?',
    fontsize=14, fontweight='bold', y=0.99
)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.48, wspace=0.35)

# 1. Distribución del rango de grupos del ganador total
ax1 = fig.add_subplot(gs[0, 0])
ranks_lider = [rank_grupos[sim, lider_total[sim]] for sim in range(N_SIM)]
counts = np.bincount(ranks_lider, minlength=N_JUGADORES + 1)[1:]
probs  = counts / N_SIM
colors = [VERDE if i < 5 else AZUL for i in range(20)]
ax1.bar(range(1, 21), probs[:20], color=colors, alpha=0.85, edgecolor='white')
ax1.axhline(1/N_JUGADORES, color=ROJO, linestyle='--', lw=1.5, label=f'Azar (1/{N_JUGADORES})')
ax1.set_xlabel('Posición del ganador total en ranking de grupos', fontsize=9)
ax1.set_ylabel('Probabilidad', fontsize=9)
ax1.set_title('¿En qué posición de grupos\nestaba el ganador total?', fontsize=10, fontweight='bold')
ax1.legend(fontsize=8); ax1.set_xlim(0.5, 20.5)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
ax1.tick_params(labelsize=8)

# 2. Top-K acumulado
ax2 = fig.add_subplot(gs[0, 1])
ks = list(top_k_res.keys()); pvs = list(top_k_res.values())
bars = ax2.bar([str(k) for k in ks], pvs,
               color=[VERDE if k <= 5 else AZUL for k in ks], alpha=0.85, edgecolor='white')
for bar, pv in zip(bars, pvs):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
             f'{pv:.0%}', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_xlabel('Top-K de la fase de grupos', fontsize=9)
ax2.set_ylabel('P(ganador total ∈ Top-K grupos)', fontsize=9)
ax2.set_title('Probabilidad acumulada:\nganador total estaba en Top-K de grupos', fontsize=10, fontweight='bold')
ax2.set_ylim(0, 1.1)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
ax2.tick_params(labelsize=8)

# 3. Scatter puntos grupos vs total
ax3 = fig.add_subplot(gs[0, 2])
idx_s = rng.integers(0, N_SIM, size=300)
pg_s = pts_grupos_todos[idx_s].flatten()
pt_s = pts_total_todos[idx_s].flatten()
ax3.scatter(pg_s, pt_s, alpha=0.05, s=4, color=AZUL)
m, b, r, _, _ = stats.linregress(pg_s, pt_s)
xl = np.linspace(pg_s.min(), pg_s.max(), 100)
ax3.plot(xl, m*xl + b, color=ROJO, lw=2, label=f'Pearson r = {r:.3f}')
ax3.set_xlabel('Puntos fase de grupos', fontsize=9)
ax3.set_ylabel('Puntos totales', fontsize=9)
ax3.set_title(f'Correlación: puntaje grupos → total\n(r = {r:.3f}, R² = {r**2:.0%})', fontsize=10, fontweight='bold')
ax3.legend(fontsize=8); ax3.tick_params(labelsize=8)

# 4. Matriz Markov (heatmap)
ax4 = fig.add_subplot(gs[1, :2])
im = ax4.imshow(trans_norm, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
ax4.set_xticks(range(n_bandas)); ax4.set_yticks(range(n_bandas))
ax4.set_xticklabels(bandas_keys, rotation=25, ha='right', fontsize=9)
ax4.set_yticklabels(bandas_keys, fontsize=9)
ax4.set_xlabel('Banda al FINAL del torneo', fontsize=9)
ax4.set_ylabel('Banda al final de GRUPOS', fontsize=9)
ax4.set_title('Cadena de Markov: P(banda final | banda en grupos)', fontsize=10, fontweight='bold')
for i in range(n_bandas):
    for j in range(n_bandas):
        v = trans_norm[i, j]
        flag = ' ◄' if i == j else ''
        ax4.text(j, i, f'{v:.0%}{flag}', ha='center', va='center', fontsize=9,
                 color='white' if v > 0.45 else 'black', fontweight='bold')
plt.colorbar(im, ax=ax4, fraction=0.03, pad=0.02)

# 5. Sensibilidad N jugadores
ax5 = fig.add_subplot(gs[1, 2])
p_rand = [1/n for n in n_jug_range]
ax5.plot(n_jug_range, [p*100 for p in p_por_n], 'o-', color=VERDE, lw=2, ms=7, label='Con habilidad')
ax5.plot(n_jug_range, [p*100 for p in p_rand], 's--', color=ROJO, lw=1.5, ms=5, label='Azar puro (1/N)')
ax5.fill_between(n_jug_range, [p*100 for p in p_rand], [p*100 for p in p_por_n],
                 alpha=0.15, color=VERDE)
ax5.set_xlabel('N° de jugadores en la polla', fontsize=9)
ax5.set_ylabel('P(líder grupos = ganador total) %', fontsize=9)
ax5.set_title('Sensibilidad: probabilidad según\nN° de jugadores', fontsize=10, fontweight='bold')
ax5.legend(fontsize=8); ax5.grid(True, alpha=0.3); ax5.tick_params(labelsize=8)

# 6. Distribución de puntos por fase
ax6 = fig.add_subplot(gs[2, 0])
ax6.hist(pts_grupos_todos[:3000].flatten(), bins=45, alpha=0.6, color=AZUL,
         label=f'Grupos (μ={mu_g:.0f}, σ={sigma_g:.0f})', density=True)
ax6.hist(pts_elim_todos[:3000].flatten(), bins=45, alpha=0.6, color=NARANJ,
         label=f'Elim. (μ={mu_e:.0f}, σ={sigma_e:.0f})', density=True)
ax6.set_xlabel('Puntos obtenidos', fontsize=9)
ax6.set_ylabel('Densidad', fontsize=9)
ax6.set_title('Distribución de puntos\npor fase (modelo)', fontsize=10, fontweight='bold')
ax6.legend(fontsize=8); ax6.tick_params(labelsize=8)

# 7. Sensibilidad heterogeneidad
ax7 = fig.add_subplot(gs[2, 1])
ax7.plot(alphas, [p*100 for p in p_por_alpha], 'D-', color=OSCURO, lw=2, ms=9)
for a, p in zip(alphas, p_por_alpha):
    ax7.annotate(f'{p:.0%}', (a, p*100), textcoords="offset points",
                 xytext=(0, 8), ha='center', fontsize=9, fontweight='bold')
ax7.set_xlabel('Parámetro α — Beta(α, 4)  (mayor α = jugadores más similares)', fontsize=9)
ax7.set_ylabel('P(líder grupos = ganador total) %', fontsize=9)
ax7.set_title('Sensibilidad: heterogeneidad de habilidad\nentre jugadores', fontsize=10, fontweight='bold')
ax7.grid(True, alpha=0.3); ax7.invert_xaxis(); ax7.tick_params(labelsize=8)

# 8. Trayectoria del líder de grupos a través de las fases
ax8 = fig.add_subplot(gs[2, 2])
x = range(len(etapas))
ax8.plot(x, mean_pos, 'o-', color=VERDE, lw=2.5, ms=8, label='Media', zorder=5)
ax8.fill_between(x, p25_pos, p75_pos, alpha=0.25, color=VERDE, label='IQR (25-75%)')
ax8.fill_between(x, p10_pos, p90_pos, alpha=0.12, color=VERDE, label='P10-P90')
ax8.axhline(1, color=ROJO, ls=':', lw=1.5, label='Pos. #1')
ax8.set_xticks(list(x)); ax8.set_xticklabels(etapas, fontsize=8)
ax8.set_ylabel('Posición del líder de grupos', fontsize=9)
ax8.set_title('Trayectoria del líder de grupos\na lo largo del torneo', fontsize=10, fontweight='bold')
ax8.invert_yaxis(); ax8.legend(fontsize=7.5)
ax8.grid(True, alpha=0.3); ax8.tick_params(labelsize=8)
ax8.set_ylim(bottom=max(p90_pos) + 1, top=0.5)

# Cuadro resumen central
fig.text(0.5, 0.685,
         f'RESULTADO PRINCIPAL: P(líder grupos = ganador total) = {p_lider:.1%}  '
         f'[×{p_lider/(1/N_JUGADORES):.0f} vs azar]   |   '
         f'Spearman ρ(rank_grupos, rank_total) ≈ 0.84',
         ha='center', fontsize=11, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#f0faf4', edgecolor=VERDE, lw=2))

plt.savefig('analisis_polla_fondeino_2026.png', dpi=150, bbox_inches='tight', facecolor='white')
print("Guardado: analisis_polla_fondeino_2026.png")
plt.show()
