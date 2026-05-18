/* Polla Mundialista FONDEINO 2026 — JS */

'use strict';

/* ── Auto-dismiss alerts after 5s ── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const btn = el.querySelector('.btn-close');
      if (btn) btn.click();
    }, 5000);
  });
});

/* ── Validación de inputs numéricos de resultados (admin) ── */
document.addEventListener('input', e => {
  const inp = e.target;
  if (inp.type === 'number' && inp.closest('form')) {
    const val = parseInt(inp.value);
    if (!isNaN(val)) {
      const min = parseInt(inp.min ?? 0);
      const max = parseInt(inp.max ?? 20);
      if (val < min) inp.value = min;
      if (val > max) inp.value = max;
    }
  }
});

/* ── Confirmar cierre de polla ── */
const cerrarForm = document.querySelector('form[action*="cerrar"]');
if (cerrarForm) {
  cerrarForm.addEventListener('submit', e => {
    if (!confirm('¿Estás seguro de cerrar la polla? Esta acción es IRREVERSIBLE.')) {
      e.preventDefault();
    }
  });
}

/* ── Countdown al próximo partido ── */
function updateCountdowns() {
  document.querySelectorAll('[data-partido-fecha]').forEach(el => {
    const fecha = new Date(el.dataset.partidoFecha);
    const ahora = new Date();
    const diff = fecha - ahora;
    if (diff <= 0) {
      el.textContent = '🔒 Cerrado';
      el.classList.add('text-danger');
      return;
    }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    if (h < 24) {
      el.textContent = `Cierra en ${h}h ${m}m`;
      if (h < 2) el.classList.add('text-warning');
    }
  });
}

if (document.querySelector('[data-partido-fecha]')) {
  updateCountdowns();
  setInterval(updateCountdowns, 60000);
}

/* ── Filtro en tabla de afiliados (client-side) ── */
const tablaAfiliados = document.querySelector('#tabla-afiliados-body');
if (tablaAfiliados) {
  const inputFiltro = document.querySelector('#filtro-afiliados');
  if (inputFiltro) {
    inputFiltro.addEventListener('input', () => {
      const q = inputFiltro.value.toLowerCase();
      tablaAfiliados.querySelectorAll('tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
}
