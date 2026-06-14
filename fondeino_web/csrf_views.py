from django.http import HttpResponseForbidden


def csrf_failure(request, reason=""):
    cookie_csrf = bool(request.COOKIES.get('csrftoken'))
    cookie_session = bool(request.COOKIES.get('sessionid'))
    origin = request.META.get('HTTP_ORIGIN', '—')
    referer = request.META.get('HTTP_REFERER', '—')
    secure = request.is_secure()

    # Detectar cookies csrftoken duplicadas (legado de Domain=.fondeino.com +
    # host-only nueva). Si hay más de una, ese es el síntoma que
    # ClearLegacyCsrfDomainCookieMiddleware está limpiando.
    raw_cookie = request.META.get('HTTP_COOKIE', '')
    csrftoken_count = raw_cookie.count('csrftoken=')
    duplicada = csrftoken_count > 1

    ok = '✅ Sí'
    no = '❌ No'

    fila_dup = (
        f'<tr><td>Cookies csrftoken duplicadas</td>'
        f'<td style="color:#e0a050;">⚠️ Sí ({csrftoken_count})</td></tr>'
    ) if duplicada else ''

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Error CSRF – Fondeino</title>
  <style>
    body {{ font-family: sans-serif; background: #0d1218; color: #dde8f6;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }}
    .card {{ background: #14263a; border: 1px solid #1e3a5f; border-radius: 12px;
             padding: 1.5rem; max-width: 480px; width: 100%; }}
    h2 {{ color: #e05050; margin: 0 0 .8rem; font-size: 1.1rem; }}
    .hint {{ color: #b0cce8; font-size: .82rem; margin: 0 0 1rem; line-height: 1.4; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .8rem; margin-bottom: .4rem; }}
    td {{ padding: .35rem .5rem; border-bottom: 1px solid #1e3050; }}
    td:first-child {{ color: #6ba4ff; white-space: nowrap; }}
    .btn {{ display: block; text-align: center; margin-top: .55rem;
            background: #1e3a5f; color: #dde8f6; text-decoration: none;
            border-radius: 8px; padding: .65rem; font-size: .9rem; }}
    .btn-primary {{ background: #f0c040; color: #0d1218; font-weight: 700; }}
    .reason {{ background: #1a0808; border: 1px solid #5a1010; border-radius: 6px;
               padding: .5rem .75rem; font-size: .78rem; color: #e05050; margin-bottom: 1rem; }}
  </style>
</head>
<body>
<div class="card">
  <h2>⚠️ Error de seguridad (CSRF)</h2>
  <div class="reason">Motivo: <strong>{reason or 'desconocido'}</strong></div>
  <p class="hint">
    Tu token de seguridad cambió entre cargar el formulario y enviarlo.
    Toca <strong>Recargar y reintentar</strong> para empezar con cookies limpias.
  </p>
  <table>
    <tr><td>Cookie csrftoken</td><td>{ok if cookie_csrf else no}</td></tr>
    <tr><td>Sesión</td><td>{ok if cookie_session else no}</td></tr>
    {fila_dup}
    <tr><td>HTTPS</td><td>{ok if secure else no}</td></tr>
    <tr><td>Origin</td><td style="font-size:.7rem;word-break:break-all;">{origin}</td></tr>
    <tr><td>Referer</td><td style="font-size:.7rem;word-break:break-all;">{referer}</td></tr>
  </table>
  <a class="btn btn-primary" href="javascript:limpiarYReintentar()">↻ Recargar y reintentar</a>
  <a class="btn" href="javascript:history.back()">← Volver atrás</a>
</div>
<script>
function limpiarYReintentar() {{
  var expira = '; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  // Borra cualquier cookie csrftoken local (host-only y legacy con Domain).
  document.cookie = 'csrftoken=' + expira;
  document.cookie = 'csrftoken=' + expira + '; domain=.fondeino.com';
  document.cookie = 'csrftoken=' + expira + '; domain=fondeino.com';
  // Vuelve al referer (donde estaba el form) o a la home de polla.
  var dest = document.referrer || '/polla/';
  window.location.href = dest;
}}
</script>
</body>
</html>"""
    return HttpResponseForbidden(html)
